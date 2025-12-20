# -*- coding: utf-8 -*-
{
    "name": "POS Pagos Maestros (Multi-orden)",
    "version": "18.0.1.0.0",
    "summary": "Registrar un pago maestro que aplica a múltiples órdenes POS (sobre pagos manuales existentes).",
    "category": "Point of Sale",
    "author": "Custom",
    "depends": ["point_of_sale", "pos_order_manual_payment"],
    "data": [
        "security/ir.model.access.csv",
        "data/pos_order_payment_master_sequence.xml",
        "views/pos_order_payment_master_views.xml",
        "views/pos_order_payment_views.xml",
        "wizard/pos_order_master_payment_wizard_views.xml",
        "report/pos_order_master_payment_receipt.xml",
        "report/pos_order_master_payment_receipt_template.xml",
    ],
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}
