from odoo import api, fields, models

class ConstructionDashboard(models.Model):
    _name = 'construction.dashboard'
    _description = 'لوحة متابعة المقاولات | Construction Dashboard'

    name = fields.Char(default='لوحة المتابعة', readonly=True)

    # ── Project KPIs ─────────────────────────────────────────────────
    count_projects_all       = fields.Integer(compute='_compute_kpis', store=False)
    count_projects_active    = fields.Integer(compute='_compute_kpis', store=False)
    count_projects_done      = fields.Integer(compute='_compute_kpis', store=False)
    count_projects_delayed   = fields.Integer(compute='_compute_kpis', store=False)

    # ── Financial KPIs ───────────────────────────────────────────────
    total_contract_value     = fields.Float(digits=(18, 2), compute='_compute_kpis', store=False)
    total_certified          = fields.Float(digits=(18, 2), compute='_compute_kpis', store=False)
    total_paid               = fields.Float(digits=(18, 2), compute='_compute_kpis', store=False)
    total_balance_due        = fields.Float(digits=(18, 2), compute='_compute_kpis', store=False)

    # ── Certificate KPIs ─────────────────────────────────────────────
    count_cert_draft         = fields.Integer(compute='_compute_kpis', store=False)
    count_cert_review        = fields.Integer(compute='_compute_kpis', store=False)
    count_cert_approved      = fields.Integer(compute='_compute_kpis', store=False)
    count_cert_paid          = fields.Integer(compute='_compute_kpis', store=False)

    # ── Payment KPIs ─────────────────────────────────────────────────
    count_payment_due        = fields.Integer(compute='_compute_kpis', store=False)
    count_payment_overdue    = fields.Integer(compute='_compute_kpis', store=False)

    # ── Expiry KPIs ──────────────────────────────────────────────────
    count_license_expiring  = fields.Integer(compute='_compute_kpis', store=False)
    count_license_expired   = fields.Integer(compute='_compute_kpis', store=False)
    count_permit_expiring   = fields.Integer(compute='_compute_kpis', store=False)
    count_permit_expired    = fields.Integer(compute='_compute_kpis', store=False)

    # ── Currency ─────────────────────────────────────────────────────
    currency_symbol = fields.Char(compute='_compute_currency_symbol', store=False)

    @api.depends()
    def _compute_currency_symbol(self):
        sar = self.env.ref('base.SAR', raise_if_not_found=False)
        symbol = sar.symbol if sar else 'SAR'
        for rec in self:
            rec.currency_symbol = symbol

    @api.depends()
    def _compute_kpis(self):
        today = fields.Date.today()
        Project     = self.env['construction.project']
        Contract    = self.env['construction.contract']
        Certificate = self.env['construction.certificate']
        PayLine     = self.env['construction.payment.line']

        # Project counts — DB-level COUNT, no records loaded into Python
        count_all     = Project.search_count([])
        count_active  = Project.search_count([('state', '=', 'active')])
        count_done    = Project.search_count([('state', '=', 'done')])
        count_delayed = Project.search_count([
            ('state', 'not in', ['done', 'cancelled']),
            ('date_end', '!=', False),
            ('date_end', '<', today),
        ])

        # Financial aggregations — DB SUM via read_group, no records loaded
        contract_agg = Contract.read_group(
            [], ['contract_value:sum', 'total_paid:sum', 'balance_due:sum'], [])
        ca = contract_agg[0] if contract_agg else {}
        total_cv = ca.get('contract_value') or 0.0
        total_tp = ca.get('total_paid') or 0.0
        total_bd = ca.get('balance_due') or 0.0

        cert_agg = Certificate.read_group(
            [('state', 'in', ('approved', 'paid'))], ['amount_net:sum'], [])
        total_cer = (cert_agg[0].get('amount_net') or 0.0) if cert_agg else 0.0

        # Certificate counts by state
        count_cert_draft    = Certificate.search_count([('state', '=', 'draft')])
        count_cert_review   = Certificate.search_count([('state', '=', 'review')])
        count_cert_approved = Certificate.search_count([('state', '=', 'approved')])
        count_cert_paid     = Certificate.search_count([('state', '=', 'paid')])

        # Payment counts — two targeted COUNT queries
        count_due     = PayLine.search_count([('state', '=', 'due')])
        count_overdue = PayLine.search_count([
            ('state', 'in', ['pending', 'due']),
            ('due_date', '!=', False),
            ('due_date', '<', today),
        ])

        # Expiry counts — stored computed fields, so search_count works
        Partner = self.env['res.partner']
        count_lic_expiring = Partner.search_count([
            ('is_contractor', '=', True), ('license_status', '=', 'expiring')])
        count_lic_expired  = Partner.search_count([
            ('is_contractor', '=', True), ('license_status', '=', 'expired')])
        count_perm_expiring = Project.search_count([
            ('state', 'not in', ['done', 'cancelled']), ('permit_status', '=', 'expiring')])
        count_perm_expired  = Project.search_count([
            ('state', 'not in', ['done', 'cancelled']), ('permit_status', '=', 'expired')])

        for rec in self:
            rec.count_projects_all     = count_all
            rec.count_projects_active  = count_active
            rec.count_projects_done    = count_done
            rec.count_projects_delayed = count_delayed

            rec.total_contract_value = total_cv
            rec.total_certified      = total_cer
            rec.total_paid           = total_tp
            rec.total_balance_due    = total_bd

            rec.count_cert_draft    = count_cert_draft
            rec.count_cert_review   = count_cert_review
            rec.count_cert_approved = count_cert_approved
            rec.count_cert_paid     = count_cert_paid

            rec.count_payment_due     = count_due
            rec.count_payment_overdue = count_overdue

            rec.count_license_expiring = count_lic_expiring
            rec.count_license_expired  = count_lic_expired
            rec.count_permit_expiring  = count_perm_expiring
            rec.count_permit_expired   = count_perm_expired

    def action_refresh(self):
        self.ensure_one()
        # Invalidate the computed cache so _compute_kpis runs again on next read
        self.invalidate_recordset()
        return self.env.ref(
            'construction_management.action_open_dashboard_server').read()[0]

    @api.model
    def action_open(self):
        rec = self.search([], limit=1)
        if not rec:
            rec = self.create({'name': 'لوحة المتابعة'})
        action = self.env.ref(
            'construction_management.action_construction_dashboard').read()[0]
        action['res_id'] = rec.id
        action['flags'] = {'mode': 'readonly'}
        return action
