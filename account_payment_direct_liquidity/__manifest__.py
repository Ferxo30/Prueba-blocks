# -*- coding: utf-8 -*-
{
    "name": "Account Payment Direct Liquidity",
    "summary": "Postea pagos directamente a la cuenta de banco/caja del diario, evitando 'Pagos pendientes'",
    "version": "18.0.1.0.1",
    "author": "Velfasa / Estuardo & ChatGPT",
    "license": "LGPL-3",
    "category": "Accounting",
    "depends": ["account"],  # <-- simple y seguro
    "data": [
        "views/account_journal_views.xml",
    ],
    "installable": True,
    "application": False,
}
