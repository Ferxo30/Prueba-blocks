# -*- coding: utf-8 -*-
{
    "name": "Stock Warehouse Inventory Report (PDF/XLSX)",
    "version": "18.0.1.0.0",
    "category": "Inventory",
    "summary": "Imprime existencias por bodega a una fecha (PDF y Excel) desde Reportes > Existencias",
    "depends": ["stock", "product"],
    "data": [
        "security/ir.model.access.csv",
        "views/warehouse_inventory_report_views.xml",
        "report/warehouse_inventory_report_templates.xml",
    ],
    "installable": True,
    "application": False,
}
