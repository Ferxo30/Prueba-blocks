# -*- coding: utf-8 -*-
{
    'name': 'Partner Internal Code',
    'summary': "Agrega campo 'Código interno' a contactos y permite búsqueda por ese código.",
    'version': '18.0.1.0.5',
    'category': 'Contacts',
    'author': 'Blockera Bustamante / ChatGPT',
    'license': 'LGPL-3',
    'website': 'https://example.com',
    'depends': ['base', 'contacts', 'point_of_sale'],   # <-- POS
    'data': ['views/res_partner_views.xml'],
    'assets': {                                         # <-- Assets POS
        'point_of_sale.assets': [
            'partner_internal_code_v4/static/src/js/pos_partner_internal_code.js',
            'partner_internal_code_v4/static/src/xml/pos_partner_internal_code.xml',
        ],
    },
    'installable': True,
    'application': False,
}
