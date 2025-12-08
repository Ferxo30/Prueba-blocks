# -*- coding: utf-8 -*-
from odoo import models
from .bak_report_xlsx_mixin import BakReportXlsxMixin


class GeneralLedgerXlsx(models.TransientModel, BakReportXlsxMixin):
    _inherit = "account.report.general.ledger"

    def action_export_xlsx(self):
        self.ensure_one()

        data = {
            "ids": self.env.context.get("active_ids", []) or self.ids,
            "model": self.env.context.get("active_model", self._name),
            "form": {},
        }
        # Igual que hace el wizard original: completa form con display_account, etc.
        data = self.pre_print_report(data)
        data["form"].update(self.read(["initial_balance", "sortby"])[0])

        report = self.env["report.base_accounting_kit.report_general_ledger"].with_context(
            active_model=self._name,
            active_ids=self.ids,
            active_id=self.id,
        )
        vals = report._get_report_values(docids=self.ids, data=data)
        accounts = vals.get("Accounts", [])

        header = [
            "Account", "Date", "Journal", "Partner", "Ref",
            "Move", "Entry Label", "Debit", "Credit", "Balance",
        ]
        rows = []

        for acc in accounts:
            acc_name = f"{acc.get('code', '')} {acc.get('name', '')}".strip()
            rows.append([
                acc_name, "", "", "", "", "", "Total cuenta",
                acc.get("debit") or 0.0,
                acc.get("credit") or 0.0,
                acc.get("balance") or 0.0,
            ])
            for line in acc.get("move_lines", []):
                rows.append([
                    "",
                    line.get("ldate") or "",
                    line.get("lcode") or "",
                    line.get("partner_name") or "",
                    line.get("lref") or "",
                    line.get("move_name") or "",
                    line.get("lname") or "",
                    line.get("debit") or 0.0,
                    line.get("credit") or 0.0,
                    line.get("balance") or 0.0,
                ])

        filename = "General_Ledger.xlsx"
        return self._export_to_xlsx(header, rows, filename=filename, sheet_name="General Ledger")


