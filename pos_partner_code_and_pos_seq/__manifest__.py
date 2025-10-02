
{
    "name": "Partner Internal Code + POS Internal Sequences",
    "summary": "Código interno en partners (buscable y visible en POS) + correlativos por POS (Serie A/B/C).",
    "version": "18.0.1.0.0",
    "author": "ChatGPT",
    "license": "LGPL-3",
    "depends": ["base", "contacts", "point_of_sale"],
    "data": [
        "views/res_partner_views.xml",
        "views/pos_order_views.xml"
    ],
    "assets": {
        "point_of_sale.assets": [
            "pos_partner_code_and_pos_seq/static/src/js/pos_partner_search_patch.js",
            "pos_partner_code_and_pos_seq/static/src/js/pos_receipt_seq_patch.js",
            "pos_partner_code_and_pos_seq/static/src/xml/pos_receipt_templates.xml"
        ]
    },
    "installable": True,
    "application": False
}
