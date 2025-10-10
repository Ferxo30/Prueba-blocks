# -*- coding: utf-8 -*-
{
    'name': 'Partner Supplier Code',
    'summary': "Código interno secuencial para proveedores (PRV-).",
    'version': '18.0.1.0.0',
    'category': 'Contacts',
    'author': 'Blockera Bustamante',
    'license': 'LGPL-3',
    'depends': ['base', 'contacts'],   # nada de POS ni multi
    'data': [
        'data/ir_sequence_data.xml',
        
    ],
    'installable': True,
    'application': False,
}
