# -*- coding: utf-8 -*-
from odoo import models
from .bak_report_xlsx_mixin import BakReportXlsxMixin


class TrialBalanceXlsx(models.TransientModel, BakReportXlsxMixin):
    _inherit = "account.balance.report"

    def action_export_xlsx(self):
        self.ensure_one()

        data = {
            "ids": self.env.context.get("active_ids", []) or self.ids,
            "model": self.env.context.get("active_model", self._name),
            "form": {},
        }
        data = self.pre_print_report(data)

        report = self.env["report.base_accounting_kit.report_trial_balance"].with_context(
            active_model=self._name,
            active_ids=self.ids,
            active_id=self.id,
        )
        vals = report._get_report_values(docids=self.ids, data=data)
        accounts = vals.get("Accounts", [])

        header = ["Code", "Account", "Debit", "Credit", "Balance"]
        rows = []

        for acc in accounts:
            rows.append([
                acc.get("code") or "",
                acc.get("name") or "",
                acc.get("debit") or 0.0,
                acc.get("credit") or 0.0,
                acc.get("balance") or 0.0,
            ])

        filename = "Trial_Balance.xlsx"
        return self._export_to_xlsx(header, rows, filename=filename, sheet_name="Trial Balance")
