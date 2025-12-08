# -*- coding: utf-8 -*-
{
    "name": "Base Accounting Kit - Excel Export",
    "version": "18.0.1.0.0",
    "summary": "Agrega exportación a Excel a los reportes del Base Accounting Kit.",
    "category": "Accounting",
    "author": "Ferxo",
    "license": "LGPL-3",
    "depends": [
        "base_accounting_kit",
    ],
    "data": [
        # Wizards con botón Excel
        "wizard/financial_report_xlsx_views.xml",
        "wizard/cash_flow_report_xlsx_views.xml",
        "wizard/day_bank_cash_book_xlsx_views.xml",
        "wizard/aged_partner_balance_xlsx_views.xml",
        "wizard/partner_ledger_xlsx_views.xml",
        "wizard/general_ledger_xlsx_views.xml",
        "wizard/trial_balance_xlsx_views.xml",
        "wizard/tax_report_xlsx_views.xml",
        "wizard/print_journal_xlsx_views.xml",
        # lo que ya tengas
        "wizard/l10n_gt_extra_xlsx_views.xml",


    ],
    "installable": True,
    "application": False,
}
