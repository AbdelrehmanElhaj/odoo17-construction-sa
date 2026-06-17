from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ConstructionBoq(models.Model):
    _name = 'construction.boq'
    _description = 'Bill of Quantities | جدول الكميات'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'
    _rec_name = 'name'

    # ── Identity ──────────────────────────────────────────────────────

    name = fields.Char(string='عنوان BOQ | BOQ Title', required=True, tracking=True)
    boq_code = fields.Char(string='رقم BOQ', readonly=True, copy=False, default='مسودة')
    project_id = fields.Many2one(
        'construction.project',
        string='المشروع | Project',
        required=True,
        ondelete='cascade',
        tracking=True,
        index=True,
    )
    state = fields.Selection([
        ('draft',     'مسودة'),
        ('confirmed', 'معتمد'),
        ('cancelled', 'ملغي'),
    ], string='الحالة', default='draft', tracking=True, required=True)
    date = fields.Date(string='التاريخ | Date', default=fields.Date.today)
    currency_id = fields.Many2one(
        'res.currency',
        string='العملة',
        related='project_id.currency_id',
        store=True,
    )

    # ── Lines ─────────────────────────────────────────────────────────

    line_ids = fields.One2many('construction.boq.line', 'boq_id', string='البنود | Items')

    # ── Computed totals ───────────────────────────────────────────────

    line_count = fields.Integer(
        compute='_compute_totals', string='عدد البنود', store=True)
    total_estimated = fields.Monetary(
        compute='_compute_totals', string='الإجمالي التقديري', store=True)
    total_actual = fields.Monetary(
        compute='_compute_totals', string='الإجمالي الفعلي', store=True)
    variance = fields.Monetary(
        compute='_compute_totals', string='الفرق', store=True)

    notes = fields.Html(string='ملاحظات')

    # ── Compute ───────────────────────────────────────────────────────

    @api.depends('line_ids', 'line_ids.price_estimated', 'line_ids.price_actual')
    def _compute_totals(self):
        for rec in self:
            rec.line_count = len(rec.line_ids)
            rec.total_estimated = sum(rec.line_ids.mapped('price_estimated'))
            rec.total_actual = sum(rec.line_ids.mapped('price_actual'))
            rec.variance = rec.total_estimated - rec.total_actual

    # ── Sequence ──────────────────────────────────────────────────────

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('boq_code', 'مسودة') == 'مسودة':
                vals['boq_code'] = (
                    self.env['ir.sequence'].next_by_code('construction.boq') or 'BOQ-NEW'
                )
        return super().create(vals_list)

    # ── State transitions ─────────────────────────────────────────────

    def action_confirm(self):
        self.write({'state': 'confirmed'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_reset_draft(self):
        self.write({'state': 'draft'})

    # ── Excel import ──────────────────────────────────────────────────

    def action_import_excel(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'استيراد من Excel',
            'res_model': 'construction.boq.import',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_boq_id': self.id},
        }


class ConstructionBoqLine(models.Model):
    _name = 'construction.boq.line'
    _description = 'BOQ Line | بند جدول الكميات'
    _order = 'sequence, id'

    # ── Parent ────────────────────────────────────────────────────────

    boq_id = fields.Many2one(
        'construction.boq', string='BOQ',
        required=True, ondelete='cascade', index=True)
    sequence = fields.Integer(string='#', default=10)

    # ── Item description ──────────────────────────────────────────────

    item_code = fields.Char(string='كود البند | Code', size=20)
    description = fields.Char(string='الوصف | Description', required=True)
    description_ar = fields.Char(string='الوصف بالعربي')
    item_type = fields.Selection([
        ('material',    'مواد — Material'),
        ('labor',       'عمالة — Labor'),
        ('equipment',   'معدات — Equipment'),
        ('subcontract', 'مقاول باطن — Subcontract'),
        ('overhead',    'مصروفات عامة — Overhead'),
    ], string='النوع | Type', default='material', required=True)

    # ── Quantities ────────────────────────────────────────────────────

    uom_id = fields.Many2one('uom.uom', string='الوحدة | UOM')
    qty_estimated = fields.Float(string='الكمية التقديرية', digits=(12, 3))
    qty_actual    = fields.Float(
        string='الكمية الفعلية', digits=(12, 3),
        compute='_compute_qty_actual', store=True)
    unit_price    = fields.Float(string='سعر الوحدة', digits=(12, 2))

    # ── From certificates ─────────────────────────────────────────────

    cert_line_ids = fields.One2many(
        'construction.certificate.line', 'boq_line_id',
        string='بنود المستخلصات')

    # ── Prices (computed) ─────────────────────────────────────────────

    currency_id = fields.Many2one(
        'res.currency', related='boq_id.currency_id', store=True)
    price_estimated = fields.Monetary(
        string='إجمالي التقديري',
        compute='_compute_prices', store=True, currency_field='currency_id')
    price_actual = fields.Monetary(
        string='إجمالي الفعلي',
        compute='_compute_prices', store=True, currency_field='currency_id')
    variance = fields.Monetary(
        string='الفرق',
        compute='_compute_prices', store=True, currency_field='currency_id')

    # ── Subcontract ───────────────────────────────────────────────────

    subcontractor_id = fields.Many2one(
        'res.partner',
        string='مقاول الباطن',
        domain="[('is_contractor', '=', True)]",
    )
    notes = fields.Char(string='ملاحظات')

    # ── Compute ───────────────────────────────────────────────────────

    @api.depends('cert_line_ids', 'cert_line_ids.qty_this',
                 'cert_line_ids.certificate_id.state')
    def _compute_qty_actual(self):
        for rec in self:
            rec.qty_actual = sum(
                l.qty_this for l in rec.cert_line_ids
                if l.certificate_id.state in ('approved', 'paid')
            )

    @api.depends('qty_estimated', 'qty_actual', 'unit_price')
    def _compute_prices(self):
        for rec in self:
            rec.price_estimated = rec.qty_estimated * rec.unit_price
            rec.price_actual    = rec.qty_actual    * rec.unit_price
            rec.variance        = rec.price_estimated - rec.price_actual

    # ── Constraint ────────────────────────────────────────────────────

    @api.constrains('qty_estimated', 'unit_price')
    def _check_positive(self):
        for rec in self:
            if rec.qty_estimated < 0:
                raise ValidationError('الكمية التقديرية يجب أن تكون صفراً أو أكثر.')
            if rec.unit_price < 0:
                raise ValidationError('سعر الوحدة يجب أن يكون صفراً أو أكثر.')
