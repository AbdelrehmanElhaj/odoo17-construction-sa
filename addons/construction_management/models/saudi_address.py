from odoo import models, fields, api


class ConstructionSaudiRegion(models.Model):
    _name = 'construction.saudi.region'
    _description = 'Saudi Administrative Region | المنطقة الإدارية'
    _order = 'name'
    _rec_name = 'name_ar'

    name = fields.Char(string='Region Name (EN)', required=True)
    name_ar = fields.Char(string='اسم المنطقة', required=True)
    code = fields.Char(string='Code', size=5)
    city_ids = fields.One2many('construction.saudi.city', 'region_id', string='Cities | المدن')
    city_count = fields.Integer(compute='_compute_city_count', string='Cities', store=True)

    @api.depends('city_ids')
    def _compute_city_count(self):
        for rec in self:
            rec.city_count = len(rec.city_ids)

    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, f"{rec.name_ar} — {rec.name}"))
        return result


class ConstructionSaudiCity(models.Model):
    _name = 'construction.saudi.city'
    _description = 'Saudi City | المدينة'
    _order = 'name_ar'
    _rec_name = 'name_ar'

    name = fields.Char(string='City Name (EN)', required=True)
    name_ar = fields.Char(string='اسم المدينة', required=True)
    region_id = fields.Many2one(
        'construction.saudi.region',
        string='Region | المنطقة',
        required=True,
        ondelete='cascade',
        index=True,
    )

    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, f"{rec.name_ar} ({rec.region_id.name_ar})"))
        return result
