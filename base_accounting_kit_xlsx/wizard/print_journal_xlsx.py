# -*- coding: utf-8 -*-
from odoo import models
from .bak_report_xlsx_mixin import BakReportXlsxMixin


class PrintJournalXlsx(models.TransientModel, BakReportXlsxMixin):
    _inherit = "account.print.journal"

    def action_export_xlsx(self):
        self.ensure_one()

        data = {
            "ids": self.env.context.get("active_ids", []) or self.ids,
            "model": self.env.context.get("active_model", self._name),
            "form": {},
        }
        data = self.pre_print_report(data)
        data["form"].update({"sort_selection": self.sort_selection})

        report = self.env["report.base_accounting_kit.report_journal_audit"].with_context(
            active_model=self._name,
            active_ids=self.ids,
            active_id=self.id,
        )
        vals = report._get_report_values(docids=self.ids, data=data)
        lines = vals.get("MoveLines", []) or vals.get("lines", [])

        header = [
            "Journal", "Date", "Entry", "Account",
            "Partner", "Label", "Debit", "Credit",
        ]
        rows = []

        for l in lines:
            rows.append([
                l.get("journal") or "",
                l.get("date") or "",
                l.get("move_name") or "",
                l.get("account_code") or "",
                l.get("partner_name") or "",
                l.get("name") or "",
                l.get("debit") or 0.0,
                l.get("credit") or 0.0,
            ])

        filename = "Journals_Audit.xlsx"
        return self._export_to_xlsx(header, rows, filename=filename, sheet_name="Journals Audit")


