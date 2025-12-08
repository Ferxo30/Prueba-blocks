# -*- coding: utf-8 -*-
from odoo import models
from .bak_report_xlsx_mixin import BakReportXlsxMixin


class CashFlowReportXlsx(models.TransientModel, BakReportXlsxMixin):
    _inherit = "cash.flow.report"

    def action_export_xlsx(self):
        self.ensure_one()

        data = {
            "ids": self.env.context.get("active_ids", []) or self.ids,
            "model": self.env.context.get("active_model", self._name),
        }
        data["form"] = self.read([
            "date_from_cmp", "debit_credit", "date_to_cmp", "filter_cmp",
            "account_report_id", "enable_filter", "label_filter",
            "target_move",
        ])[0]

        report = self.env["report.base_accounting_kit.report_cash_flow"].with_context(
            active_model=self._name,
            active_ids=self.ids,
            active_id=self.id,
        )
        vals = report._get_report_values(docids=self.ids, data=data)
        lines = vals.get("report_lines", []) or vals.get("get_account_lines", [])

        show_debit_credit = bool(data["form"].get("debit_credit"))
        rows = []

        if show_debit_credit:
            header = ["Name", "Debit", "Credit", "Balance"]
            for line in lines:
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
            for line in lines:
                name = line.get("name") or ""
                indent = ".." * int(line.get("level", 0))
                if indent:
                    name = f"{indent} {name}"
                rows.append([
                    name,
                    line.get("balance") or 0.0,
                ])

        filename = "Cash_Flow_Statement.xlsx"
        return self._export_to_xlsx(header, rows, filename=filename, sheet_name="Cash Flow")

