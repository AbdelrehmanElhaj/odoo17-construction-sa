import re
from datetime import date, timedelta
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # ── Saudi Identity ────────────────────────────────────────────────

    saudi_id_type = fields.Selection([
        ('national_id', 'هوية وطنية — National ID'),
        ('iqama',       'إقامة — Iqama'),
        ('cr',          'سجل تجاري — CR'),
        ('gcc',         'هوية خليجي — GCC'),
        ('passport',    'جواز سفر — Passport'),
    ], string='نوع الهوية | ID Type')

    saudi_id_number = fields.Char(string='رقم الهوية | ID Number', size=20)
    saudi_id_expiry = fields.Date(string='تاريخ الانتهاء | ID Expiry')
    saudi_id_status = fields.Selection([
        ('valid',    'سارية'),
        ('expiring', 'تنتهي قريباً'),
        ('expired',  'منتهية'),
    ], string='حالة الهوية', compute='_compute_saudi_id_status')

    # ── Saudi Phone Numbers ───────────────────────────────────────────

    mobile_sa      = fields.Char(string='جوال | Mobile SA',       size=20)
    phone_work_sa  = fields.Char(string='هاتف العمل | Work Phone', size=15)
    whatsapp_sa    = fields.Char(string='واتساب | WhatsApp',       size=20)

    # ── National Address — Saudi Post Standard ────────────────────────

    sa_building_no   = fields.Char(string='رقم المبنى | Building No.',    size=4)
    sa_street_name   = fields.Char(string='اسم الشارع | Street Name')
    sa_secondary_no  = fields.Char(string='الرقم الإضافي | Secondary No.', size=4)
    sa_district      = fields.Char(string='الحي | District')
    sa_city_id       = fields.Many2one('construction.saudi.city',   string='المدينة | City')
    sa_region_id     = fields.Many2one(
        'construction.saudi.region',
        string='المنطقة | Region',
        compute='_compute_sa_region',
        store=True,
        readonly=False,
    )
    sa_postal_code   = fields.Char(string='الرمز البريدي | Postal Code', size=5)
    sa_national_address = fields.Char(
        string='العنوان الوطني | National Address',
        compute='_compute_national_address',
        store=True,
    )

    # ── Contractor Fields ─────────────────────────────────────────────

    is_contractor          = fields.Boolean(string='مقاول | Contractor')
    commercial_registration = fields.Char(string='رقم السجل التجاري | CR No.', size=10)
    contractor_grade       = fields.Selection([
        ('A', 'الدرجة الأولى — A'),
        ('B', 'الدرجة الثانية — B'),
        ('C', 'الدرجة الثالثة — C'),
        ('D', 'الدرجة الرابعة — D'),
    ], string='درجة الترخيص | Grade')
    contractor_license = fields.Char(string='رقم الترخيص المهني | License No.')
    license_expiry     = fields.Date(string='تاريخ انتهاء الترخيص | License Expiry')
    license_status     = fields.Selection([
        ('valid',    'ساري'),
        ('expiring', 'ينتهي قريباً'),
        ('expired',  'منتهي'),
    ], string='حالة الترخيص | License Status',
        compute='_compute_license_status', store=True)
    contractor_type    = fields.Selection([
        ('general',   'مقاول عام — General'),
        ('civil',     'أعمال مدنية — Civil'),
        ('mep',       'ميكانيكا وكهرباء — MEP'),
        ('finishing', 'تشطيبات — Finishing'),
    ], string='تصنيف المقاول | Type')
    retention_percent = fields.Float(
        string='نسبة الضمان المحتجز | Retention %',
        default=5.0,
        digits=(5, 2),
    )

    # ── Computed ──────────────────────────────────────────────────────

    @api.depends('saudi_id_expiry')
    def _compute_saudi_id_status(self):
        today = date.today()
        for rec in self:
            if not rec.saudi_id_expiry:
                rec.saudi_id_status = False
            elif rec.saudi_id_expiry <= today:
                rec.saudi_id_status = 'expired'
            elif rec.saudi_id_expiry <= today + timedelta(days=90):
                rec.saudi_id_status = 'expiring'
            else:
                rec.saudi_id_status = 'valid'

    @api.depends('license_expiry')
    def _compute_license_status(self):
        today = date.today()
        for rec in self:
            if not rec.license_expiry:
                rec.license_status = False
            elif rec.license_expiry <= today:
                rec.license_status = 'expired'
            elif rec.license_expiry <= today + timedelta(days=30):
                rec.license_status = 'expiring'
            else:
                rec.license_status = 'valid'

    @api.depends('sa_city_id')
    def _compute_sa_region(self):
        for rec in self:
            if rec.sa_city_id:
                rec.sa_region_id = rec.sa_city_id.region_id
            # don't clear if region was set manually without a city

    @api.depends('sa_building_no', 'sa_street_name', 'sa_secondary_no',
                 'sa_district', 'sa_city_id', 'sa_region_id', 'sa_postal_code')
    def _compute_national_address(self):
        for rec in self:
            parts = []
            if rec.sa_building_no and rec.sa_street_name:
                parts.append(f"{rec.sa_building_no} {rec.sa_street_name}")
            if rec.sa_secondary_no:
                parts.append(rec.sa_secondary_no)
            if rec.sa_district:
                parts.append(rec.sa_district)
            if rec.sa_city_id:
                parts.append(rec.sa_city_id.name_ar)
            if rec.sa_region_id:
                parts.append(rec.sa_region_id.name_ar)
            if rec.sa_postal_code:
                parts.append(rec.sa_postal_code)
            rec.sa_national_address = '، '.join(parts) if parts else False

    # ── Constraints ───────────────────────────────────────────────────

    @api.constrains('saudi_id_number', 'saudi_id_type')
    def _check_saudi_id(self):
        for rec in self:
            if not rec.saudi_id_number or not rec.saudi_id_type:
                continue
            num = rec.saudi_id_number.strip()
            if rec.saudi_id_type == 'national_id':
                if not re.match(r'^1\d{9}$', num):
                    raise ValidationError(
                        'رقم الهوية الوطنية يجب أن يبدأ بـ 1 ويتكون من 10 أرقام.\n'
                        'مثال: 1XXXXXXXXX'
                    )
            elif rec.saudi_id_type == 'iqama':
                if not re.match(r'^2\d{9}$', num):
                    raise ValidationError(
                        'رقم الإقامة يجب أن يبدأ بـ 2 ويتكون من 10 أرقام.\n'
                        'مثال: 2XXXXXXXXX'
                    )
            elif rec.saudi_id_type == 'cr':
                if not re.match(r'^\d{10}$', num):
                    raise ValidationError('رقم السجل التجاري يجب أن يتكون من 10 أرقام.')

    @api.constrains('mobile_sa')
    def _check_mobile_sa(self):
        pattern = r'^(05\d{8}|\+9665\d{8}|009665\d{8})$'
        for rec in self:
            if rec.mobile_sa and not re.match(pattern, rec.mobile_sa.strip()):
                raise ValidationError(
                    'رقم الجوال غير صحيح.\n'
                    'الصيغ المقبولة: 05XXXXXXXX  أو  +9665XXXXXXXX  أو  009665XXXXXXXX'
                )

    @api.constrains('phone_work_sa')
    def _check_phone_work_sa(self):
        for rec in self:
            if rec.phone_work_sa and not re.match(r'^01\d{8}$', rec.phone_work_sa.strip()):
                raise ValidationError('هاتف العمل غير صحيح. الصيغة المقبولة: 01XXXXXXXX')

    @api.constrains('whatsapp_sa')
    def _check_whatsapp_sa(self):
        for rec in self:
            if rec.whatsapp_sa and not re.match(r'^\+9665\d{8}$', rec.whatsapp_sa.strip()):
                raise ValidationError('رقم واتساب غير صحيح. الصيغة المقبولة: +9665XXXXXXXX')

    @api.constrains('sa_building_no')
    def _check_building_no(self):
        for rec in self:
            if rec.sa_building_no and not re.match(r'^\d{4}$', rec.sa_building_no.strip()):
                raise ValidationError('رقم المبنى يجب أن يتكون من 4 أرقام بالضبط. مثال: 3542')

    @api.constrains('sa_secondary_no')
    def _check_secondary_no(self):
        for rec in self:
            if rec.sa_secondary_no and not re.match(r'^\d{4}$', rec.sa_secondary_no.strip()):
                raise ValidationError('الرقم الإضافي يجب أن يتكون من 4 أرقام بالضبط. مثال: 7894')

    @api.constrains('sa_postal_code')
    def _check_postal_code(self):
        for rec in self:
            if rec.sa_postal_code and not re.match(r'^\d{5}$', rec.sa_postal_code.strip()):
                raise ValidationError('الرمز البريدي يجب أن يتكون من 5 أرقام بالضبط. مثال: 12212')

    @api.constrains('commercial_registration')
    def _check_cr(self):
        for rec in self:
            if rec.commercial_registration and not re.match(r'^\d{10}$', rec.commercial_registration.strip()):
                raise ValidationError('رقم السجل التجاري يجب أن يتكون من 10 أرقام.')
