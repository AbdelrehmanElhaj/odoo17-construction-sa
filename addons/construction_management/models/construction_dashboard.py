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

        projects  = Project.search([])
        contracts = Contract.search([])
        certs     = Certificate.search([])
        paylines  = PayLine.search([])

        total_cv  = sum(contracts.mapped('contract_value'))
        total_tp  = sum(contracts.mapped('total_paid'))
        total_bd  = sum(contracts.mapped('balance_due'))
        cert_appr = certs.filtered(lambda c: c.state in ('approved', 'paid'))
        total_cer = sum(cert_appr.mapped('amount_net'))

        for rec in self:
            rec.count_projects_all      = len(projects)
            rec.count_projects_active   = len(projects.filtered(lambda p: p.state == 'active'))
            rec.count_projects_done     = len(projects.filtered(lambda p: p.state == 'done'))
            rec.count_projects_delayed  = len(projects.filtered(
                lambda p: p.state not in ('done', 'cancelled')
                and p.date_end and p.date_end < today))

            rec.total_contract_value    = total_cv
            rec.total_certified         = total_cer
            rec.total_paid              = total_tp
            rec.total_balance_due       = total_bd

            rec.count_cert_draft    = len(certs.filtered(lambda c: c.state == 'draft'))
            rec.count_cert_review   = len(certs.filtered(lambda c: c.state == 'review'))
            rec.count_cert_approved = len(certs.filtered(lambda c: c.state == 'approved'))
            rec.count_cert_paid     = len(certs.filtered(lambda c: c.state == 'paid'))

            rec.count_payment_due     = len(paylines.filtered(lambda l: l.state == 'due'))
            rec.count_payment_overdue = len(paylines.filtered(
                lambda l: l.state in ('pending', 'due')
                and l.due_date and l.due_date < today))

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
