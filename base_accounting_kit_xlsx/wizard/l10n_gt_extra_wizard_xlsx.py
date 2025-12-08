# -*- coding: utf-8 -*-
from odoo import api, models


class AsistenteReporteVentasXlsx(models.TransientModel):
    _inherit = "l10n_gt_extra.asistente_reporte_ventas"

    def print_report_excel(self):
        """Botón existente 'Reporte excel' en asistente_reporte_ventas_views."""
        self.ensure_one()
        # Campos relevantes para el reporte de ventas
        data = {
            "form": self.read([
                "folio_inicial",
                "fecha_desde",
                "fecha_hasta",
                "resumido",
                "impuesto_id",
                "diarios_id",
            ])[0]
        }
        report = self.env["report.l10n_gt_extra.reporte_ventas"]
        # Debes tener implementado report.action_export_xlsx(data)
        return report.action_export_xlsx(data)


class AsistenteReporteComprasXlsx(models.TransientModel):
    _inherit = "l10n_gt_extra.asistente_reporte_compras"

    def print_report_excel(self):
        """Botón existente 'Reporte excel' en asistente_reporte_compras_views."""
        self.ensure_one()
        data = {
            "form": self.read([
                "folio_inicial",
                "fecha_desde",
                "fecha_hasta",
                "impuesto_id",
                "diarios_id",
            ])[0]
        }
        report = self.env["report.l10n_gt_extra.reporte_compras"]
        return report.action_export_xlsx(data)


class AsistenteReporteDiarioXlsx(models.TransientModel):
    _inherit = "l10n_gt_extra.asistente_reporte_diario"

    def print_report_excel(self):
        """Botón existente 'Reporte excel' en asistente_reporte_diario_views."""
        self.ensure_one()
        data = {
            "form": self.read([
                "folio_inicial",
                "fecha_desde",
                "fecha_hasta",
                "agrupado_por_dia",
                "cuentas_id",
            ])[0]
        }
        report = self.env["report.l10n_gt_extra.reporte_diario"]
        return report.action_export_xlsx(data)


class AsistenteReporteMayorXlsx(models.TransientModel):
    _inherit = "l10n_gt_extra.asistente_reporte_mayor"

    def print_report_excel(self):
        """Botón existente 'Reporte excel' en asistente_reporte_mayor_views."""
        self.ensure_one()
        data = {
            "form": self.read([
                "folio_inicial",
                "fecha_desde",
                "fecha_hasta",
                "agrupado_por_dia",
                "cuentas_id",
            ])[0]
        }
        report = self.env["report.l10n_gt_extra.reporte_mayor"]
        return report.action_export_xlsx(data)


class AsistenteReporteInventarioXlsx(models.TransientModel):
    _inherit = "l10n_gt_extra.asistente_reporte_inventario"

    def action_export_xlsx(self):
        """Nuevo botón Excel para Inventario (no existía en la vista original)."""
        self.ensure_one()
        data = {
            "form": self.read([
                "folio_inicial",
                "fecha_hasta",
                "cuentas_id",
            ])[0]
        }
        report = self.env["report.l10n_gt_extra.reporte_inventario"]
        return report.action_export_xlsx(data)


class AsistenteReporteBancoXlsx(models.TransientModel):
    _inherit = "l10n_gt_extra.asistente_reporte_banco"

    def action_export_xlsx(self):
        """Nuevo botón Excel para Banco (no existía en la vista original)."""
        self.ensure_one()
        data = {
            "form": self.read([
                "cuenta_bancaria_id",
                "fecha_desde",
                "fecha_hasta",
            ])[0]
        }
        report = self.env["report.l10n_gt_extra.reporte_banco"]
        return report.action_export_xlsx(data)
