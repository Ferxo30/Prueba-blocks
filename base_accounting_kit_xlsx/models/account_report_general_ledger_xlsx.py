# -*- coding: utf-8 -*-

from odoo import models, _
from odoo.exceptions import UserError


class AccountReportGeneralLedger(models.TransientModel):
    _inherit = 'account.report.general.ledger'

    def _print_report_xlsx(self, data):
        """Genera el Excel del Mayor General reutilizando la lógica del reporte QWeb."""
        # Copiamos la lógica de _print_report original
        data = self.pre_print_report(data)
        data['form'].update(self.read(['initial_balance', 'sortby'])[0])

        if data['form'].get('initial_balance') and not data['form'].get('date_from'):
            raise UserError(_("You must define a Start Date"))

        records = self.env[data['model']].browse(data.get('ids', []))
        used_context = data['form'].get('used_context', {})

        # Motor del reporte PDF
        report_model = self.env['report.base_accounting_kit.report_general_ledger']

        model = data['model']
        docs = records
        init_balance = data['form'].get('initial_balance', True)
        sortby = data['form'].get('sortby', 'sort_date')
        display_account = data['form']['display_account']

        codes = []
        if data['form'].get('journal_ids'):
            codes = [j.code for j in self.env['account.journal'].browse(
                data['form']['journal_ids'])]

        accounts = docs if model == 'account.account' else self.env[
            'account.account'].search([])

        accounts_res = report_model.with_context(
            used_context
        )._get_account_move_entry(
            accounts, init_balance, sortby, display_account
        )

        filename = _("General_Ledger.xlsx")

        def build(workbook):
            sheet = workbook.add_worksheet(_("General Ledger")[:31])
            row = 0

            header_fmt = workbook.add_format({'bold': True})
            headers = [
                _('Account Code'),
                _('Account Name'),
                _('Date'),
                _('Journal'),
                _('Reference'),
                _('Label'),
                _('Partner'),
                _('Debit'),
                _('Credit'),
                _('Balance'),
            ]
            for col, h in enumerate(headers):
                sheet.write(row, col, h, header_fmt)
            row += 1

            # Llenar líneas
            for acc in accounts_res:
                code = acc.get('code')
                name = acc.get('name')
                for line in acc.get('move_lines', []):
                    sheet.write(row, 0, code)
                    sheet.write(row, 1, name)
                    sheet.write(row, 2, line.get('ldate'))
                    sheet.write(row, 3, line.get('lcode'))
                    sheet.write(row, 4, line.get('lref'))
                    sheet.write(row, 5, line.get('lname'))
                    sheet.write(row, 6, line.get('partner_name'))
                    sheet.write(row, 7, line.get('debit') or 0.0)
                    sheet.write(row, 8, line.get('credit') or 0.0)
                    sheet.write(row, 9, line.get('balance') or 0.0)
                    row += 1

        return self._xlsx_response(filename, build)
