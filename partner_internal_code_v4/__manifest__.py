# -*- coding: utf-8 -*-
{
    'name': 'Partner Internal Code',
    'summary': "Código interno secuencial para clientes; búsqueda y asignación masiva.",
    'version': '18.0.2.0.1',
    'category': 'Contacts',
    'author': 'Blockera Bustamante / ChatGPT',
    'license': 'LGPL-3',
    'website': 'https://example.com',
    'depends': ['base', 'contacts', 'point_of_sale'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/internal_code_wizard_views.xml',
        'views/res_partner_views.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'partner_internal_code_v4/static/src/js/pos_partner_internal_code.js',
            'partner_internal_code_v4/static/src/xml/pos_partner_internal_code.xml',
        ],
    },
    'installable': True,
    'application': False,
}
