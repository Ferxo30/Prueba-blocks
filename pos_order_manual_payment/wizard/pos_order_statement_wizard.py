# -*- coding: utf-8 -*-
import io
import base64
import xlsxwriter

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PosOrderStatementWizard(models.TransientModel):
    _name = "pos.order.statement.wizard"
    _description = "Estado de cuenta POS"

    # -------------------------------------------------------------------------
    # Campos del wizard
    # -------------------------------------------------------------------------
    partner_id = fields.Many2one(
        "res.partner",
        string="Cliente",
        help="Si se indica, solo se mostrarán órdenes de este cliente.",
    )
    date_from = fields.Date(string="Desde")
    date_to = fields.Date(string="Hasta")

    show_only_pending = fields.Boolean(
        string="Solo pendientes de pago",
        default=True,
        help="Si está activo, solo se mostrarán órdenes con saldo pendiente.",
    )

    # -------------------------------------------------------------------------
    # Dominio base: POS sin factura (crédito por cuenta de cliente)
    # -------------------------------------------------------------------------
    @api.model
    def _get_base_domain(self):
        """
        Dominio base: órdenes POS a crédito (Cuenta de cliente) sin factura.

        Reglas:
        - state en paid/done   -> ya cerradas en POS
        - account_move = False -> no tienen factura
        - payment_ids.payment_method_id.is_customer_account = True
          (método de pago marcado como 'Cuenta de cliente')
        """
        domain = [
            ("state", "in", ["paid", "done"]),
            ("account_move", "=", False),
            ("payment_ids.payment_method_id.is_customer_account", "=", True),
        ]
        return domain

    # -------------------------------------------------------------------------
    # Búsqueda de órdenes que entran al estado de cuenta
    # -------------------------------------------------------------------------
    def _get_orders(self):
        self.ensure_one()
        domain = self._get_base_domain()

        if self.partner_id:
            domain.append(("partner_id", "=", self.partner_id.id))
        if self.date_from:
            domain.append(("date_order", ">=", self.date_from))
        if self.date_to:
            domain.append(("date_order", "<=", self.date_to))

        orders = self.env["pos.order"].search(
            domain,
            order="partner_id, date_order, name",
        )

        # Filtro opcional: solo órdenes con saldo pendiente
        if self.show_only_pending:
            orders = orders.filtered(
                lambda o: (o.amount_total or 0.0) - (o.manual_paid_amount or 0.0) > 0.00001
            )

        return orders

    # -------------------------------------------------------------------------
    # Acción del botón "Imprimir estado de cuenta"
    # -------------------------------------------------------------------------
    def action_print_report(self):
        self.ensure_one()

        # 1) Órdenes según filtros del wizard
        orders = self._get_orders().exists()  # .exists() elimina IDs “muertos”

        if not orders:
            raise UserError(
                _("No se encontraron órdenes POS que cumplan los filtros seleccionados.")
            )

        # 2) Buscamos el reporte por nombre técnico
        report = self.env["ir.actions.report"]._get_report_from_name(
            "pos_order_manual_payment.report_pos_order_statement"
        )
        if not report:
            raise UserError(
                _(
                    "No se encontró el reporte técnico "
                    "'pos_order_manual_payment.report_pos_order_statement'.\n\n"
                    "Verifica que el archivo XML "
                    "'report/pos_order_statement_report.xml' esté cargado "
                    "y vuelve a actualizar el módulo."
                )
            )

        # 3) Limpiamos active_ids/active_id/active_model del CONTEXTO que vamos a usar
        ctx = dict(self.env.context or {})
        ctx.pop("active_ids", None)
        ctx.pop("active_id", None)
        ctx.pop("active_model", None)

        # Mandamos también los filtros del wizard por si los quieres usar en QWeb
        ctx.update(
            {
                "statement_partner_id": self.partner_id.id if self.partner_id else False,
                "statement_date_from": self.date_from and self.date_from.isoformat() or False,
                "statement_date_to": self.date_to and self.date_to.isoformat() or False,
                "statement_show_only_pending": self.show_only_pending,
            }
        )

        # 4) Llamamos al reporte usando el contexto LIMPIO
        action = report.with_context(ctx).report_action(orders.ids)
        return action

    # -------------------------------------------------------------------------
    # Exportar a Excel
    # -------------------------------------------------------------------------
    def action_export_xlsx(self):
        self.ensure_one()

        orders = self._get_orders().exists()
        if not orders:
            raise UserError(
                _("No se encontraron órdenes POS que cumplan los filtros seleccionados.")
            )

        # Crear libro en memoria
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {"in_memory": True})
        sheet = workbook.add_worksheet("Estado de cuenta POS")

        # Formatos
        bold = workbook.add_format({"bold": True})
        money = workbook.add_format({"num_format": "#,##0.00"})
        date_fmt = workbook.add_format({"num_format": "dd/mm/yyyy"})

        row = 0

        # Encabezado con filtros
        sheet.write(row, 0, "Cliente", bold)
        if self.partner_id:
            sheet.write(row, 1, self.partner_id.display_name or "")
        else:
            sheet.write(row, 1, "Todos")
        row += 1

        sheet.write(row, 0, "Solo pendientes", bold)
        sheet.write(row, 1, "Sí" if self.show_only_pending else "No")
        row += 1

        sheet.write(row, 0, "Desde", bold)
        sheet.write(row, 1, self.date_from and self.date_from.strftime("%d/%m/%Y") or "")
        row += 1

        sheet.write(row, 0, "Hasta", bold)
        sheet.write(row, 1, self.date_to and self.date_to.strftime("%d/%m/%Y") or "")
        row += 2

        # Encabezado de tabla
        headers = [
            "Fecha orden",
            "Cliente",
            "Correlativo interno",
            "Referencia",
            "Importe total",
            "Total pagado POS",
            "Saldo pendiente",
        ]
        for col, header in enumerate(headers):
            sheet.write(row, col, header, bold)
        row += 1

        # Mismos agrupamientos que en el PDF
        current_partner = False
        subtotal_total = 0.0
        subtotal_paid = 0.0
        subtotal_pending = 0.0

        for o in orders:
            partner = o.partner_id
            pending = (o.amount_total or 0.0) - (o.manual_paid_amount or 0.0)

            # Cambio de cliente: imprimir subtotal anterior
            if current_partner and partner != current_partner:
                display_name = current_partner.display_name or "Sin cliente"
                internal_code = current_partner.internal_code or False
                if internal_code:
                    label = "Total cliente (%s) %s" % (internal_code, display_name)
                else:
                    label = "Total cliente %s" % display_name

                sheet.write(row, 0, label, bold)
                sheet.write(row, 4, subtotal_total, money)
                sheet.write(row, 5, subtotal_paid, money)
                sheet.write(row, 6, subtotal_pending, money)
                row += 2
                subtotal_total = subtotal_paid = subtotal_pending = 0.0

            # Solo actualizamos current_partner (ya no escribimos "Cliente: ...")
            if not current_partner or partner != current_partner:
                current_partner = partner

            # Fila detalle
            if o.date_order:
                sheet.write_datetime(row, 0, o.date_order, date_fmt)
            else:
                sheet.write(row, 0, "")

            sheet.write(row, 1, partner.display_name or "")
            sheet.write(row, 2, o.name or "")
            sheet.write(row, 3, o.pos_reference or "")
            sheet.write(row, 4, o.amount_total or 0.0, money)
            sheet.write(row, 5, o.manual_paid_amount or 0.0, money)
            sheet.write(row, 6, pending, money)

            subtotal_total += o.amount_total or 0.0
            subtotal_paid += o.manual_paid_amount or 0.0
            subtotal_pending += pending
            row += 1

        # Subtotal último cliente
        if current_partner:
            display_name = current_partner.display_name or "Sin cliente"
            internal_code = current_partner.internal_code or False
            if internal_code:
                label = "Total cliente (%s) %s" % (internal_code, display_name)
            else:
                label = "Total cliente %s" % display_name

            sheet.write(row, 0, label, bold)
            sheet.write(row, 4, subtotal_total, money)
            sheet.write(row, 5, subtotal_paid, money)
            sheet.write(row, 6, subtotal_pending, money)

        workbook.close()
        output.seek(0)
        data = base64.b64encode(output.read())

        filename = "estado_cuenta_pos.xlsx"
        attachment = self.env["ir.attachment"].create({
            "name": filename,
            "type": "binary",
            "datas": data,
            "res_model": self._name,
            "res_id": self.id,
            "mimetype": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        })

        return {
            "type": "ir.actions.act_url",
            "url": "/web/content/%s?download=1" % attachment.id,
            "target": "self",
        }
