# -*- encoding: utf-8 -*-

{
    'name': 'FEL Guatemala',
    'version': '18.0.1.0.0',
    'category': 'Custom',
    'description': """ Campos y funciones base para la facturación electrónica en Guatemala """,
    'author': 'aquíH',
    'website': 'http://aquih.com/',
    'depends': ['l10n_gt_extra'],
    'data': [
        'views/account_views.xml',
        'views/res_company_views.xml',
        'views/res_partner_views.xml',
        'views/report_invoice.xml',
    ],
    'demo': [],
    'installable': True,
    'license': 'Other OSI approved licence',
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
