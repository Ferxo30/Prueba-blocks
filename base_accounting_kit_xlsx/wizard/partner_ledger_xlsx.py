# -*- coding: utf-8 -*-
from odoo import models
from .bak_report_xlsx_mixin import BakReportXlsxMixin


class PartnerLedgerXlsx(models.TransientModel, BakReportXlsxMixin):
    _inherit = "account.report.partner.ledger"

    def action_export_xlsx(self):
        self.ensure_one()

        data = {
            "ids": self.env.context.get("active_ids", []),
            "model": self.env.context.get("active_model", "res.partner"),
            "form": {},  # <- inicializado
        }
        data = self.pre_print_report(data)
        data["form"].update({
            "reconciled": self.reconciled,
            "amount_currency": self.amount_currency,
            "partner_ids": self.partner_ids.ids,
        })

        report_model = self.env["report.base_accounting_kit.report_partnerledger"]
        vals = report_model._get_report_values(self.ids, data=data)
        docs = vals.get("docs", [])
        form = vals.get("data", data["form"])

        header = [
            "Partner", "Date", "Journal", "Label",
            "Debit", "Credit", "Balance", "Currency",
        ]
        rows = []

        for partner in docs:
            partner_name = f"{partner.ref or ''} - {partner.name or ''}".strip(" -")
            total_debit = report_model._sum_partner(form, partner, "debit")
            total_credit = report_model._sum_partner(form, partner, "credit")
            total_balance = report_model._sum_partner(form, partner, "debit - credit")

            rows.append([
                partner_name,
                "",
                "",
                "Total partner",
                total_debit,
                total_credit,
                total_balance,
                "",
            ])

            for line in report_model._lines(form, partner):
                currency_txt = ""
                if form.get("amount_currency") and line.get("currency_id"):
                    currency_txt = str(line.get("amount_currency") or "")

                rows.append([
                    "",
                    line.get("date") or "",
                    line.get("code") or "",
                    line.get("displayed_name") or "",
                    line.get("debit") or 0.0,
                    line.get("credit") or 0.0,
                    line.get("progress") or 0.0,
                    currency_txt,
                ])

        filename = "Partner_Ledger.xlsx"
        return self._export_to_xlsx(header, rows, filename=filename, sheet_name="Partner Ledger")
