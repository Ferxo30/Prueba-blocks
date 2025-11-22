# -*- coding: utf-8 -*-
{
    "name": "POS Order Manual Payment (Cuenta cliente)",
    "version": "18.0.2.0.0",
    "summary": "Registrar pagos manuales en órdenes POS sin afectar la contabilidad.",
    "category": "Point of Sale",
    "author": "Custom",
    "depends": ["point_of_sale"],
    "data": [
        "security/ir.model.access.csv",
        "data/pos_order_payment_sequence.xml", 
        "wizard/pos_order_payment_wizard_views.xml",
        "views/pos_order_views.xml",
        'views/pos_payment_method_views.xml', 
        'report/pos_manual_payment_report.xml', 
        'wizard/pos_order_statement_wizard_views.xml',
        'report/pos_order_statement_report.xml',
        #'report/pos_order_statement_templates.xml'
        'wizard/pos_order_invoice_statement_wizard_views.xml',
        'report/pos_order_invoice_statement_report.xml',
    ],
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}
