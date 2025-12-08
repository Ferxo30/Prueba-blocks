from odoo import models, _
from odoo.exceptions import UserError
from .bak_report_xlsx_mixin import BakReportXlsxMixin
from datetime import datetime
from dateutil.relativedelta import relativedelta


class AgedPartnerBalanceXlsx(models.TransientModel, BakReportXlsxMixin):
    _inherit = "account.aged.trial.balance"

    def action_export_xlsx(self):
        self.ensure_one()

        data = {
            "ids": self.env.context.get("active_ids", []) or self.ids,
            "model": self.env.context.get("active_model", self._name),
            "form": self.read(["date_from", "period_length", "result_selection",
                               "target_move", "company_id"])[0],
        }

        period_length = data["form"]["period_length"]
        if period_length <= 0:
            raise UserError(_("You must set a period length greater than 0."))
        if not data["form"]["date_from"]:
            raise UserError(_("You must set a start date."))

        start = data["form"]["date_from"]
        start = datetime.strptime(start, "%Y-%m-%d").date()
        res = {}
        for i in range(5)[::-1]:
            stop = start - relativedelta(days=period_length - 1)
            res[str(i)] = {
                "name": (i != 0 and (
                    str((5 - (i + 1)) * period_length) + "-" + str(
                        (5 - i) * period_length)) or (
                    "+" + str(4 * period_length))),
                "stop": start.strftime("%Y-%m-%d"),
                "start": (i != 0 and stop.strftime("%Y-%m-%d") or False),
            }
            start = stop - relativedelta(days=1)
        data["form"].update(res)

        report = self.env["report.base_accounting_kit.report_agedpartnerbalance"].with_context(
            active_model=self._name,
            active_ids=self.ids,
            active_id=self.id,
        )
        vals = report._get_report_values(docids=self.ids, data=data)
        lines = vals.get("get_partner_lines", [])
        totals = vals.get("get_direction", {})

        header = [
            "Partner",
            "Not due",
            data["form"]["4"]["name"],
            data["form"]["3"]["name"],
            data["form"]["2"]["name"],
            data["form"]["1"]["name"],
            data["form"]["0"]["name"],
            "Total",
        ]
        rows = []

        if totals:
            rows.append([
                "Account Total",
                totals.get("direction", 0.0),
                totals.get("4", 0.0),
                totals.get("3", 0.0),
                totals.get("2", 0.0),
                totals.get("1", 0.0),
                totals.get("0", 0.0),
                totals.get("total", 0.0),
            ])

        for p in lines:
            rows.append([
                p.get("name") or "",
                p.get("direction") or 0.0,
                p.get("4") or 0.0,
                p.get("3") or 0.0,
                p.get("2") or 0.0,
                p.get("1") or 0.0,
                p.get("0") or 0.0,
                p.get("total") or 0.0,
            ])

        filename = "Aged_Partner_Balance.xlsx"
        return self._export_to_xlsx(header, rows, filename=filename, sheet_name="Aged Partner")
