#!/usr/bin/env python3
"""
Realistic demo data for Construction Management (Odoo 17).
5 projects · 5 contractors · 3 clients · 5 BOQs · 5 contracts
7 subcontracts · 8 certificates with full workflow progression
"""
import odoo, sys

DB = 'ConstructionDemo'
odoo.tools.config.parse_config(['--database=' + DB, '--no-http', '--log-level=error'])
from odoo.modules.registry import Registry
from odoo.api import Environment

def p(msg): print(msg, flush=True)

def main():
    registry = Registry(DB)
    with registry.cursor() as cr:
        env = Environment(cr, odoo.SUPERUSER_ID, {})
        try:
            run(env)
            cr.commit()
            p('\n✓ Realistic demo data loaded.')
        except Exception as e:
            cr.rollback()
            import traceback; traceback.print_exc()
            sys.exit(1)

def run(env):
    Region = env['construction.saudi.region']
    City   = env['construction.saudi.city']
    Partner = env['res.partner']

    # ── Regions ───────────────────────────────────────────────────────────
    p('[1/8] Locating regions and cities...')
    r_riyadh  = Region.search([('name', 'ilike', 'Riyadh')],  limit=1)
    r_western = (Region.search([('name', 'ilike', 'Makkah')], limit=1)
                 or Region.search([('name', 'ilike', 'Mecca')], limit=1)
                 or Region.search([('name', 'ilike', 'Western')], limit=1))
    r_eastern = (Region.search([('name', 'ilike', 'Eastern')], limit=1)
                 or Region.search([('name', 'ilike', 'Sharqiyah')], limit=1))

    def city(name, region=None):
        d = [('name', 'ilike', name)]
        if region: d.append(('region_id', '=', region.id))
        return City.search(d, limit=1)

    c_riyadh = city('Riyadh',  r_riyadh)  or City.search([], limit=1)
    c_jeddah = city('Jeddah',  r_western) or c_riyadh
    c_dammam = city('Dammam',  r_eastern) or c_riyadh
    c_jubail = city('Jubail',  r_eastern) or c_dammam
    p(f'  Riyadh={c_riyadh.id}  Jeddah={c_jeddah.id}  Dammam={c_dammam.id}  Jubail={c_jubail.id}')

    # ── Partners ──────────────────────────────────────────────────────────
    p('[2/8] Creating partners...')

    def partner(vals):
        cr_no = vals.get('commercial_registration')
        if cr_no:
            ex = Partner.search([('commercial_registration', '=', cr_no)], limit=1)
            if ex: return ex
        return Partner.create(vals)

    cont_general = partner({
        'name': 'شركة البناء والتطوير السعودية', 'is_company': True,
        'is_contractor': True, 'commercial_registration': '1010456781',
        'contractor_grade': 'A', 'contractor_type': 'general',
        'contractor_license': 'MCL-2020-00456', 'license_expiry': '2027-03-31',
        'retention_percent': 5.0, 'mobile_sa': '0501234561',
        'sa_building_no': '1100', 'sa_street_name': 'طريق الملك عبدالعزيز',
        'sa_secondary_no': '2200', 'sa_district': 'حي العليا',
        'sa_city_id': c_riyadh.id, 'sa_postal_code': '11564',
    })
    cont_civil = partner({
        'name': 'مجموعة الإنشاءات المدنية الخليجية', 'is_company': True,
        'is_contractor': True, 'commercial_registration': '4030567892',
        'contractor_grade': 'A', 'contractor_type': 'civil',
        'contractor_license': 'CCL-2019-00789', 'license_expiry': '2026-09-30',
        'retention_percent': 5.0, 'mobile_sa': '0551234562',
        'sa_building_no': '2200', 'sa_street_name': 'شارع الأمير سلطان',
        'sa_secondary_no': '3300', 'sa_district': 'حي الروضة',
        'sa_city_id': c_jeddah.id, 'sa_postal_code': '21523',
    })
    cont_mep = partner({
        'name': 'شركة الأعمال الكهروميكانيكية المتقدمة', 'is_company': True,
        'is_contractor': True, 'commercial_registration': '2050678913',
        'contractor_grade': 'B', 'contractor_type': 'mep',
        'contractor_license': 'MEP-2021-00234', 'license_expiry': '2026-12-31',
        'retention_percent': 5.0, 'mobile_sa': '0561234563',
        'sa_building_no': '3300', 'sa_street_name': 'شارع الملك فيصل',
        'sa_secondary_no': '4400', 'sa_district': 'حي الشاطئ',
        'sa_city_id': c_dammam.id, 'sa_postal_code': '32222',
    })
    cont_finishing = partner({
        'name': 'مؤسسة التشطيبات العصرية', 'is_company': True,
        'is_contractor': True, 'commercial_registration': '1040789124',
        'contractor_grade': 'C', 'contractor_type': 'finishing',
        'contractor_license': 'FIN-2022-00567', 'license_expiry': '2027-06-30',
        'retention_percent': 5.0, 'mobile_sa': '0571234564',
        'sa_building_no': '4400', 'sa_street_name': 'طريق المدينة المنورة',
        'sa_secondary_no': '5500', 'sa_district': 'حي الصفا',
        'sa_city_id': c_riyadh.id, 'sa_postal_code': '11476',
    })
    cont_roads = partner({
        'name': 'شركة الطرق والمشاريع الكبرى', 'is_company': True,
        'is_contractor': True, 'commercial_registration': '2080890235',
        'contractor_grade': 'A', 'contractor_type': 'civil',
        'contractor_license': 'RCL-2018-01234', 'license_expiry': '2027-08-31',
        'retention_percent': 5.0, 'mobile_sa': '0581234565',
        'sa_building_no': '5500', 'sa_street_name': 'شارع الصناعة',
        'sa_secondary_no': '6600', 'sa_district': 'حي الجبيل الصناعية',
        'sa_city_id': c_jubail.id, 'sa_postal_code': '35718',
    })
    client_amanah = partner({
        'name': 'أمانة منطقة الرياض', 'is_company': True,
        'commercial_registration': '1010111223',
        'mobile_sa': '0503334455',
        'sa_building_no': '3333', 'sa_street_name': 'طريق المطار',
        'sa_secondary_no': '4444', 'sa_district': 'حي الورود',
        'sa_city_id': c_riyadh.id, 'sa_postal_code': '12271',
    })
    client_royal = partner({
        'name': 'الهيئة الملكية للجبيل وينبع', 'is_company': True,
        'commercial_registration': '2050987655',
        'mobile_sa': '0502223344',
        'sa_building_no': '2222', 'sa_street_name': 'شارع المدينة الصناعية',
        'sa_secondary_no': '3333', 'sa_district': 'حي الجبيل',
        'sa_city_id': c_jubail.id, 'sa_postal_code': '35718',
    })
    client_aramco = partner({
        'name': 'شركة أرامكو السعودية للعقارات', 'is_company': True,
        'commercial_registration': '2080123457',
        'mobile_sa': '0501112233',
        'sa_building_no': '1111', 'sa_street_name': 'طريق الملك',
        'sa_secondary_no': '2222', 'sa_district': 'حي الدهران',
        'sa_city_id': c_dammam.id, 'sa_postal_code': '31311',
    })
    p('  8 partners ready')

    # ── Projects ──────────────────────────────────────────────────────────
    p('[3/8] Creating projects...')
    P = env['construction.project']

    proj1 = P.create({
        'name': 'مشروع أبراج الريان السكنية - الرياض',
        'project_type': 'residential', 'partner_id': client_amanah.id,
        'date_start': '2024-01-15', 'date_end': '2026-03-31',
        'contract_value': 42_000_000.0, 'budget_estimated': 39_500_000.0,
        'building_permit': 'BP-RYD-2024-0234', 'permit_expiry': '2026-12-31',
        'municipality_ref': 'MUN-2024-RYD-1122',
        'region_id': r_riyadh.id if r_riyadh else False, 'city_id': c_riyadh.id,
        'site_building_no': '1200', 'site_street': 'طريق الملك سلمان',
        'site_secondary_no': '3400', 'site_district': 'حي الياسمين',
        'site_postal_code': '13326',
    })
    proj1.action_activate()

    proj2 = P.create({
        'name': 'مشروع مركز جدة للأعمال التجاري',
        'project_type': 'commercial', 'partner_id': client_royal.id,
        'date_start': '2023-09-01', 'date_end': '2026-08-31',
        'contract_value': 105_000_000.0, 'budget_estimated': 98_000_000.0,
        'building_permit': 'JP-JED-2023-0567', 'permit_expiry': '2027-06-30',
        'municipality_ref': 'MUN-2023-JED-4455',
        'region_id': r_western.id if r_western else False, 'city_id': c_jeddah.id,
        'site_building_no': '5600', 'site_street': 'شارع الأمير محمد بن عبدالعزيز',
        'site_secondary_no': '7800', 'site_district': 'حي البلد',
        'site_postal_code': '21441',
    })
    proj2.action_activate()

    proj3 = P.create({
        'name': 'مشروع البنية التحتية والمرافق - الجبيل',
        'project_type': 'infra', 'partner_id': client_aramco.id,
        'date_start': '2024-06-01', 'date_end': '2027-05-31',
        'contract_value': 78_000_000.0, 'budget_estimated': 73_000_000.0,
        'building_permit': 'IP-JUB-2024-0891', 'permit_expiry': '2027-12-31',
        'municipality_ref': 'MUN-2024-JUB-7788',
        'region_id': r_eastern.id if r_eastern else False, 'city_id': c_jubail.id,
        'site_building_no': '8900', 'site_street': 'شارع المدينة الصناعية الثانية',
        'site_secondary_no': '1100', 'site_district': 'حي الصناعية',
        'site_postal_code': '35718',
    })
    proj3.action_activate()

    proj4 = P.create({
        'name': 'مشروع توسعة طريق الملك عبدالله - الدمام',
        'project_type': 'roads', 'partner_id': client_aramco.id,
        'date_start': '2025-03-01', 'date_end': '2027-02-28',
        'contract_value': 55_000_000.0, 'budget_estimated': 52_000_000.0,
        'building_permit': 'RP-DMM-2025-0112', 'permit_expiry': '2027-06-30',
        'municipality_ref': 'MUN-2025-DMM-3344',
        'region_id': r_eastern.id if r_eastern else False, 'city_id': c_dammam.id,
        'site_building_no': '2300', 'site_street': 'طريق الملك عبدالله',
        'site_secondary_no': '4500', 'site_district': 'حي الفيصلية',
        'site_postal_code': '32233',
    })
    proj4.action_activate()

    proj5 = P.create({
        'name': 'مشروع المجمع الصناعي الخفيف - الرياض',
        'project_type': 'industrial', 'partner_id': client_royal.id,
        'date_start': '2022-03-01', 'date_end': '2024-08-31',
        'contract_value': 31_000_000.0, 'budget_estimated': 29_500_000.0,
        'building_permit': 'IP-RYD-2022-0334', 'permit_expiry': '2025-12-31',
        'municipality_ref': 'MUN-2022-RYD-9900',
        'region_id': r_riyadh.id if r_riyadh else False, 'city_id': c_riyadh.id,
        'site_building_no': '6700', 'site_street': 'طريق الدمام',
        'site_secondary_no': '8900', 'site_district': 'حي الصناعية',
        'site_postal_code': '11432',
    })
    proj5.action_activate()
    p('  5 projects created')

    # ── UOMs ──────────────────────────────────────────────────────────────
    UOM = env['uom.uom']
    def find_uom(*names):
        for n in names:
            u = UOM.search([('name', 'ilike', n)], limit=1)
            if u: return u
        return UOM.search([], limit=1)

    uom_m3   = find_uom('m³', 'm3', 'cubic meter', 'Cubic')
    uom_m2   = find_uom('m²', 'm2', 'square meter', 'Square')
    uom_m    = find_uom('meter', 'Meter', 'metres')
    uom_unit = find_uom('Unit', 'Units', 'unit(s)')
    uom_ton  = find_uom('Tonne', 'ton', 'Metric Ton')

    def u(uom): return uom.id if uom else False

    # ── BOQs ──────────────────────────────────────────────────────────────
    p('[4/8] Creating BOQs...')
    BOQ = env['construction.boq']
    BL  = env['construction.boq.line']

    def boq_line(boq_id, code, desc, itype, uom, qty, price):
        return BL.create({
            'boq_id': boq_id, 'item_code': code, 'description': desc,
            'description_ar': desc, 'item_type': itype,
            'uom_id': u(uom), 'qty_estimated': qty, 'unit_price': price,
        })

    # BOQ 1 — Residential Riyadh (42 M)
    b1 = BOQ.create({'name': 'جدول كميات أبراج الريان', 'project_id': proj1.id, 'date': '2024-01-20'})
    bl1 = [
        boq_line(b1.id, 'A-001', 'أعمال الحفر والردم',            'labor',       uom_m3,   8500,  42.0),
        boq_line(b1.id, 'A-002', 'أعمال الأساسات الخرسانية',      'material',    uom_m3,   2200, 720.0),
        boq_line(b1.id, 'A-003', 'الهيكل الخرساني المسلح',        'material',    uom_m3,   6800, 950.0),
        boq_line(b1.id, 'B-001', 'أعمال البناء والطابوق',          'material',    uom_m2,  18500, 135.0),
        boq_line(b1.id, 'B-002', 'العزل الحراري والمائي',          'material',    uom_m2,  12000,  85.0),
        boq_line(b1.id, 'C-001', 'أعمال السباكة والصرف الصحي',    'subcontract', uom_unit,  120,32000.0),
        boq_line(b1.id, 'C-002', 'أعمال الكهرباء والإنارة',        'subcontract', uom_unit,  120,26000.0),
        boq_line(b1.id, 'C-003', 'أعمال التكييف والتهوية',         'subcontract', uom_unit,   60,18500.0),
        boq_line(b1.id, 'D-001', 'التشطيبات الداخلية',             'material',    uom_m2,  24000, 185.0),
        boq_line(b1.id, 'D-002', 'الواجهات والزجاج',               'material',    uom_m2,   6500, 420.0),
        boq_line(b1.id, 'E-001', 'الطرق الداخلية والأرصفة',       'material',    uom_m2,   4800, 145.0),
        boq_line(b1.id, 'E-002', 'التشجير والتنسيق',               'overhead',    uom_m2,   3200, 110.0),
    ]
    b1.action_confirm()

    # BOQ 2 — Commercial Jeddah (105 M)
    b2 = BOQ.create({'name': 'جدول كميات مركز جدة للأعمال', 'project_id': proj2.id, 'date': '2023-09-10'})
    bl2 = [
        boq_line(b2.id, 'A-001', 'أعمال الحفر وأعمال الدعم',        'labor',       uom_m3,  25000,   55.0),
        boq_line(b2.id, 'A-002', 'الأساسات الخازوقية الخرسانية',    'material',    uom_m3,   8500,  800.0),
        boq_line(b2.id, 'A-003', 'الهيكل الخرساني للأبراج',          'material',    uom_m3,  32000,  850.0),
        boq_line(b2.id, 'B-001', 'الواجهات الزجاجية كيرتين وول',    'material',    uom_m2,  22000, 1200.0),
        boq_line(b2.id, 'C-001', 'المنظومة الكهربائية الكاملة',      'subcontract', uom_unit,    1,18500000.0),
        boq_line(b2.id, 'C-002', 'منظومة التكييف المركزي',           'subcontract', uom_unit,    1,14200000.0),
        boq_line(b2.id, 'C-003', 'المصاعد والسلالم المتحركة',        'subcontract', uom_unit,   24, 280000.0),
        boq_line(b2.id, 'D-001', 'التشطيبات التجارية الفاخرة',       'material',    uom_m2,  35000,  380.0),
        boq_line(b2.id, 'E-001', 'مواقف متعددة الطوابق',             'material',    uom_m3,  15000,  350.0),
        boq_line(b2.id, 'F-001', 'الإشراف والإدارة',                  'overhead',    uom_unit,    1, 2200000.0),
    ]
    b2.action_confirm()

    # BOQ 3 — Infrastructure Jubail (78 M)
    b3 = BOQ.create({'name': 'جدول كميات البنية التحتية - الجبيل', 'project_id': proj3.id, 'date': '2024-06-10'})
    bl3 = [
        boq_line(b3.id, 'A-001', 'أعمال الترابة والحفر والدعم',     'labor',       uom_m3,  45000,  38.0),
        boq_line(b3.id, 'B-001', 'شبكات المياه الرئيسية',           'material',    uom_m,   12000, 850.0),
        boq_line(b3.id, 'B-002', 'شبكات الصرف الصحي',               'material',    uom_m,    8500,1200.0),
        boq_line(b3.id, 'B-003', 'شبكات الكهرباء الأرضية',          'material',    uom_m,   15000, 450.0),
        boq_line(b3.id, 'C-001', 'محطة ضخ المياه',                   'subcontract', uom_unit,    2, 8500000.0),
        boq_line(b3.id, 'C-002', 'محطة معالجة الصرف',                'subcontract', uom_unit,    1,12000000.0),
        boq_line(b3.id, 'D-001', 'رصف الطرق الداخلية',               'material',    uom_m2,  35000, 185.0),
        boq_line(b3.id, 'E-001', 'الإضاءة العامة والمنظومة الأمنية', 'overhead',    uom_unit,    1, 4200000.0),
    ]
    b3.action_confirm()

    # BOQ 4 — Roads Dammam (55 M)
    b4 = BOQ.create({'name': 'جدول كميات مشروع الطريق - الدمام', 'project_id': proj4.id, 'date': '2025-03-05'})
    bl4 = [
        boq_line(b4.id, 'A-001', 'أعمال الترابة والتسوية',          'labor',       uom_m3, 120000,  28.0),
        boq_line(b4.id, 'B-001', 'طبقة الأساس من المواد الحجرية',   'material',    uom_m3,  35000, 180.0),
        boq_line(b4.id, 'B-002', 'طبقة الإسفلت السطحية',            'material',    uom_m2, 180000,  95.0),
        boq_line(b4.id, 'C-001', 'الجسور والتقاطعات',                'subcontract', uom_unit,    4, 5500000.0),
        boq_line(b4.id, 'D-001', 'الإنارة والإشارات المرورية',       'subcontract', uom_unit,    1, 8200000.0),
        boq_line(b4.id, 'E-001', 'الأسوار والمواقف والخدمات',        'overhead',    uom_unit,    1, 3500000.0),
    ]
    b4.action_confirm()

    # BOQ 5 — Industrial Riyadh (31 M) — completed project
    b5 = BOQ.create({'name': 'جدول كميات المجمع الصناعي - الرياض', 'project_id': proj5.id, 'date': '2022-03-10'})
    bl5 = [
        boq_line(b5.id, 'A-001', 'أعمال ترابة وأساسات صناعية',       'labor',       uom_m3,  18000,   65.0),
        boq_line(b5.id, 'A-002', 'الهياكل الصلبة الصناعية',           'material',    uom_ton,   850,18500.0),
        boq_line(b5.id, 'B-001', 'الأبنية الصناعية الجاهزة',          'material',    uom_m2,  12000,  650.0),
        boq_line(b5.id, 'C-001', 'المنظومة الكهربائية الصناعية',       'subcontract', uom_unit,    1, 3500000.0),
        boq_line(b5.id, 'C-002', 'شبكات المياه والصرف الصناعي',       'subcontract', uom_unit,    1, 2200000.0),
        boq_line(b5.id, 'C-003', 'منظومة الإطفاء والسلامة',           'subcontract', uom_unit,    1, 1800000.0),
        boq_line(b5.id, 'D-001', 'تشطيبات الأرضيات الصناعية',         'material',    uom_m2,  10000,  280.0),
        boq_line(b5.id, 'E-001', 'أعمال الخارجية والمداخل',           'overhead',    uom_unit,    1, 2100000.0),
    ]
    b5.action_confirm()
    p('  5 BOQs confirmed')

    # ── Contracts + Payment Schedules ─────────────────────────────────────
    p('[5/8] Creating contracts and payment schedules...')
    C  = env['construction.contract']
    PL = env['construction.payment.line']

    def pay(contract_id, name, ptype, amount, due_date):
        return PL.create({'contract_id': contract_id, 'name': name,
                          'payment_type': ptype, 'amount': amount, 'due_date': due_date})

    def mark_paid(pl, paid_date):
        pl.action_mark_due(); pl.action_mark_paid()
        pl.write({'paid_date': paid_date})

    # Contract 1 — Riyadh Residential
    c1 = C.create({
        'name': 'عقد إنشاء أبراج الريان السكنية',
        'contract_type': 'main', 'project_id': proj1.id,
        'partner_id': cont_general.id, 'boq_id': b1.id,
        'date_signed': '2024-01-25', 'date_start': '2024-02-01', 'date_end': '2026-03-31',
        'contract_value': 42_000_000.0, 'retention_percent': 5.0, 'advance_percent': 10.0,
        'scope_of_work': '<p>إنشاء مجمع سكني متكامل 120 وحدة سكنية بجميع الأعمال الإنشائية والكهرومكانيكية والتشطيبات.</p>',
    })
    p10 = pay(c1.id, 'دفعة مقدمة 10%',                   'advance',   4_200_000, '2024-02-10')
    p11 = pay(c1.id, 'مرحلة أولى - الأساسات',             'milestone', 8_400_000, '2024-08-31')
    p12 = pay(c1.id, 'مرحلة ثانية - الهيكل الإنشائي',    'milestone',10_500_000, '2025-03-31')
    p13 = pay(c1.id, 'مرحلة ثالثة - الكهروميكانيكا',     'milestone',10_500_000, '2025-10-31')
    p14 = pay(c1.id, 'مرحلة رابعة - التسليم المبدئي',    'milestone', 6_300_000, '2026-03-31')
    p15 = pay(c1.id, 'الدفعة الختامية - تحرير الضمان',   'retention', 2_100_000, '2027-03-31')
    mark_paid(p10, '2024-02-15')
    c1.action_activate()

    # Contract 2 — Jeddah Commercial
    c2 = C.create({
        'name': 'عقد إنشاء مركز جدة للأعمال',
        'contract_type': 'main', 'project_id': proj2.id,
        'partner_id': cont_civil.id, 'boq_id': b2.id,
        'date_signed': '2023-09-05', 'date_start': '2023-09-15', 'date_end': '2026-08-31',
        'contract_value': 105_000_000.0, 'retention_percent': 5.0, 'advance_percent': 10.0,
        'scope_of_work': '<p>إنشاء برج تجاري 45 طابقاً بمساحة 45,000 م² يشمل مكاتب ومحلات وفندق بوتيك.</p>',
    })
    p20 = pay(c2.id, 'دفعة مقدمة 10%',                     'advance',  10_500_000, '2023-10-01')
    p21 = pay(c2.id, 'مرحلة أولى - الأعمال تحت الأرض',    'milestone',15_750_000, '2024-06-30')
    p22 = pay(c2.id, 'مرحلة ثانية - هيكل الأبراج',        'milestone',26_250_000, '2025-06-30')
    p23 = pay(c2.id, 'مرحلة ثالثة - الواجهات والميكانيكا','milestone',26_250_000, '2026-01-31')
    p24 = pay(c2.id, 'مرحلة رابعة - التشطيبات والتسليم',  'milestone',21_000_000, '2026-08-31')
    p25 = pay(c2.id, 'تحرير ضمان حسن الأداء',              'retention', 5_250_000, '2027-08-31')
    mark_paid(p20, '2023-10-08')
    mark_paid(p21, '2024-07-12')
    c2.action_activate()

    # Contract 3 — Infrastructure Jubail
    c3 = C.create({
        'name': 'عقد البنية التحتية - الجبيل الصناعية',
        'contract_type': 'main', 'project_id': proj3.id,
        'partner_id': cont_roads.id, 'boq_id': b3.id,
        'date_signed': '2024-06-15', 'date_start': '2024-07-01', 'date_end': '2027-05-31',
        'contract_value': 78_000_000.0, 'retention_percent': 5.0, 'advance_percent': 15.0,
        'scope_of_work': '<p>تنفيذ شبكات البنية التحتية الكاملة لمنطقة صناعية تشمل المياه والصرف والكهرباء والطرق.</p>',
    })
    p30 = pay(c3.id, 'دفعة مقدمة 15%',                    'advance',  11_700_000, '2024-07-15')
    p31 = pay(c3.id, 'مرحلة أولى - أعمال الترابة',        'milestone',15_600_000, '2025-01-31')
    p32 = pay(c3.id, 'مرحلة ثانية - الشبكات الرئيسية',   'milestone',19_500_000, '2025-09-30')
    p33 = pay(c3.id, 'مرحلة ثالثة - المحطات والمنشآت',   'milestone',19_500_000, '2026-06-30')
    p34 = pay(c3.id, 'مرحلة رابعة - الطرق والتشطيبات',   'milestone', 7_800_000, '2027-05-31')
    p35 = pay(c3.id, 'الضمان - بعد فترة الصيانة',         'retention', 3_900_000, '2028-05-31')
    mark_paid(p30, '2024-07-20')
    c3.action_activate()

    # Contract 4 — Roads Dammam
    c4 = C.create({
        'name': 'عقد توسعة طريق الملك عبدالله - الدمام',
        'contract_type': 'main', 'project_id': proj4.id,
        'partner_id': cont_roads.id, 'boq_id': b4.id,
        'date_signed': '2025-03-10', 'date_start': '2025-04-01', 'date_end': '2027-02-28',
        'contract_value': 55_000_000.0, 'retention_percent': 5.0, 'advance_percent': 10.0,
    })
    p40 = pay(c4.id, 'دفعة مقدمة 10%',              'advance',   5_500_000, '2025-04-15')
    p41 = pay(c4.id, 'مرحلة أولى - أعمال الترابة', 'milestone',11_000_000, '2025-11-30')
    p42 = pay(c4.id, 'مرحلة ثانية - الأساس والإسفلت','milestone',16_500_000,'2026-07-31')
    p43 = pay(c4.id, 'مرحلة ثالثة - الجسور والإنارة','milestone',16_500_000,'2027-02-28')
    p44 = pay(c4.id, 'المستخلص الختامي',             'final',     2_750_000, '2027-02-28')
    p45 = pay(c4.id, 'تحرير ضمان الصيانة',          'retention', 2_750_000, '2028-02-28')
    mark_paid(p40, '2025-04-20')
    c4.action_activate()

    # Contract 5 — Industrial Riyadh (completed)
    c5 = C.create({
        'name': 'عقد المجمع الصناعي الخفيف - الرياض',
        'contract_type': 'main', 'project_id': proj5.id,
        'partner_id': cont_general.id, 'boq_id': b5.id,
        'date_signed': '2022-03-15', 'date_start': '2022-04-01',
        'date_end': '2024-08-31', 'date_actual_end': '2024-09-15',
        'contract_value': 31_000_000.0, 'retention_percent': 5.0, 'advance_percent': 10.0,
    })
    p50 = pay(c5.id, 'دفعة مقدمة',        'advance',   3_100_000, '2022-04-15')
    p51 = pay(c5.id, 'مرحلة أولى',        'milestone', 7_750_000, '2023-02-28')
    p52 = pay(c5.id, 'مرحلة ثانية',       'milestone', 7_750_000, '2023-10-31')
    p53 = pay(c5.id, 'مرحلة ثالثة',       'milestone', 7_750_000, '2024-05-31')
    p54 = pay(c5.id, 'المستخلص الختامي',  'final',     3_100_000, '2024-09-15')
    p55 = pay(c5.id, 'تحرير الضمان',      'retention', 1_550_000, '2025-09-15')
    for pl, pd in [(p50,'2022-04-18'),(p51,'2023-03-05'),(p52,'2023-11-10'),
                   (p53,'2024-06-08'),(p54,'2024-09-20'),(p55,'2025-09-18')]:
        mark_paid(pl, pd)
    c5.action_activate()
    c5.action_complete()
    proj5.action_done()
    p('  5 contracts + payment schedules created')

    # ── Subcontracts ──────────────────────────────────────────────────────
    p('[6/8] Creating subcontracts...')
    SC = env['construction.subcontract']

    def sub(contract, name, partner_id, start, end, value, scope=''):
        s = SC.create({
            'name': name, 'contract_id': contract.id, 'partner_id': partner_id,
            'date_start': start, 'date_end': end,
            'subcontract_value': value, 'retention_percent': 5.0,
            'scope_description': f'<p>{scope}</p>' if scope else False,
        })
        s.action_activate()
        return s

    sub(c1, 'باطن - سباكة وصرف صحي - أبراج الريان',   cont_mep.id,      '2024-06-01','2025-09-30', 3_840_000, 'تنفيذ جميع أعمال السباكة والصرف لـ 120 وحدة')
    sub(c1, 'باطن - تكييف وتهوية - أبراج الريان',      cont_mep.id,      '2024-09-01','2025-11-30', 2_220_000, 'منظومة التكييف المركزي')
    sub(c1, 'باطن - تشطيبات داخلية - أبراج الريان',    cont_finishing.id,'2025-03-01','2026-02-28', 4_440_000, 'كافة أعمال التشطيبات الداخلية والواجهات')
    sub(c2, 'باطن - المنظومة الكهربائية - مركز جدة',   cont_mep.id,      '2024-03-01','2026-02-28',18_500_000)
    sub(c2, 'باطن - التكييف المركزي - مركز جدة',       cont_mep.id,      '2024-06-01','2026-05-31',14_200_000)
    sub(c3, 'باطن - محطات المياه والصرف - الجبيل',     cont_mep.id,      '2025-01-01','2026-06-30',20_500_000)
    s5 = sub(c5, 'باطن - المنظومة الكهربائية الصناعية', cont_mep.id,     '2022-07-01','2024-02-28', 3_500_000)
    s5.action_complete()
    p('  7 subcontracts created')

    # ── Certificates ──────────────────────────────────────────────────────
    p('[7/8] Creating certificates...')
    Cert  = env['construction.certificate']
    CLine = env['construction.certificate.line']
    admin = env['res.users'].browse(2)

    def cert_line(cert_id, bl, code, desc, itype, uom, qty_boq, qty_prev, qty_this, price):
        return CLine.create({
            'certificate_id': cert_id, 'boq_line_id': bl.id,
            'item_code': code, 'description': desc, 'item_type': itype,
            'uom_id': u(uom), 'qty_boq': qty_boq,
            'qty_previous': qty_prev, 'qty_this': qty_this, 'unit_price': price,
        })

    def submit_approve_pay(cert, approved_date, paid_date=None):
        cert.action_submit_review()
        cert.write({'reviewed_by': admin.id})
        cert.action_approve()
        cert.write({'approved_by': admin.id, 'date_approved': approved_date})
        if paid_date:
            cert.action_mark_paid()
            cert.write({'date_paid': paid_date})

    # ── Project 1 — 3 certs (paid, paid, approved) ──────────────────────
    ct1_1 = Cert.create({
        'name': 'مستخلص 001 - أعمال الحفر والأساسات',
        'certificate_number': 1, 'project_id': proj1.id, 'contract_id': c1.id,
        'payment_line_id': p11.id,
        'date_from': '2024-02-01', 'date_to': '2024-07-31', 'date_submitted': '2024-08-05',
        'retention_percent': 5.0, 'advance_deduction': 1_680_000.0, 'vat_rate': 15.0,
    })
    cert_line(ct1_1.id, bl1[0],'A-001','أعمال الحفر والردم',         'labor',       uom_m3,   8500,    0, 8500,  42.0)
    cert_line(ct1_1.id, bl1[1],'A-002','أعمال الأساسات الخرسانية',   'material',    uom_m3,   2200,    0, 2200, 720.0)
    submit_approve_pay(ct1_1, '2024-08-20', '2024-09-10')

    ct1_2 = Cert.create({
        'name': 'مستخلص 002 - الهيكل الإنشائي',
        'certificate_number': 2, 'project_id': proj1.id, 'contract_id': c1.id,
        'payment_line_id': p12.id,
        'date_from': '2024-08-01', 'date_to': '2025-02-28', 'date_submitted': '2025-03-05',
        'retention_percent': 5.0, 'advance_deduction': 2_100_000.0, 'vat_rate': 15.0,
    })
    cert_line(ct1_2.id, bl1[2],'A-003','الهيكل الخرساني المسلح',     'material', uom_m3, 6800,    0, 4500, 950.0)
    cert_line(ct1_2.id, bl1[3],'B-001','أعمال البناء والطابوق',       'material', uom_m2,18500,    0,12000, 135.0)
    submit_approve_pay(ct1_2, '2025-03-20', '2025-04-05')

    ct1_3 = Cert.create({
        'name': 'مستخلص 003 - البناء والكهروميكانيكا',
        'certificate_number': 3, 'project_id': proj1.id, 'contract_id': c1.id,
        'payment_line_id': p13.id,
        'date_from': '2025-03-01', 'date_to': '2025-09-30', 'date_submitted': '2025-10-08',
        'retention_percent': 5.0, 'advance_deduction': 2_100_000.0, 'vat_rate': 15.0,
    })
    cert_line(ct1_3.id, bl1[2],'A-003','الهيكل الخرساني (المتبقي)',  'material',    uom_m3,  6800, 4500, 2300, 950.0)
    cert_line(ct1_3.id, bl1[3],'B-001','البناء والطابوق (المتبقي)',   'material',    uom_m2, 18500,12000, 5500, 135.0)
    cert_line(ct1_3.id, bl1[5],'C-001','أعمال السباكة والصرف',        'subcontract', uom_unit,  120,    0,   80,32000.0)
    cert_line(ct1_3.id, bl1[6],'C-002','أعمال الكهرباء والإنارة',     'subcontract', uom_unit,  120,    0,   80,26000.0)
    submit_approve_pay(ct1_3, '2025-10-20')   # approved only, not paid

    # ── Project 2 — 2 certs (paid, review) ──────────────────────────────
    ct2_1 = Cert.create({
        'name': 'مستخلص 001 - الأعمال تحت الأرض والأساسات',
        'certificate_number': 1, 'project_id': proj2.id, 'contract_id': c2.id,
        'payment_line_id': p21.id,
        'date_from': '2023-09-15', 'date_to': '2024-06-30', 'date_submitted': '2024-07-05',
        'retention_percent': 5.0, 'advance_deduction': 3_150_000.0, 'vat_rate': 15.0,
    })
    cert_line(ct2_1.id, bl2[0],'A-001','أعمال الحفر وأعمال الدعم',       'labor',    uom_m3, 25000,    0,25000,   55.0)
    cert_line(ct2_1.id, bl2[1],'A-002','الأساسات الخازوقية الخرسانية',   'material', uom_m3,  8500,    0, 8500,  800.0)
    submit_approve_pay(ct2_1, '2024-07-18', '2024-07-25')

    ct2_2 = Cert.create({
        'name': 'مستخلص 002 - هيكل الأبراج (المرحلة الأولى)',
        'certificate_number': 2, 'project_id': proj2.id, 'contract_id': c2.id,
        'payment_line_id': p22.id,
        'date_from': '2024-07-01', 'date_to': '2025-03-31', 'date_submitted': '2025-04-05',
        'retention_percent': 5.0, 'advance_deduction': 5_250_000.0, 'vat_rate': 15.0,
    })
    cert_line(ct2_2.id, bl2[2],'A-003','الهيكل الخرساني للأبراج',   'material', uom_m3, 32000, 0, 18000, 850.0)
    cert_line(ct2_2.id, bl2[3],'B-001','الواجهات الزجاجية',          'material', uom_m2, 22000, 0,  8000,1200.0)
    ct2_2.action_submit_review()  # leave in review

    # ── Project 3 — 1 cert (approved) ────────────────────────────────────
    ct3_1 = Cert.create({
        'name': 'مستخلص 001 - أعمال الترابة والشبكات',
        'certificate_number': 1, 'project_id': proj3.id, 'contract_id': c3.id,
        'payment_line_id': p31.id,
        'date_from': '2024-07-01', 'date_to': '2025-01-31', 'date_submitted': '2025-02-05',
        'retention_percent': 5.0, 'advance_deduction': 3_900_000.0, 'vat_rate': 15.0,
    })
    cert_line(ct3_1.id, bl3[0],'A-001','أعمال الترابة والحفر',       'labor',    uom_m3, 45000,    0,45000,  38.0)
    cert_line(ct3_1.id, bl3[1],'B-001','شبكات المياه الرئيسية (1/2)','material', uom_m,  12000,    0, 6000, 850.0)
    submit_approve_pay(ct3_1, '2025-02-20')  # approved only

    # ── Project 5 — 2 certs (both paid, project done) ────────────────────
    ct5_1 = Cert.create({
        'name': 'مستخلص 001 - الهياكل الصناعية والأساسات',
        'certificate_number': 1, 'project_id': proj5.id, 'contract_id': c5.id,
        'payment_line_id': p51.id,
        'date_from': '2022-04-01', 'date_to': '2023-01-31', 'date_submitted': '2023-02-05',
        'retention_percent': 5.0, 'advance_deduction': 1_550_000.0, 'vat_rate': 15.0,
    })
    cert_line(ct5_1.id, bl5[0],'A-001','أعمال ترابة وأساسات صناعية', 'labor',    uom_m3,  18000,    0,18000,   65.0)
    cert_line(ct5_1.id, bl5[1],'A-002','الهياكل الصلبة الصناعية',     'material', uom_ton,   850,    0,  850,18500.0)
    submit_approve_pay(ct5_1, '2023-02-20', '2023-03-05')

    ct5_2 = Cert.create({
        'name': 'مستخلص 002 - الأبنية والتشطيبات النهائية',
        'certificate_number': 2, 'project_id': proj5.id, 'contract_id': c5.id,
        'payment_line_id': p53.id,
        'date_from': '2023-02-01', 'date_to': '2024-07-31', 'date_submitted': '2024-08-10',
        'retention_percent': 5.0, 'advance_deduction': 1_550_000.0, 'vat_rate': 15.0,
    })
    cert_line(ct5_2.id, bl5[2],'B-001','الأبنية الصناعية الجاهزة',    'material', uom_m2, 12000, 0, 12000, 650.0)
    cert_line(ct5_2.id, bl5[6],'D-001','تشطيبات الأرضيات الصناعية',   'material', uom_m2, 10000, 0, 10000, 280.0)
    submit_approve_pay(ct5_2, '2024-08-25', '2024-09-20')

    p('  8 certificates created and progressed')

    # ── Summary ───────────────────────────────────────────────────────────
    p('\n[8/8] Summary')
    p('=' * 65)
    for proj, cont in [(proj1,c1),(proj2,c2),(proj3,c3),(proj4,c4),(proj5,c5)]:
        proj.invalidate_recordset(); cont.invalidate_recordset()
        certs = Cert.search([('project_id', '=', proj.id)])
        cert_states = dict(draft=0, review=0, approved=0, paid=0)
        for c in certs: cert_states[c.state] = cert_states.get(c.state,0) + 1
        state_str = '  '.join(f"{s}:{n}" for s,n in cert_states.items() if n)
        p(f"\n  {proj.name}")
        p(f"    State: {proj.state:<10} | Contract: {cont.contract_value:>15,.0f} SAR")
        p(f"    Paid:  {cont.total_paid:>15,.0f} SAR | Progress: {proj.progress_percent:.1f}%")
        p(f"    Certs: {state_str}")

    # ── Admin group ───────────────────────────────────────────────────────
    p('\n[+] Assigning admin to Construction Manager group...')
    group = env.ref('construction_management.group_construction_manager')
    env['res.users'].browse(2).write({'groups_id': [(4, group.id)]})
    p('  Done')

    # ── Hide Discuss from home screen ─────────────────────────────────────
    p('[+] Hiding Discuss from home screen...')
    discuss_menu = (env.ref('mail.mail_menu_root', raise_if_not_found=False)
                    or env['ir.ui.menu'].search(
                        [('web_icon', 'ilike', 'mail'), ('parent_id', '=', False)], limit=1))
    if discuss_menu:
        discuss_menu.write({'active': False})
        p('  Done')
    else:
        p('  Discuss menu not found — skipped')

if __name__ == '__main__':
    main()
