# -*- coding: utf-8 -*-
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
