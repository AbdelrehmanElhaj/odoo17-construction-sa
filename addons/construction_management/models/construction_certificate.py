import base64
import struct

from odoo import models, fields, api
from odoo.exceptions import ValidationError

try:
    import qrcode
    from io import BytesIO
    _HAS_QRCODE = True
except ImportError:
    _HAS_QRCODE = False


def _zatca_tlv(tag, value):
    b = value.encode('utf-8') if isinstance(value, str) else value
    return bytes([tag, len(b)]) + b


def _zatca_qr_string(seller_name, vat_no, invoice_dt, total_with_vat, vat_amount):
    tlv = (
        _zatca_tlv(1, seller_name)
        + _zatca_tlv(2, vat_no or '')
        + _zatca_tlv(3, invoice_dt)
        + _zatca_tlv(4, '{:.2f}'.format(total_with_vat))
        + _zatca_tlv(5, '{:.2f}'.format(vat_amount))
    )
    return base64.b64encode(tlv).decode('ascii')


class ConstructionCertificate(models.Model):
    _name = 'construction.certificate'
    _description = 'Progress Certificate | مستخلص التقدم'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_to desc, id desc'
    _rec_name = 'name'

    # ── Identity ──────────────────────────────────────────────────────

    name = fields.Char(
        string='عنوان المستخلص | Certificate Title', required=True, tracking=True)
    certificate_code = fields.Char(
        string='رقم المستخلص', readonly=True, copy=False, default='مسودة')
    certificate_number = fields.Integer(
        string='المستخلص رقم | Certificate No.', default=1)

    # ── Links ─────────────────────────────────────────────────────────

    project_id = fields.Many2one(
        'construction.project', string='المشروع | Project',
        required=True, ondelete='cascade', tracking=True, index=True)
    contract_id = fields.Many2one(
        'construction.contract', string='العقد | Contract',
        domain="[('project_id', '=', project_id)]",
        ondelete='restrict', tracking=True, index=True)
    payment_line_id = fields.Many2one(
        'construction.payment.line', string='دفعة مجدولة | Payment Milestone',
        domain="[('contract_id', '=', contract_id)]")

    # ── State ─────────────────────────────────────────────────────────

    state = fields.Selection([
        ('draft',    'مسودة'),
        ('review',   'قيد المراجعة'),
        ('approved', 'معتمد'),
        ('paid',     'مدفوع'),
    ], string='الحالة', default='draft', tracking=True, required=True)

    # ── Period ────────────────────────────────────────────────────────

    date_from      = fields.Date(string='من تاريخ | From')
    date_to        = fields.Date(string='إلى تاريخ | To')
    date_submitted = fields.Date(string='تاريخ التقديم | Submitted')
    date_approved  = fields.Date(string='تاريخ الاعتماد | Approved')
    date_paid      = fields.Date(string='تاريخ الدفع | Paid')

    # ── Approvers ─────────────────────────────────────────────────────

    reviewed_by = fields.Many2one('res.users', string='المراجع | Reviewed By')
    approved_by = fields.Many2one('res.users', string='المعتمد | Approved By')

    # ── Financial ─────────────────────────────────────────────────────

    currency_id = fields.Many2one(
        'res.currency', compute='_compute_currency_id', store=True)
    amount_gross = fields.Monetary(
        string='الإجمالي قبل الخصومات | Gross',
        compute='_compute_amounts', store=True)
    retention_percent = fields.Float(
        string='نسبة الضمان % | Retention %', digits=(5, 2))
    retention_amount = fields.Monetary(
        string='خصم الضمان | Retention',
        compute='_compute_amounts', store=True)
    advance_deduction = fields.Monetary(
        string='خصم الدفعة المقدمة | Advance Deduction')
    amount_net = fields.Monetary(
        string='صافي المستخلص | Net Amount',
        compute='_compute_amounts', store=True)

    # ── VAT / ZATCA ───────────────────────────────────────────────────

    vat_rate = fields.Float(
        string='نسبة الضريبة % | VAT %',
        default=15.0, digits=(5, 2))
    vat_amount = fields.Monetary(
        string='ضريبة القيمة المضافة | VAT Amount',
        compute='_compute_amounts', store=True)
    amount_with_vat = fields.Monetary(
        string='الإجمالي شامل الضريبة | Total with VAT',
        compute='_compute_amounts', store=True)
    zatca_qr_code = fields.Binary(
        string='ZATCA QR',
        compute='_compute_zatca_qr', store=True, attachment=False,
        help='QR code encoded per ZATCA Phase 1 TLV specification')

    # ── Lines ─────────────────────────────────────────────────────────

    line_ids = fields.One2many(
        'construction.certificate.line', 'certificate_id', string='البنود | Items')

    description = fields.Html(string='وصف | Description')
    notes = fields.Char(string='ملاحظات')

    # ── Computed ──────────────────────────────────────────────────────

    @api.depends('contract_id', 'project_id')
    def _compute_currency_id(self):
        sar = self.env.ref('base.SAR', raise_if_not_found=False)
        for rec in self:
            if rec.contract_id and rec.contract_id.currency_id:
                rec.currency_id = rec.contract_id.currency_id
            elif rec.project_id and rec.project_id.currency_id:
                rec.currency_id = rec.project_id.currency_id
            else:
                rec.currency_id = sar

    @api.depends('line_ids.amount_this', 'retention_percent',
                 'advance_deduction', 'vat_rate')
    def _compute_amounts(self):
        for rec in self:
            rec.amount_gross     = sum(rec.line_ids.mapped('amount_this'))
            rec.retention_amount = rec.amount_gross * rec.retention_percent / 100.0
            rec.amount_net       = (
                rec.amount_gross - rec.retention_amount - (rec.advance_deduction or 0.0)
            )
            rec.vat_amount       = rec.amount_net * rec.vat_rate / 100.0
            rec.amount_with_vat  = rec.amount_net + rec.vat_amount

    @api.depends('amount_net', 'vat_amount', 'date_approved', 'date_submitted',
                 'state')
    def _compute_zatca_qr(self):
        for rec in self:
            if not _HAS_QRCODE:
                rec.zatca_qr_code = False
                continue
            company = rec.env.company
            invoice_dt = (rec.date_approved or rec.date_submitted)
            dt_str = (
                invoice_dt.strftime('%Y-%m-%dT00:00:00Z')
                if invoice_dt else '2000-01-01T00:00:00Z'
            )
            qr_data = _zatca_qr_string(
                seller_name   = company.name or '',
                vat_no        = company.vat or '',
                invoice_dt    = dt_str,
                total_with_vat= rec.amount_with_vat,
                vat_amount    = rec.vat_amount,
            )
            try:
                qr = qrcode.QRCode(
                    box_size=4, border=2,
                    error_correction=qrcode.constants.ERROR_CORRECT_M)
                qr.add_data(qr_data)
                qr.make(fit=True)
                img = qr.make_image(fill_color='black', back_color='white')
                buf = BytesIO()
                img.save(buf, format='PNG')
                rec.zatca_qr_code = base64.b64encode(buf.getvalue())
            except Exception:
                rec.zatca_qr_code = False

    # ── Auto-fill from contract ───────────────────────────────────────

    @api.onchange('contract_id')
    def _onchange_contract_id(self):
        if self.contract_id:
            self.retention_percent = self.contract_id.retention_percent

    # ── Validation helpers ────────────────────────────────────────────

    def _validate_amount_vs_contract(self):
        for rec in self:
            if not rec.contract_id or not rec.contract_id.contract_value:
                continue
            sibling_total = sum(
                c.amount_gross
                for c in rec.contract_id.certificate_ids
                if c.state in ('review', 'approved', 'paid') and c.id != rec.id
            )
            total = sibling_total + rec.amount_gross
            limit = rec.contract_id.contract_value
            if total > limit:
                excess = total - limit
                currency = rec.currency_id.name or 'SAR'
                raise ValidationError(
                    'لا يمكن تجاوز قيمة العقد.\n'
                    f'قيمة العقد:  {limit:,.2f} {currency}\n'
                    f'إجمالي المستخلصات (شاملاً هذا المستخلص):  {total:,.2f} {currency}\n'
                    f'الزيادة:  {excess:,.2f} {currency}'
                )

    # ── Constraints ───────────────────────────────────────────────────

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for rec in self:
            if rec.date_from and rec.date_to and rec.date_to < rec.date_from:
                raise ValidationError('"إلى تاريخ" يجب أن يكون بعد "من تاريخ".')

    @api.constrains('date_from', 'date_to', 'contract_id')
    def _check_period_overlap(self):
        for rec in self:
            if not rec.contract_id or not rec.date_from or not rec.date_to:
                continue
            overlap = self.search([
                ('contract_id', '=', rec.contract_id.id),
                ('id', '!=', rec.id),
                ('state', 'not in', ['draft']),
                ('date_from', '<=', rec.date_to),
                ('date_to', '>=', rec.date_from),
            ], limit=1)
            if overlap:
                raise ValidationError(
                    f'فترة المستخلص تتداخل مع المستخلص "{overlap.name}" '
                    f'({overlap.date_from} – {overlap.date_to}).\n'
                    'يجب أن تكون فترات المستخلصات متتالية وغير متداخلة.'
                )

    # ── Sequence ──────────────────────────────────────────────────────

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('certificate_code', 'مسودة') == 'مسودة':
                vals['certificate_code'] = (
                    self.env['ir.sequence'].next_by_code('construction.certificate')
                    or 'CERT-NEW'
                )
        return super().create(vals_list)

    # ── State transitions ─────────────────────────────────────────────

    def action_submit_review(self):
        self._validate_amount_vs_contract()
        self.write({
            'state': 'review',
            'date_submitted': fields.Date.today(),
        })
        for rec in self:
            reviewer = rec.reviewed_by or self.env['res.users'].browse(self.env.uid)
            rec.activity_schedule(
                activity_type_xmlid='mail.mail_activity_data_todo',
                summary=f'مراجعة المستخلص {rec.certificate_code}',
                user_id=reviewer.id,
                note=(
                    f'يرجى مراجعة المستخلص <b>{rec.certificate_code} — {rec.name}</b><br/>'
                    f'الإجمالي: <b>{rec.amount_gross:,.2f} {rec.currency_id.name or "SAR"}</b>'
                ),
            )

    def action_approve(self):
        self._validate_amount_vs_contract()
        self.write({
            'state': 'approved',
            'approved_by': self.env.user.id,
            'date_approved': fields.Date.today(),
        })
        for rec in self:
            if rec.payment_line_id and rec.payment_line_id.state == 'pending':
                rec.payment_line_id.action_mark_due()
            rec.message_post(
                body=(
                    f'✓ اعتمد المستخلص <b>{rec.approved_by.name}</b> بتاريخ {rec.date_approved}<br/>'
                    f'الإجمالي قبل الخصومات: {rec.amount_gross:,.2f} {rec.currency_id.name or "SAR"}<br/>'
                    f'خصم الضمان ({rec.retention_percent:.1f}%): {rec.retention_amount:,.2f}<br/>'
                    f'ضريبة القيمة المضافة ({rec.vat_rate:.0f}%): {rec.vat_amount:,.2f}<br/>'
                    f'<b>الإجمالي المستحق شامل الضريبة: {rec.amount_with_vat:,.2f} {rec.currency_id.name or "SAR"}</b>'
                ),
                subtype_xmlid='mail.mt_note',
            )
            rec.activity_schedule(
                activity_type_xmlid='mail.mail_activity_data_todo',
                summary=f'صرف دفعة المستخلص {rec.certificate_code}',
                user_id=self.env.uid,
                note=(
                    f'المستخلص <b>{rec.certificate_code}</b> معتمد وجاهز للصرف.<br/>'
                    f'المبلغ المستحق شامل الضريبة: <b>{rec.amount_with_vat:,.2f} {rec.currency_id.name or "SAR"}</b>'
                ),
            )

    def action_mark_paid(self):
        self.write({
            'state': 'paid',
            'date_paid': fields.Date.today(),
        })
        for rec in self:
            if rec.payment_line_id and rec.payment_line_id.state != 'paid':
                rec.payment_line_id.action_mark_paid()

    def action_reject(self):
        self.write({'state': 'draft'})

    def action_reset_draft(self):
        self.write({'state': 'draft'})


class ConstructionCertificateLine(models.Model):
    _name = 'construction.certificate.line'
    _description = 'Certificate Line | بند المستخلص'
    _order = 'sequence, id'

    # ── Parent ────────────────────────────────────────────────────────

    certificate_id = fields.Many2one(
        'construction.certificate', string='المستخلص',
        required=True, ondelete='cascade', index=True)
    sequence = fields.Integer(string='#', default=10)

    # ── Item ──────────────────────────────────────────────────────────

    boq_line_id = fields.Many2one(
        'construction.boq.line', string='بند BOQ')
    item_code   = fields.Char(string='الكود | Code')
    description = fields.Char(string='الوصف | Description', required=True)
    item_type   = fields.Selection([
        ('material',    'مواد'),
        ('labor',       'عمالة'),
        ('equipment',   'معدات'),
        ('subcontract', 'مقاول باطن'),
        ('overhead',    'مصروفات عامة'),
    ], string='النوع', default='material')
    uom_id = fields.Many2one('uom.uom', string='الوحدة | UOM')

    # ── Quantities ────────────────────────────────────────────────────

    qty_boq      = fields.Float(string='كمية BOQ',            digits=(12, 3))
    qty_previous = fields.Float(string='كمية سابقة مجمعة',   digits=(12, 3))
    qty_this     = fields.Float(string='كمية هذا المستخلص',  digits=(12, 3))
    qty_total    = fields.Float(
        string='إجمالي الكمية المعتمدة',
        compute='_compute_qty', store=True, digits=(12, 3))
    percent_complete = fields.Float(
        string='نسبة الإنجاز %',
        compute='_compute_qty', store=True, digits=(5, 2))
    unit_price   = fields.Float(string='سعر الوحدة', digits=(12, 2))

    # ── Amounts ───────────────────────────────────────────────────────

    currency_id = fields.Many2one(
        'res.currency', related='certificate_id.currency_id', store=True)
    amount_previous = fields.Monetary(
        string='مبلغ سابق',
        compute='_compute_amounts', store=True, currency_field='currency_id')
    amount_this = fields.Monetary(
        string='مبلغ هذا المستخلص',
        compute='_compute_amounts', store=True, currency_field='currency_id')
    amount_total = fields.Monetary(
        string='المبلغ الإجمالي المعتمد',
        compute='_compute_amounts', store=True, currency_field='currency_id')

    # ── Computed ──────────────────────────────────────────────────────

    @api.depends('qty_previous', 'qty_this', 'qty_boq')
    def _compute_qty(self):
        for rec in self:
            rec.qty_total = rec.qty_previous + rec.qty_this
            rec.percent_complete = (
                min(100.0, rec.qty_total / rec.qty_boq * 100.0)
                if rec.qty_boq > 0 else 0.0
            )

    @api.depends('qty_previous', 'qty_this', 'qty_total', 'unit_price')
    def _compute_amounts(self):
        for rec in self:
            rec.amount_previous = rec.qty_previous * rec.unit_price
            rec.amount_this     = rec.qty_this     * rec.unit_price
            rec.amount_total    = rec.qty_total    * rec.unit_price

    # ── Auto-fill from BOQ line ───────────────────────────────────────

    @api.onchange('boq_line_id')
    def _onchange_boq_line_id(self):
        if not self.boq_line_id:
            return
        line = self.boq_line_id
        self.description = line.description
        self.item_code   = line.item_code or False
        self.item_type   = line.item_type
        self.uom_id      = line.uom_id
        self.qty_boq     = line.qty_estimated
        self.unit_price  = line.unit_price
        # Sum qty from previously approved/paid certificates for this BOQ line
        prev_qty = sum(
            cl.qty_this
            for cl in line.cert_line_ids
            if cl.certificate_id.id != self.certificate_id.id
            and cl.certificate_id.state in ('approved', 'paid')
        )
        self.qty_previous = prev_qty

    # ── Constraints ───────────────────────────────────────────────────

    @api.constrains('qty_this', 'qty_previous')
    def _check_qty(self):
        for rec in self:
            if rec.qty_this < 0:
                raise ValidationError('الكمية لا يمكن أن تكون سالبة.')
            if rec.qty_previous < 0:
                raise ValidationError('الكمية السابقة لا يمكن أن تكون سالبة.')
