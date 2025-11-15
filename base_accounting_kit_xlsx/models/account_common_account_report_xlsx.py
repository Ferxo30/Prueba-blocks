# -*- coding: utf-8 -*-

from odoo import models, _
from odoo.exceptions import UserError
from odoo.tools.misc import xlsxwriter, get_lang
import io
import base64


class AccountReport(models.Model):
    """
    Extendemos el modelo base 'account.report' (el mismo que usa
    base_accounting_kit para el wizard "Report Options") para añadir:

      - check_report_xlsx: método llamado por el botón "Exportar a Excel"
      - _print_report_xlsx: hook a sobreescribir en cada reporte concreto
      - _xlsx_response: helper para crear y devolver el archivo XLSX
    """
    _inherit = 'account.report'

    def _print_report_xlsx(self, data):
        """Por defecto NO implementado.

        Cada wizard concreto (Mayor General, Partner Ledger, Balance, etc.)
        debe sobreescribir este método.
        """
        raise UserError(_("Este reporte todavía no soporta exportación a Excel."))

    def check_report_xlsx(self):
        """Método llamado por el botón 'Exportar a Excel' en la vista base.

        Es prácticamente un clon de check_report(), pero llamando a
        _print_report_xlsx en lugar de _print_report.
        """
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')

        # Mismos campos que usa base_accounting_kit en check_report()
        data['form'] = self.read([
            'date_from',
            'date_to',
            'journal_ids',
            'target_move',
            'company_id',
        ])[0]

        # Usamos el mismo _build_contexts que ya define AccountCommonReport
        used_context = self._build_contexts(data)
        data['form']['used_context'] = dict(
            used_context,
            lang=get_lang(self.env).code,
        )

        # Igual que en check_report(), pero llamando a nuestra versión XLSX
        return self.with_context(discard_logo_check=True)._print_report_xlsx(data)

    def _xlsx_response(self, filename, build_func):
        """Helper genérico para construir y devolver un XLSX.

        - filename: nombre del archivo (string)
        - build_func(workbook): función que escribe el contenido en el workbook
        """
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        build_func(workbook)
        workbook.close()
        output.seek(0)
        xlsx_data = output.read()

        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'datas': base64.b64encode(xlsx_data),
            'res_model': self._name,
            'res_id': self.id,
            'type': 'binary',
            'mimetype': (
                'application/vnd.openxmlformats-officedocument.'
                'spreadsheetml.sheet'
            ),
        })

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=1' % attachment.id,
            'target': 'self',
        }
