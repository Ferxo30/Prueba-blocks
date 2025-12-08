# -*- coding: utf-8 -*-
from odoo import models
from odoo.tools.misc import get_lang
from .bak_report_xlsx_mixin import BakReportXlsxMixin


class TaxReportXlsx(models.TransientModel, BakReportXlsxMixin):
    _inherit = "kit.account.tax.report"

    def action_export_xlsx(self):
        self.ensure_one()
        data = {}
        data["ids"] = self.env.context.get("active_ids", []) or self.ids
        data["model"] = self.env.context.get("active_model", self._name)
        data["form"] = self.read(
            ["date_from", "date_to", "journal_ids", "target_move", "company_id"]
        )[0]

        used_context = self._build_contexts(data)
        data["form"]["used_context"] = dict(
            used_context, lang=get_lang(self.env).code
        )
        data = self.pre_print_report(data)

        report = self.env["report.base_accounting_kit.report_tax"].with_context(
            active_model=self._name,
            active_ids=self.ids,
            active_id=self.id,
        )
        vals = report._get_report_values(docids=self.ids, data=data)
        groups = vals.get("lines", {})  # dict: {'sale': [...], 'purchase': [...]}

        header = ["Type", "Tax", "Base", "Tax Amount"]
        rows = []

        for tp, items in groups.items():
            type_label = tp.capitalize()
            for t in items:
                rows.append([
                    type_label,
                    t.get("name") or "",
                    t.get("net") or 0.0,
                    t.get("tax") or 0.0,
                ])

        filename = "Tax_Report.xlsx"
        return self._export_to_xlsx(header, rows, filename=filename, sheet_name="Tax Report")
