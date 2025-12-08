# -*- coding: utf-8 -*-
from odoo import models
from .bak_report_xlsx_mixin import BakReportXlsxMixin


class DayBookReportXlsx(models.TransientModel, BakReportXlsxMixin):
    _inherit = "account.day.book.report"

    def action_export_xlsx(self):
        self.ensure_one()
        data = {}
        data["ids"] = self.env.context.get("active_ids", []) or self.ids
        data["model"] = self.env.context.get("active_model", self._name)
        data["form"] = self.read(
            ["date_from", "date_to", "journal_ids", "target_move", "account_ids"]
        )[0]
        used_context = self._build_contexts(data)
        data["form"]["used_context"] = dict(
            used_context, lang=self.env.context.get("lang") or "en_US"
        )

        report = self.env["report.base_accounting_kit.day_book_report_template"].with_context(
            active_model=self._name,
            active_ids=self.ids,
            active_id=self.id,
        )
        vals = report._get_report_values(docids=self.ids, data=data)
        accounts = vals.get("Accounts", [])

        header = [
            "Date", "Journal", "Partner", "Ref", "Move",
            "Entry Label", "Debit", "Credit", "Balance", "Currency",
        ]
        rows = []

        for acc in accounts:
            # fila resumen por fecha
            rows.append([
                acc.get("date") or "",
                "", "", "", "",
                "Total día",
                acc.get("debit") or 0.0,
                acc.get("credit") or 0.0,
                acc.get("balance") or 0.0,
                "",
            ])
            for line in acc.get("child_lines", []):
                rows.append([
                    line.get("ldate") or "",
                    line.get("lcode") or "",
                    line.get("partner_name") or "",
                    line.get("lref") or "",
                    line.get("move_name") or "",
                    line.get("lname") or "",
                    line.get("debit") or 0.0,
                    line.get("credit") or 0.0,
                    line.get("balance") or 0.0,
                    (
                        f"{line.get('amount_currency')} {line.get('currency_code')}"
                        if line.get("amount_currency")
                        else ""
                    ),
                ])

        return self._export_to_xlsx(header, rows, filename="Day_Book.xlsx", sheet_name="Day Book")



class BankBookReportXlsx(models.TransientModel, BakReportXlsxMixin):
    _inherit = "account.bank.book.report"

    def action_export_xlsx(self):
        self.ensure_one()
        data = {}
        data["ids"] = self.env.context.get("active_ids", []) or self.ids
        data["model"] = self.env.context.get("active_model", self._name)
        data["form"] = self.read([
            "date_from", "date_to", "journal_ids", "target_move",
            "display_account", "account_ids", "sortby",
        ])[0]
        used_context = self._build_contexts(data)
        data["form"]["used_context"] = dict(
            used_context, lang=self.env.context.get("lang") or "en_US"
        )

        report = self.env["report.base_accounting_kit.report_bank_book"].with_context(
            active_model=self._name,
            active_ids=self.ids,
            active_id=self.id,
        )
        vals = report._get_report_values(docids=self.ids, data=data)
        accounts = vals.get("Accounts", [])

        header = [
            "Account", "Date", "Journal", "Partner", "Ref",
            "Move", "Entry Label", "Debit", "Credit", "Balance", "Currency",
        ]
        rows = []

        for acc in accounts:
            acc_name = f"{acc.get('code', '')} {acc.get('name', '')}".strip()
            rows.append([
                acc_name, "", "", "", "",
                "", "Total cuenta",
                acc.get("debit") or 0.0,
                acc.get("credit") or 0.0,
                acc.get("balance") or 0.0,
                "",
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
                    (
                        f"{line.get('amount_currency')} {line.get('currency_code')}"
                        if line.get("amount_currency")
                        else ""
                    ),
                ])

        return self._export_to_xlsx(header, rows, filename="Bank_Book.xlsx", sheet_name="Bank Book")



class CashBookReportXlsx(models.TransientModel, BakReportXlsxMixin):
    _inherit = "account.cash.book.report"

    def action_export_xlsx(self):
        self.ensure_one()
        data = {}
        data["ids"] = self.env.context.get("active_ids", []) or self.ids
        data["model"] = self.env.context.get("active_model", self._name)
        data["form"] = self.read([
            "date_from", "date_to", "journal_ids", "target_move",
            "display_account", "account_ids", "sortby",
        ])[0]
        used_context = self._build_contexts(data)
        data["form"]["used_context"] = dict(
            used_context, lang=self.env.context.get("lang") or "en_US"
        )

        report = self.env["report.base_accounting_kit.report_cash_book"].with_context(
            active_model=self._name,
            active_ids=self.ids,
            active_id=self.id,
        )
        vals = report._get_report_values(docids=self.ids, data=data)
        accounts = vals.get("Accounts", [])

        header = [
            "Account", "Date", "Journal", "Partner", "Ref",
            "Move", "Entry Label", "Debit", "Credit", "Balance", "Currency",
        ]
        rows = []

        for acc in accounts:
            acc_name = f"{acc.get('code', '')} {acc.get('name', '')}".strip()
            rows.append([
                acc_name, "", "", "", "",
                "", "Total cuenta",
                acc.get("debit") or 0.0,
                acc.get("credit") or 0.0,
                acc.get("balance") or 0.0,
                "",
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
                    (
                        f"{line.get('amount_currency')} {line.get('currency_code')}"
                        if line.get("amount_currency")
                        else ""
                    ),
                ])

        return self._export_to_xlsx(header, rows, filename="Cash_Book.xlsx", sheet_name="Cash Book")

