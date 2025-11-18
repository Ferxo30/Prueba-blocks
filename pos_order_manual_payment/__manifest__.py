# -*- coding: utf-8 -*-
{
    'name': 'POS Order Manual Payment (Cuenta cliente)',
    'version': '18.0.1.0.0',
    'summary': 'Registrar pagos manuales en órdenes POS con Cuenta de cliente sin factura.',
    'category': 'Point of Sale',
    'author': 'Custom',
    'depends': ['point_of_sale'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/pos_order_payment_wizard_views.xml',
        'views/pos_order_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
