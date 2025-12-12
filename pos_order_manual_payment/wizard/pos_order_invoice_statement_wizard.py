# -*- coding: utf-8 -*-
import io
import base64
import xlsxwriter

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PosOrderInvoiceStatementWizard(models.TransientModel):
    _name = "pos.order.invoice.statement.wizard"
    _description = "Estado de cuenta de facturación POS"

    # -------------------------------------------------------------------------
    # Campos del wizard
    # -------------------------------------------------------------------------
    partner_id = fields.Many2one(
        "res.partner",
        string="Cliente",
        help="Si se indica, solo se mostrarán órdenes de este cliente.",
    )
    pos_config_id = fields.Many2one(
        "pos.config",
        string="Establecimiento",
        help="Si se indica, solo se mostrarán órdenes de este punto de venta.",
    )
    date_from = fields.Date(string="Desde")
    date_to = fields.Date(string="Hasta")

    show_only_pending = fields.Boolean(
        string="Solo facturas con saldo pendiente",
        default=True,
    )

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------
    def _get_orders_domain(self):
        """Dominio base: órdenes POS que tengan factura."""
        self.ensure_one()
        domain = [
            ("account_move", "!=", False),
        ]

        if self.partner_id:
            domain.append(("partner_id", "=", self.partner_id.id))

        if self.pos_config_id:
            domain.append(("session_id.config_id", "=", self.pos_config_id.id))

        if self.date_from:
            # Filtramos por fecha de la factura
            domain.append(("account_move.invoice_date", ">=", self.date_from))

        if self.date_to:
            domain.append(("account_move.invoice_date", "<=", self.date_to))

        return domain

    def _order_has_refunds(self, order):
        """Devuelve True si la orden es un reembolso o tiene reembolsos ligados."""
        refund_order = getattr(order, "refund_order_id", False)
        refund_orders_1 = getattr(order, "refund_order_ids", False)
        refund_orders_2 = getattr(order, "refund_orders", False)
        refund_count = getattr(order, "refund_orders_count", 0)
        return bool(refund_order or refund_orders_1 or refund_orders_2 or refund_count)

    def _filter_and_sort_orders(self, orders):
        """Aplica filtros comunes (pendientes, reembolsos) y ordenamiento."""
        # Filtramos por saldo pendiente si corresponde
        if self.show_only_pending:
            orders = orders.filtered(
                lambda o: o.account_move and o.account_move.amount_residual > 0
            )

        # Excluir órdenes que sean reembolsos o tengan reembolsos asociados
        orders = orders.filtered(lambda o: not self._order_has_refunds(o))

        if not orders:
            return orders

        # Ordenar: código interno del cliente, nombre cliente, fecha factura, correlativo interno / nombre
        orders = orders.sorted(
            key=lambda o: (
                o.partner_id.internal_code or "",
                o.partner_id.display_name or "",
                o.account_move.invoice_date or o.date_order or fields.Date.today(),
                o.internal_correlative or o.name or "",
            )
        )
        return orders

    # -------------------------------------------------------------------------
    # Acción principal (PDF)
    # -------------------------------------------------------------------------
    def action_print(self):
        self.ensure_one()

        report = self.env.ref(
            "pos_order_manual_payment.action_report_pos_order_invoice_statement",
            raise_if_not_found=False,
        )
        if not report:
            raise UserError(_(
                "No se encontró la acción de reporte "
                "'action_report_pos_order_invoice_statement'. "
                "Verifica el XML del reporte."
            ))

        domain = self._get_orders_domain()
        orders = self.env["pos.order"].search(domain)

        orders = self._filter_and_sort_orders(orders)
        if not orders:
            raise UserError(_(
                "No se encontraron órdenes de POS con factura "
                "que coincidan con los filtros."
            ))

        # Contexto para el QWeb
        ctx = dict(self.env.context or {})
        ctx.update(
            {
                "statement_partner_id": self.partner_id.id if self.partner_id else False,
                "statement_pos_config_id": self.pos_config_id.id if self.pos_config_id else False,
                "statement_date_from": self.date_from and self.date_from.isoformat() or False,
                "statement_date_to": self.date_to and self.date_to.isoformat() or False,
                "statement_show_only_pending": self.show_only_pending,
                "statement_mode": "invoice",
            }
        )

        return report.with_context(ctx).report_action(orders.ids)

    # -------------------------------------------------------------------------
    # Exportar a Excel
    # -------------------------------------------------------------------------
    def action_export_xlsx(self):
        self.ensure_one()

        domain = self._get_orders_domain()
        orders = self.env["pos.order"].search(domain)

        orders = self._filter_and_sort_orders(orders)
        if not orders:
            raise UserError(_(
                "No se encontraron órdenes de POS con factura "
                "que coincidan con los filtros."
            ))

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {"in_memory": True})
        sheet = workbook.add_worksheet("Facturación POS")

        bold = workbook.add_format({"bold": True})
        money = workbook.add_format({"num_format": "#,##0.00"})

        row = 0

        # Filtros
        sheet.write(row, 0, "Cliente", bold)
        if self.partner_id:
            sheet.write(row, 1, self.partner_id.display_name or "")
        else:
            sheet.write(row, 1, "Todos")
        row += 1

        sheet.write(row, 0, "Establecimiento", bold)
        if self.pos_config_id:
            sheet.write(row, 1, self.pos_config_id.display_name or self.pos_config_id.name or "")
        else:
            sheet.write(row, 1, "Todos")
        row += 1

        sheet.write(row, 0, "Solo con saldo pendiente", bold)
        sheet.write(row, 1, "Sí" if self.show_only_pending else "No")
        row += 1

        sheet.write(row, 0, "Desde", bold)
        sheet.write(row, 1, self.date_from and self.date_from.strftime("%d/%m/%Y") or "")
        row += 1

        sheet.write(row, 0, "Hasta", bold)
        sheet.write(row, 1, self.date_to and self.date_to.strftime("%d/%m/%Y") or "")
        row += 2

        # Encabezados
        headers = [
            "Fecha factura",
            "Cliente",
            "Orden POS",
            "DTE FEL",
            "Total factura",
            "Total pagado",
            "Saldo pendiente",
        ]
        for col, header in enumerate(headers):
            sheet.write(row, col, header, bold)
        row += 1

        current_partner = False
        subtotal_total = subtotal_paid = subtotal_pending = 0.0

        for o in orders:
            inv = o.account_move
            if not inv:
                continue

            total = inv.amount_total or 0.0
            pending = inv.amount_residual or 0.0
            paid = total - pending

            partner = inv.partner_id

            # Cambio de cliente: subtotal
            if current_partner and partner != current_partner:
                display_name = current_partner.display_name or "Sin cliente"
                internal_code = getattr(current_partner, "internal_code", False) or False
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

            # Encabezado cliente (solo actualizamos current_partner)
            if not current_partner or partner != current_partner:
                current_partner = partner

            # Fila detalle
            sheet.write(row, 0, inv.invoice_date and inv.invoice_date.strftime("%d/%m/%Y") or "")
            sheet.write(row, 1, partner.display_name or "")
            sheet.write(row, 2, o.internal_correlative or o.name or "")
            # Usar número FEL (numero_fel) en lugar del nombre de la factura
            sheet.write(row, 3, getattr(inv, "numero_fel", "") or "")
            sheet.write(row, 4, total, money)
            sheet.write(row, 5, paid, money)
            sheet.write(row, 6, pending, money)

            subtotal_total += total
            subtotal_paid += paid
            subtotal_pending += pending
            row += 1

        # Subtotal último cliente
        if current_partner:
            display_name = current_partner.display_name or "Sin cliente"
            internal_code = getattr(current_partner, "internal_code", False) or False
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

        filename = "estado_cuenta_facturacion_pos.xlsx"
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
