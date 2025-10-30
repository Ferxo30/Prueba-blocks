from odoo import models
from odoo.exceptions import UserError

class StockScrap(models.Model):
    _inherit = "stock.scrap"

    def action_print_scrap(self):
        self.ensure_one()

        REPORT_NAME = 'stock_scrap_print_button_fix.report_stock_scrap_document'
        Report = self.env['ir.actions.report']

        # 1) Intenta por xmlid del action (si existe)
        report = False
        try:
            report = self.env.ref('stock_scrap_print_button_fix.action_report_stock_scrap')
        except Exception:
            report = False

        # 2) Intenta por report_name exacto
        if not report:
            report = Report._get_report_from_name(REPORT_NAME)

        # 3) Busca por criterios (por si hay espacios/typos)
        if not report:
            report = Report.search([
                ('model', '=', 'stock.scrap'),
                ('report_type', '=', 'qweb-pdf'),
                ('report_name', '=', REPORT_NAME),
            ], limit=1)

        # 4) Si NO existe, lo creamos en caliente (autocorrección)
        if not report:
            # Verifica que la plantilla QWeb exista
            try:
                self.env.ref(REPORT_NAME)  # asegura que la vista QWeb existe
            except Exception:
                raise UserError(
                    "No encuentro la plantilla QWeb del reporte.\n"
                    f"Plantilla esperada: {REPORT_NAME}\n"
                    "Verifica en Ajustes → Técnico → Vistas que exista con ese ID externo."
                )
            # Crea la acción de reporte
            vals = {
                'name': 'Orden de Desecho',
                'model': 'stock.scrap',
                'report_type': 'qweb-pdf',
                'report_name': REPORT_NAME,
                'report_file': REPORT_NAME,
                'print_report_name': "'SCRAP-%s' % (object.name or '')",
            }
            report = Report.create(vals)

        # 5) Devuelve SIEMPRE la acción lista para imprimir
        return report.report_action(self)
