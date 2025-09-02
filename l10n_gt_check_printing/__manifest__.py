{
    "name": "Guatemala - Check Printing",
    "summary": "Custom printable check layouts for Guatemala (Community)",
    "version": "18.0.1.0.0",
    "author": "Estuardo Sandoval & ChatGPT",
    "website": "https://example.com",
    "category": "Accounting/Localizations",
    "license": "LGPL-3",
    "depends": ["account", "account_check_printing"],
    "data": [
        "reports/paperformat.xml",               # Deja el paperformat SOLO aquí
        "reports/report_check_templates.xml",    # Template + acción    
    ],
    "assets": {},
    "installable": True,
    "application": False,
    "auto_install": False
}
