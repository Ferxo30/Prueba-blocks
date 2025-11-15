# -*- coding: utf-8 -*-

from odoo import models, _


class AccountPartnerLedger(models.TransientModel):
    _inherit = 'account.report.partner.ledger'

    def _print_report_xlsx(self, data):
        """Genera el Excel del Partner Ledger reutilizando la lógica del reporte QWeb."""
        # Igual que _print_report del wizard original
        data = self.pre_print_report(data)
        data['form'].update({
            'reconciled': self.reconciled,
            'amount_currency': self.amount_currency,
            'partner_ids': self.partner_ids.ids,
        })

        report_model = self.env['report.base_accounting_kit.report_partnerledger']

        vals = report_model._get_report_values(
            self.env.context.get('active_ids', []),
            data=data,
        )

        partners = vals['docs']
        computed_data = vals['data']

        filename = _("Partner_Ledger.xlsx")

        def build(workbook):
            sheet = workbook.add_worksheet(_("Partner Ledger")[:31])
            row = 0

            header_fmt = workbook.add_format({'bold': True})
            headers = [
                _('Partner'),
                _('Date'),
                _('Journal'),
                _('Account'),
                _('Label'),
                _('Debit'),
                _('Credit'),
                _('Balance'),
                _('Currency'),
                _('Amount Currency'),
            ]
            for col, h in enumerate(headers):
                sheet.write(row, col, h, header_fmt)
            row += 1

            def _safe(val):
                """Convierte cualquier cosa rara a algo que xlsxwriter entienda."""
                if val is None:
                    return ''
                if isinstance(val, (int, float)):
                    return val
                # Para dicts (como a_name), intentamos sacar un nombre legible
                if isinstance(val, dict):
                    return (
                        val.get('name')
                        or val.get('display_name')
                        or val.get('code')
                        or str(val)
                    )
                # para todo lo demás (recordsets, etc.) usamos str()
                return str(val)

            # Para cada partner, usamos el helper _lines del reporte
            for partner in partners:
                lines = report_model._lines(computed_data, partner)
                for line in lines:
                    sheet.write(row, 0, _safe(partner.display_name))
                    sheet.write(row, 1, _safe(line.get('date')))
                    sheet.write(row, 2, _safe(line.get('code')))          # journal code

                    # a_name puede ser dict → usamos _safe para convertirlo
                    sheet.write(row, 3, _safe(line.get('a_name')))        # account name

                    sheet.write(row, 4, _safe(line.get('displayed_name')))
                    sheet.write(row, 5, _safe(line.get('debit')))
                    sheet.write(row, 6, _safe(line.get('credit')))
                    sheet.write(row, 7, _safe(line.get('progress')))      # saldo acumulado
                    sheet.write(row, 8, _safe(line.get('currency_code')))
                    sheet.write(row, 9, _safe(line.get('amount_currency')))
                    row += 1

        return self._xlsx_response(filename, build)
