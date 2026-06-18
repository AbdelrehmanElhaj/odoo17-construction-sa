from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ConstructionContract(models.Model):
    _name = 'construction.contract'
    _description = 'Construction Contract | عقد المقاولات'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_signed desc, id desc'
    _rec_name = 'name'

    # ── Identity ──────────────────────────────────────────────────────

    name = fields.Char(string='اسم العقد | Contract Name', required=True, tracking=True)
    contract_code = fields.Char(string='رقم العقد', readonly=True, copy=False, default='مسودة')
    contract_type = fields.Selection([
        ('main',      'عقد رئيسي — Main Contract'),
        ('amendment', 'ملحق عقد — Amendment'),
        ('addendum',  'إضافة عقد — Addendum'),
    ], string='نوع العقد | Type', default='main', required=True, tracking=True)
    state = fields.Selection([
        ('draft',      'مسودة'),
        ('active',     'نشط'),
        ('completed',  'مكتمل'),
        ('cancelled',  'ملغي'),
        ('terminated', 'مفسوخ'),
    ], string='الحالة', default='draft', tracking=True, required=True)

    # ── Parties ───────────────────────────────────────────────────────

    project_id = fields.Many2one(
        'construction.project', string='المشروع | Project',
        required=True, ondelete='cascade', tracking=True, index=True)
    partner_id = fields.Many2one(
        'res.partner', string='المقاول | Contractor',
        domain="[('is_contractor', '=', True)]", tracking=True)
    engineer_id = fields.Many2one(
        'res.users', string='المهندس المسؤول | Engineer',
        default=lambda self: self.env.user, tracking=True)

    # ── Dates ─────────────────────────────────────────────────────────

    date_signed     = fields.Date(string='تاريخ التوقيع | Signed',   tracking=True)
    date_start      = fields.Date(string='تاريخ البداية | Start',    tracking=True)
    date_end        = fields.Date(string='الانتهاء المتوقع | Expected End', tracking=True)
    date_actual_end = fields.Date(string='الانتهاء الفعلي | Actual End')

    # ── Financial ─────────────────────────────────────────────────────

    currency_id = fields.Many2one(
        'res.currency', related='project_id.currency_id', store=True)
    contract_value = fields.Monetary(
        string='قيمة العقد | Contract Value', tracking=True)
    retention_percent = fields.Float(
        string='نسبة الضمان % | Retention %', default=5.0, digits=(5, 2))
    retention_amount = fields.Monetary(
        string='قيمة الضمان | Retention',
        compute='_compute_financials', store=True)
    advance_percent = fields.Float(
        string='نسبة الدفعة المقدمة % | Advance %', digits=(5, 2))
    advance_amount = fields.Monetary(
        string='قيمة الدفعة المقدمة | Advance',
        compute='_compute_financials', store=True)

    # ── Amendment / Addendum linking ──────────────────────────────────

    parent_contract_id = fields.Many2one(
        'construction.contract',
        string='العقد الأصلي | Parent Contract',
        domain="[('contract_type', '=', 'main'), ('project_id', '=', project_id)]",
        ondelete='restrict', tracking=True, index=True)
    amendment_ids = fields.One2many(
        'construction.contract', 'parent_contract_id',
        string='الملاحق والإضافات | Amendments')
    amendment_count = fields.Integer(
        compute='_compute_amendment_count', store=True, string='عدد الملاحق')
    amendment_value = fields.Monetary(
        string='قيمة التعديل ± | Amendment Value',
        tracking=True,
        help='المبلغ الإضافي أو التخفيضي لهذا الملحق — يمكن أن يكون سالباً')
    amendment_reason = fields.Char(
        string='سبب التعديل | Amendment Reason', tracking=True)

    # ── Effective value (main contracts) ──────────────────────────────

    total_amendments_value = fields.Monetary(
        string='إجمالي قيمة الملاحق | Total Amendments',
        compute='_compute_effective_value', store=True)
    effective_contract_value = fields.Monetary(
        string='القيمة الفعلية | Effective Contract Value',
        compute='_compute_effective_value', store=True)

    # ── BOQ link ──────────────────────────────────────────────────────

    boq_id = fields.Many2one(
        'construction.boq', string='جدول الكميات المرتبط | Linked BOQ',
        domain="[('project_id', '=', project_id)]")

    # ── Payment schedule ──────────────────────────────────────────────

    payment_line_ids = fields.One2many(
        'construction.payment.line', 'contract_id', string='جدول الدفعات')
    total_scheduled = fields.Monetary(
        string='إجمالي المجدول', compute='_compute_payment_totals', store=True)
    total_paid = fields.Monetary(
        string='إجمالي المدفوع', compute='_compute_payment_totals', store=True)
    balance_due = fields.Monetary(
        string='الرصيد المستحق', compute='_compute_payment_totals', store=True)

    # ── Certificate totals ────────────────────────────────────────────

    total_certified = fields.Monetary(
        string='إجمالي المعتمد | Total Certified',
        compute='_compute_certified_totals', store=True)
    remaining_to_certify = fields.Monetary(
        string='المتبقي للاعتماد | Remaining to Certify',
        compute='_compute_certified_totals', store=True)

    # ── Retention tracking ────────────────────────────────────────────

    total_retention_held = fields.Monetary(
        string='إجمالي الضمان المحتجز | Total Retention Held',
        compute='_compute_retention_balance', store=True)
    retention_released = fields.Monetary(
        string='الضمان المُفرج عنه | Retention Released',
        compute='_compute_retention_balance', store=True)
    retention_balance = fields.Monetary(
        string='رصيد الضمان | Retention Balance',
        compute='_compute_retention_balance', store=True)

    # ── Subcontracts ──────────────────────────────────────────────────

    subcontract_ids = fields.One2many(
        'construction.subcontract', 'contract_id', string='قائمة عقود الباطن')
    certificate_ids = fields.One2many(
        'construction.certificate', 'contract_id', string='قائمة المستخلصات')
    subcontract_count = fields.Integer(
        compute='_compute_counts', string='عقود الباطن', store=True)
    payment_count = fields.Integer(
        compute='_compute_counts', string='الدفعات', store=True)
    paid_payment_count = fields.Integer(
        compute='_compute_counts', string='مدفوع', store=True)
    certificate_count = fields.Integer(
        compute='_compute_counts', string='مستخلصات', store=True)

    # ── Terms ─────────────────────────────────────────────────────────

    payment_terms_notes = fields.Char(string='شروط الدفع | Payment Terms')
    scope_of_work       = fields.Html(string='نطاق العمل | Scope of Work')
    special_conditions  = fields.Html(string='شروط خاصة | Special Conditions')
    notes               = fields.Html(string='ملاحظات')

    # ── Computed ──────────────────────────────────────────────────────

    @api.depends('contract_value', 'retention_percent', 'advance_percent')
    def _compute_financials(self):
        for rec in self:
            rec.retention_amount = rec.contract_value * rec.retention_percent / 100.0
            rec.advance_amount   = rec.contract_value * rec.advance_percent   / 100.0

    @api.depends('amendment_ids')
    def _compute_amendment_count(self):
        for rec in self:
            rec.amendment_count = len(rec.amendment_ids)

    @api.depends(
        'amendment_ids.amendment_value', 'amendment_ids.state',
        'contract_value', 'contract_type')
    def _compute_effective_value(self):
        for rec in self:
            if rec.contract_type == 'main':
                amendments_total = sum(
                    a.amendment_value
                    for a in rec.amendment_ids
                    if a.state in ('active', 'completed')
                )
                rec.total_amendments_value = amendments_total
                rec.effective_contract_value = rec.contract_value + amendments_total
            else:
                rec.total_amendments_value = 0.0
                rec.effective_contract_value = rec.contract_value

    @api.depends(
        'certificate_ids.amount_gross', 'certificate_ids.state', 'contract_value')
    def _compute_certified_totals(self):
        for rec in self:
            certified = sum(
                c.amount_gross
                for c in rec.certificate_ids
                if c.state in ('review', 'approved', 'paid')
            )
            rec.total_certified = certified
            rec.remaining_to_certify = rec.contract_value - certified

    @api.depends(
        'certificate_ids.retention_amount', 'certificate_ids.state',
        'payment_line_ids.amount', 'payment_line_ids.state',
        'payment_line_ids.payment_type')
    def _compute_retention_balance(self):
        for rec in self:
            held = sum(
                c.retention_amount
                for c in rec.certificate_ids
                if c.state in ('approved', 'paid')
            )
            released = sum(
                l.amount
                for l in rec.payment_line_ids
                if l.payment_type == 'retention' and l.state == 'paid'
            )
            rec.total_retention_held = held
            rec.retention_released = released
            rec.retention_balance = held - released

    @api.depends('payment_line_ids.amount', 'payment_line_ids.state')
    def _compute_payment_totals(self):
        for rec in self:
            lines = rec.payment_line_ids
            rec.total_scheduled = sum(lines.mapped('amount'))
            rec.total_paid      = sum(l.amount for l in lines if l.state == 'paid')
            rec.balance_due     = sum(l.amount for l in lines if l.state in ('pending', 'due'))

    @api.depends('subcontract_ids', 'payment_line_ids', 'payment_line_ids.state',
                 'certificate_ids')
    def _compute_counts(self):
        for rec in self:
            rec.subcontract_count  = len(rec.subcontract_ids)
            rec.payment_count      = len(rec.payment_line_ids)
            rec.paid_payment_count = len(rec.payment_line_ids.filtered(
                lambda l: l.state == 'paid'))
            rec.certificate_count  = len(rec.certificate_ids)

    # ── Sequence ──────────────────────────────────────────────────────

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('contract_code', 'مسودة') == 'مسودة':
                vals['contract_code'] = (
                    self.env['ir.sequence'].next_by_code('construction.contract')
                    or 'CONT-NEW'
                )
        return super().create(vals_list)

    # ── Constraints ───────────────────────────────────────────────────

    @api.constrains('contract_type', 'parent_contract_id', 'project_id')
    def _check_amendment_parent(self):
        for rec in self:
            if rec.contract_type in ('amendment', 'addendum'):
                if not rec.parent_contract_id:
                    raise ValidationError(
                        'يجب تحديد العقد الأصلي للملاحق والإضافات.'
                    )
                if rec.parent_contract_id.contract_type != 'main':
                    raise ValidationError(
                        'العقد الأصلي يجب أن يكون من نوع "عقد رئيسي".'
                    )
                if rec.parent_contract_id.project_id != rec.project_id:
                    raise ValidationError(
                        'يجب أن يكون الملحق في نفس مشروع العقد الأصلي.'
                    )
            if rec.contract_type == 'main' and rec.parent_contract_id:
                raise ValidationError(
                    'العقد الرئيسي لا يمكن أن يرتبط بعقد أصلي آخر.'
                )

    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        for rec in self:
            if rec.date_start and rec.date_end and rec.date_end < rec.date_start:
                raise ValidationError('تاريخ الانتهاء يجب أن يكون بعد تاريخ البداية.')

    @api.constrains('retention_percent', 'advance_percent')
    def _check_percents(self):
        for rec in self:
            if not (0 <= rec.retention_percent <= 100):
                raise ValidationError('نسبة الضمان يجب أن تكون بين 0 و 100.')
            if not (0 <= rec.advance_percent <= 100):
                raise ValidationError('نسبة الدفعة المقدمة يجب أن تكون بين 0 و 100.')

    # ── State transitions ─────────────────────────────────────────────

    def action_activate(self):
        self.write({'state': 'active'})

    def action_complete(self):
        self.write({'state': 'completed'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_terminate(self):
        self.write({'state': 'terminated'})

    def action_reset_draft(self):
        self.write({'state': 'draft'})

    # ── Smart button actions ──────────────────────────────────────────

    def action_release_retention(self):
        self.ensure_one()
        if self.retention_balance <= 0:
            raise ValidationError(
                'لا يوجد رصيد ضمان متاح للإفراج.\n'
                f'إجمالي المحتجز: {self.total_retention_held:,.2f} — '
                f'المُفرج عنه: {self.retention_released:,.2f}'
            )
        next_seq = max(self.payment_line_ids.mapped('sequence') or [0]) + 10
        self.env['construction.payment.line'].create({
            'contract_id': self.id,
            'name': 'إفراج ضمان — Retention Release',
            'payment_type': 'retention',
            'amount': self.retention_balance,
            'sequence': next_seq,
            'state': 'pending',
        })
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'تم إنشاء طلب إفراج الضمان',
                'message': (
                    f'دفعة إفراج ضمان بقيمة {self.retention_balance:,.2f} '
                    f'{self.currency_id.name or "SAR"} — يمكن تعديل المبلغ قبل التسجيل.'
                ),
                'type': 'success',
                'sticky': False,
            },
        }

    def action_create_amendment(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'ملحق جديد — New Amendment',
            'res_model': 'construction.contract',
            'view_mode': 'form',
            'context': {
                'default_project_id': self.project_id.id,
                'default_partner_id': self.partner_id.id,
                'default_parent_contract_id': self.id,
                'default_contract_type': 'amendment',
                'default_retention_percent': self.retention_percent,
            },
        }

    def action_view_amendments(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'الملاحق والإضافات',
            'res_model': 'construction.contract',
            'view_mode': 'list,form',
            'domain': [('parent_contract_id', '=', self.id)],
            'context': {
                'default_parent_contract_id': self.id,
                'default_project_id': self.project_id.id,
            },
        }

    def action_view_certificates(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'المستخلصات',
            'res_model': 'construction.certificate',
            'view_mode': 'list,form',
            'domain': [('contract_id', '=', self.id)],
            'context': {
                'default_contract_id': self.id,
                'default_project_id': self.project_id.id,
            },
        }

    def action_view_subcontracts(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'عقود الباطن',
            'res_model': 'construction.subcontract',
            'view_mode': 'list,form',
            'domain': [('contract_id', '=', self.id)],
            'context': {'default_contract_id': self.id},
        }


class ConstructionSubcontract(models.Model):
    _name = 'construction.subcontract'
    _description = 'Construction Subcontract | عقد الباطن'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'
    _rec_name = 'name'

    # ── Identity ──────────────────────────────────────────────────────

    name = fields.Char(string='اسم عقد الباطن', required=True, tracking=True)
    subcontract_code = fields.Char(
        string='رقم عقد الباطن', readonly=True, copy=False, default='مسودة')
    contract_id = fields.Many2one(
        'construction.contract', string='العقد الرئيسي | Main Contract',
        required=True, ondelete='cascade', tracking=True, index=True)
    project_id = fields.Many2one(
        'construction.project',
        related='contract_id.project_id', store=True, string='المشروع')
    state = fields.Selection([
        ('draft',     'مسودة'),
        ('active',    'نشط'),
        ('completed', 'مكتمل'),
        ('cancelled', 'ملغي'),
    ], string='الحالة', default='draft', tracking=True, required=True)

    # ── Parties & Dates ───────────────────────────────────────────────

    partner_id = fields.Many2one(
        'res.partner', string='مقاول الباطن | Subcontractor',
        domain="[('is_contractor', '=', True)]", tracking=True)
    date_start = fields.Date(string='تاريخ البداية', tracking=True)
    date_end   = fields.Date(string='تاريخ الانتهاء', tracking=True)

    # ── Financial ─────────────────────────────────────────────────────

    currency_id = fields.Many2one(
        'res.currency', related='contract_id.currency_id', store=True)
    subcontract_value = fields.Monetary(
        string='قيمة عقد الباطن | Subcontract Value', tracking=True)
    retention_percent = fields.Float(
        string='نسبة الضمان % | Retention %', default=5.0, digits=(5, 2))
    retention_amount = fields.Monetary(
        string='قيمة الضمان',
        compute='_compute_retention', store=True)

    # ── Scope ─────────────────────────────────────────────────────────

    scope_description = fields.Html(string='نطاق الأعمال | Scope of Work')
    notes = fields.Char(string='ملاحظات')

    # ── Computed ──────────────────────────────────────────────────────

    @api.depends('subcontract_value', 'retention_percent')
    def _compute_retention(self):
        for rec in self:
            rec.retention_amount = rec.subcontract_value * rec.retention_percent / 100.0

    # ── Sequence ──────────────────────────────────────────────────────

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('subcontract_code', 'مسودة') == 'مسودة':
                vals['subcontract_code'] = (
                    self.env['ir.sequence'].next_by_code('construction.subcontract')
                    or 'SUB-NEW'
                )
        return super().create(vals_list)

    # ── Constraints ───────────────────────────────────────────────────

    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        for rec in self:
            if rec.date_start and rec.date_end and rec.date_end < rec.date_start:
                raise ValidationError('تاريخ الانتهاء يجب أن يكون بعد تاريخ البداية.')

    # ── State transitions ─────────────────────────────────────────────

    def action_activate(self):
        self.write({'state': 'active'})

    def action_complete(self):
        self.write({'state': 'completed'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_reset_draft(self):
        self.write({'state': 'draft'})


class ConstructionPaymentLine(models.Model):
    _name = 'construction.payment.line'
    _description = 'Payment Schedule Line | دفعة مجدولة'
    _order = 'sequence, due_date, id'

    # ── Parent ────────────────────────────────────────────────────────

    contract_id = fields.Many2one(
        'construction.contract', string='العقد',
        required=True, ondelete='cascade', index=True)
    sequence = fields.Integer(string='#', default=10)

    # ── Description ───────────────────────────────────────────────────

    name = fields.Char(string='وصف الدفعة | Description', required=True)
    payment_type = fields.Selection([
        ('advance',   'دفعة مقدمة — Advance'),
        ('milestone', 'مرحلة — Milestone'),
        ('retention', 'إفراج ضمان — Retention Release'),
        ('final',     'دفعة نهائية — Final'),
    ], string='النوع | Type', default='milestone', required=True)

    # ── Amount ────────────────────────────────────────────────────────

    currency_id = fields.Many2one(
        'res.currency', related='contract_id.currency_id', store=True)
    percent = fields.Float(
        string='النسبة % | Percent', digits=(5, 2),
        help='اختياري — يحسب المبلغ تلقائياً من قيمة العقد')
    amount = fields.Monetary(string='المبلغ | Amount')

    # ── Schedule ──────────────────────────────────────────────────────

    due_date  = fields.Date(string='تاريخ الاستحقاق | Due Date')
    state = fields.Selection([
        ('pending', 'معلق'),
        ('due',     'مستحق'),
        ('paid',    'مدفوع'),
    ], string='الحالة', default='pending')
    paid_date = fields.Date(string='تاريخ الدفع | Paid Date')
    notes = fields.Char(string='ملاحظات')

    # ── Auto-fill amount from percent ─────────────────────────────────

    @api.onchange('percent')
    def _onchange_percent(self):
        if self.percent and self.contract_id.contract_value:
            self.amount = self.contract_id.contract_value * self.percent / 100.0

    # ── Constraints ───────────────────────────────────────────────────

    @api.constrains('amount')
    def _check_amount(self):
        for rec in self:
            if rec.amount < 0:
                raise ValidationError('المبلغ لا يمكن أن يكون سالباً.')

    # ── State transitions ─────────────────────────────────────────────

    def action_mark_due(self):
        self.write({'state': 'due'})

    def action_mark_paid(self):
        self.write({'state': 'paid', 'paid_date': fields.Date.today()})

    def action_reset_pending(self):
        self.write({'state': 'pending', 'paid_date': False})
