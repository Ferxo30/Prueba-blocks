{
    "name": "POS Partner Code & POS Sequence (correlativo en recibo y factura)",
    "summary": "Añade correlativo interno POS al recibo POS y lo copia a la factura (campo buscable).",
    "version": "18.0.0.6",
    "author": "Tu equipo",
    "license": "LGPL-3",
    "depends": ["point_of_sale", "account"],
    "data": [
        "views/account_move_views.xml"
    ],
   'assets': {
    'point_of_sale.assets': [
        # solo JS del POS, si existe
        'pos_partner_code_and_pos_seq_fixed_v6/static/src/js/**/*.js',
    ],
    'web.assets_qweb': [
        # los XML SIEMPRE aquí
        'pos_partner_code_and_pos_seq_fixed_v6/static/src/xml/**/*.xml',
    ],
},

    "installable": True,
    "application": False,
}
