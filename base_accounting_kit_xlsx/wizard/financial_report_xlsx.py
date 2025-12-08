# -*- coding: utf-8 -*-
from odoo import models
from .bak_report_xlsx_mixin import BakReportXlsxMixin


class FinancialReportXlsx(models.TransientModel, BakReportXlsxMixin):
    _inherit = "financial.report"

    def action_export_xlsx(self):
        self.ensure_one()

        data = dict()
        data["ids"] = self.env.context.get("active_ids", [])
        data["model"] = self.env.context.get("active_model", "ir.ui.menu")
        data["form"] = self.read([
            "date_from",
            "enable_filter",
            "debit_credit",
            "date_to",
            "account_report_id",
            "target_move",
            "view_format",
            "company_id",
        ])[0]

        used_context = self._build_contexts(data)
        data["form"]["used_context"] = dict(
            used_context,
            lang=self.env.context.get("lang") or "en_US",
        )

        report_lines = self.get_account_lines(data["form"])
        show_debit_credit = bool(data["form"].get("debit_credit"))
        rows = []

        if show_debit_credit:
            header = ["Name", "Debit", "Credit", "Balance"]
            for line in report_lines:
                if line.get("level") == 0:
                    continue
                name = line.get("name") or ""
                indent = ".." * int(line.get("level", 0))
                if indent:
                    name = f"{indent} {name}"
                rows.append([
                    name,
                    line.get("debit") or 0.0,
                    line.get("credit") or 0.0,
                    line.get("balance") or 0.0,
                ])
        else:
            header = ["Name", "Balance"]
            for line in report_lines:
                if line.get("level") == 0:
                    continue
                name = line.get("name") or ""
                indent = ".." * int(line.get("level", 0))
                if indent:
                    name = f"{indent} {name}"
                rows.append([
                    name,
                    line.get("balance") or 0.0,
                ])

        report_name = data["form"]["account_report_id"][1] if data["form"].get("account_report_id") else "Financial_Report"
        filename = f"{report_name.replace(' ', '_')}.xlsx"
        return self._export_to_xlsx(header, rows, filename=filename, sheet_name=report_name)
