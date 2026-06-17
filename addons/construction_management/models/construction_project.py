from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ConstructionProject(models.Model):
    _name = 'construction.project'
    _description = 'Construction Project | مشروع المقاولات'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_start desc, id desc'
    _rec_name = 'name'

    # ── Identity ──────────────────────────────────────────────────────

    name = fields.Char(
        string='اسم المشروع | Project Name',
        required=True,
        tracking=True,
    )
    project_code = fields.Char(
        string='رقم المشروع | Project Code',
        readonly=True,
        copy=False,
        default='مسودة',
    )
    project_type = fields.Selection([
        ('residential', 'سكني — Residential'),
        ('commercial',  'تجاري — Commercial'),
        ('infra',       'بنية تحتية — Infrastructure'),
        ('roads',       'طرق — Roads'),
        ('industrial',  'صناعي — Industrial'),
    ], string='نوع المشروع | Project Type', tracking=True)

    state = fields.Selection([
        ('draft',     'مسودة'),
        ('active',    'نشط'),
        ('paused',    'موقوف مؤقتاً'),
        ('done',      'مكتمل'),
        ('cancelled', 'ملغي'),
    ], string='الحالة | Status',
        default='draft',
        tracking=True,
        required=True,
    )

    # ── Parties ───────────────────────────────────────────────────────

    partner_id = fields.Many2one(
        'res.partner',
        string='العميل / المالك | Client',
        tracking=True,
        index=True,
    )
    engineer_id = fields.Many2one(
        'res.users',
        string='المهندس المسؤول | Engineer',
        default=lambda self: self.env.user,
        tracking=True,
        index=True,
    )

    # ── Dates ─────────────────────────────────────────────────────────

    date_start = fields.Date(string='تاريخ البداية | Start Date', tracking=True)
    date_end   = fields.Date(string='تاريخ الانتهاء المتوقع | Expected End', tracking=True)

    # ── Location — Saudi National Address ─────────────────────────────

    region_id      = fields.Many2one('construction.saudi.region', string='المنطقة | Region')
    city_id        = fields.Many2one(
        'construction.saudi.city',
        string='المدينة | City',
        domain="[('region_id', '=', region_id)]",
    )
    site_building_no  = fields.Char(string='رقم المبنى | Building No.', size=4)
    site_street       = fields.Char(string='الشارع | Street')
    site_secondary_no = fields.Char(string='الرقم الإضافي | Secondary No.', size=4)
    site_district     = fields.Char(string='الحي | District')
    site_postal_code  = fields.Char(string='الرمز البريدي | Postal Code', size=5)
    location          = fields.Char(string='وصف الموقع | Site Description')
    site_national_address = fields.Char(
        string='العنوان الوطني | National Address',
        compute='_compute_site_address',
        store=True,
    )

    # ── Permits ───────────────────────────────────────────────────────

    building_permit   = fields.Char(string='رقم رخصة البناء | Building Permit')
    municipality_ref  = fields.Char(string='مرجع البلدية | Municipality Ref')
    permit_expiry     = fields.Date(string='انتهاء الرخصة | Permit Expiry')

    # ── Financials ────────────────────────────────────────────────────

    currency_id = fields.Many2one(
        'res.currency',
        string='العملة | Currency',
        default=lambda self: self.env.ref('base.SAR', raise_if_not_found=False),
    )
    contract_value    = fields.Monetary(string='قيمة العقد | Contract Value', tracking=True)
    budget_estimated  = fields.Monetary(string='الميزانية التقديرية | Estimated Budget')
    cost_actual       = fields.Monetary(
        string='التكلفة الفعلية | Actual Cost',
        compute='_compute_financials',
        store=True,
    )
    progress_percent  = fields.Float(
        string='نسبة الإنجاز | Progress %',
        compute='_compute_financials',
        store=True,
        digits=(5, 2),
    )

    # ── Description ───────────────────────────────────────────────────

    description = fields.Html(string='وصف المشروع | Description')

    # ── Relational ────────────────────────────────────────────────────

    boq_ids         = fields.One2many('construction.boq',         'project_id', string='جداول الكميات')
    contract_ids    = fields.One2many('construction.contract',    'project_id', string='العقود المرتبطة')
    certificate_ids = fields.One2many('construction.certificate', 'project_id', string='المستخلصات المرتبطة')
    boq_count         = fields.Integer(compute='_compute_counts', string='BOQ',   store=True)
    contract_count    = fields.Integer(compute='_compute_counts', string='عقود',  store=True)
    certificate_count = fields.Integer(compute='_compute_counts', string='شهادات', store=True)

    # ── Computed ──────────────────────────────────────────────────────

    @api.depends('site_building_no', 'site_street', 'site_secondary_no',
                 'site_district', 'city_id', 'region_id', 'site_postal_code')
    def _compute_site_address(self):
        for rec in self:
            parts = []
            if rec.site_building_no and rec.site_street:
                parts.append(f"{rec.site_building_no} {rec.site_street}")
            if rec.site_secondary_no:
                parts.append(rec.site_secondary_no)
            if rec.site_district:
                parts.append(rec.site_district)
            if rec.city_id:
                parts.append(rec.city_id.name_ar)
            if rec.region_id:
                parts.append(rec.region_id.name_ar)
            if rec.site_postal_code:
                parts.append(rec.site_postal_code)
            rec.site_national_address = '، '.join(parts) if parts else False

    @api.depends('contract_ids.total_paid',
                 'certificate_ids.amount_net', 'certificate_ids.state',
                 'contract_ids.contract_value')
    def _compute_financials(self):
        for rec in self:
            rec.cost_actual = sum(rec.contract_ids.mapped('total_paid'))
            approved = rec.certificate_ids.filtered(
                lambda c: c.state in ('approved', 'paid'))
            total_certified = sum(approved.mapped('amount_net'))
            total_contract  = sum(rec.contract_ids.mapped('contract_value'))
            rec.progress_percent = (
                min(100.0, total_certified / total_contract * 100.0)
                if total_contract > 0 else 0.0
            )

    @api.depends('boq_ids', 'contract_ids', 'certificate_ids')
    def _compute_counts(self):
        for rec in self:
            rec.boq_count         = len(rec.boq_ids)
            rec.contract_count    = len(rec.contract_ids)
            rec.certificate_count = len(rec.certificate_ids)

    # ── Region auto-fill from city ────────────────────────────────────

    @api.onchange('city_id')
    def _onchange_city_id(self):
        if self.city_id and self.city_id.region_id:
            self.region_id = self.city_id.region_id

    # ── Constraints ───────────────────────────────────────────────────

    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        for rec in self:
            if rec.date_start and rec.date_end and rec.date_end < rec.date_start:
                raise ValidationError('تاريخ الانتهاء يجب أن يكون بعد تاريخ البداية.')

    @api.constrains('site_building_no')
    def _check_site_building_no(self):
        import re
        for rec in self:
            if rec.site_building_no and not re.match(r'^\d{4}$', rec.site_building_no.strip()):
                raise ValidationError('رقم المبنى يجب أن يتكون من 4 أرقام بالضبط.')

    @api.constrains('site_postal_code')
    def _check_site_postal_code(self):
        import re
        for rec in self:
            if rec.site_postal_code and not re.match(r'^\d{5}$', rec.site_postal_code.strip()):
                raise ValidationError('الرمز البريدي يجب أن يتكون من 5 أرقام بالضبط.')

    # ── Sequence ──────────────────────────────────────────────────────

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('project_code', 'مسودة') == 'مسودة':
                vals['project_code'] = self.env['ir.sequence'].next_by_code('construction.project') or 'PROJ-NEW'
        return super().create(vals_list)

    # ── State transitions ─────────────────────────────────────────────

    def action_activate(self):
        self.write({'state': 'active'})

    def action_pause(self):
        self.write({'state': 'paused'})

    def action_done(self):
        self.write({'state': 'done'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_reset_draft(self):
        self.write({'state': 'draft'})

    # ── Smart button stubs (replaced in Phases 4–6) ───────────────────

    def action_view_boq(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'جداول الكميات | BOQ',
            'res_model': 'construction.boq',
            'view_mode': 'list,form',
            'domain': [('project_id', '=', self.id)],
            'context': {'default_project_id': self.id},
        }

    def action_view_contracts(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'العقود | Contracts',
            'res_model': 'construction.contract',
            'view_mode': 'list,form',
            'domain': [('project_id', '=', self.id)],
            'context': {'default_project_id': self.id},
        }

    def action_view_certificates(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'المستخلصات | Certificates',
            'res_model': 'construction.certificate',
            'view_mode': 'list,form',
            'domain': [('project_id', '=', self.id)],
            'context': {'default_project_id': self.id},
        }
