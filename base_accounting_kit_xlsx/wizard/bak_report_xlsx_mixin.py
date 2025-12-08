# -*- coding: utf-8 -*-
import io
import base64

from odoo import models
from odoo.exceptions import UserError


class BakReportXlsxMixin(models.AbstractModel):
    _name = "bak.report.xlsx.mixin"
    _description = "BAK XLSX helper"

    def _export_to_xlsx(self, header, rows, filename, sheet_name="Sheet1"):
        """
        Genera un XLSX en memoria, crea un ir.attachment y devuelve
        un ir.actions.act_url apuntando a /web/content/<id>?download=1

        No usamos self.id ni self.ensure_one(), para que funcione también
        con modelos report.* (AbstractModel).
        """
        try:
            import xlsxwriter
        except ImportError:
            raise UserError("Falta la librería python 'xlsxwriter'.")

        # Crear el archivo en memoria
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {"in_memory": True})

        # Excel sólo permite 31 caracteres para el nombre de la hoja
        worksheet = workbook.add_worksheet(sheet_name[:31])

        # Encabezados
        for col, h in enumerate(header):
            worksheet.write(0, col, h)

        # Filas
        row_idx = 1
        for row in rows:
            for col, value in enumerate(row):
                worksheet.write(row_idx, col, value)
            row_idx += 1

        workbook.close()
        output.seek(0)
        xlsx_data = base64.b64encode(output.read())

        # Crear adjunto (no hace falta ligarlo a un modelo real)
        attachment = self.env["ir.attachment"].create({
            "name": filename,
            "type": "binary",
            "datas": xlsx_data,
            "mimetype": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "res_model": "ir.ui.view",
            "public": False,
        })

        # Descargar el archivo usando el controlador estándar de Odoo
        return {
            "type": "ir.actions.act_url",
            "url": f"/web/content/{attachment.id}?download=1",
            "target": "self",
        }
