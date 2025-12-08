# -*- coding: utf-8 -*-
from odoo import models


class ReporteBancoFix(models.AbstractModel):
    _inherit = "report.l10n_gt_extra.reporte_banco"

    def balance_inicial(self, datos):
        """Versión adaptada a Odoo 18 (account.account.company_ids)."""
        cuenta = self.env["account.account"].browse(datos["cuenta_bancaria_id"][0])

        # En Odoo 18 es Many2many company_ids; tomamos una (o la actual)
        company = cuenta.company_ids[:1] or self.env.company

        if not cuenta.currency_id or (cuenta.currency_id.id == company.currency_id.id):
            usar_balance_moneda = False
        else:
            usar_balance_moneda = True

        # Movimientos anteriores a la fecha_desde, en estado 'posted'
        domain = [
            ("account_id", "=", cuenta.id),
            ("date", "<", datos["fecha_desde"]),
            ("parent_state", "=", "posted"),
        ]

        groups = self.env["account.move.line"].read_group(
            domain,
            ["debit", "credit", "amount_currency"],
            [],
        )

        if groups:
            debit = groups[0].get("debit", 0.0) or 0.0
            credit = groups[0].get("credit", 0.0) or 0.0
            amount_currency = groups[0].get("amount_currency", 0.0) or 0.0
        else:
            debit = credit = amount_currency = 0.0

        result = {
            "balance": debit - credit,
            "balance_moneda": amount_currency,
            "usar_balance_moneda": usar_balance_moneda,
        }
        return result
