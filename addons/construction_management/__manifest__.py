{
    'name': 'Construction Management | إدارة المقاولات',
    'version': '17.0.1.0.0',
    'category': 'Industries',
    'summary': 'نظام إدارة مشاريع المقاولات للسوق السعودي',
    'description': """
Construction Management System for the Saudi Arabian market.

نظام متكامل لإدارة مشاريع المقاولات في السوق السعودي.

Features:

- Project management with Saudi national address
- Bill of Quantities (BOQ) with Excel import
- Main contracts + subcontracts + payment schedule
- Progress certificates with 4-stage approval workflow
- ZATCA Phase 1 QR code on certificates
- Full Arabic RTL PDF reports
""",
    'author': 'Abdelrehman Elhaj',
    'website': 'https://github.com/AbdelrehmanElhaj',
    'license': 'LGPL-3',
    'depends': ['base', 'mail', 'uom', 'web'],
    'demo': [
        'demo/demo_data.xml',
    ],
    'data': [
        'security/construction_security.xml',
        'security/ir.model.access.csv',
        'data/saudi_cities.xml',
        'data/construction_sequences.xml',
        'data/expiry_cron.xml',
        'views/saudi_address_views.xml',
        'views/res_partner_views.xml',
        'views/construction_project_views.xml',
        'views/construction_boq_views.xml',
        'views/boq_import_wizard_views.xml',
        'views/construction_contract_views.xml',
        'views/construction_certificate_views.xml',
        'views/construction_dashboard_views.xml',
        'views/menus.xml',
        'views/login_template.xml',
        'reports/report_certificate.xml',
        'reports/report_boq.xml',
        'reports/report_contract.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'construction_management/static/src/css/login.css',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'sequence': 1,
    'images': ['static/description/icon.png'],
}
