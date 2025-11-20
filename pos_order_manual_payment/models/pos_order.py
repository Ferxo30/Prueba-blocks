# -*- coding: utf-8 -*-
from odoo import api, fields, models


class PosOrder(models.Model):
    _inherit = "pos.order"

    # Muestra / oculta el botón y la pestaña de Pagos POS
    show_manual_payment_features = fields.Boolean(
        string="Mostrar Pagos POS",
        compute="_compute_manual_payments",
        store=False,
    )

    manual_payment_ids = fields.One2many(
        comodel_name="pos.order.payment",
        inverse_name="pos_order_id",
        string="Pagos POS",
    )

    manual_paid_amount = fields.Monetary(
        string="Total pagado POS",
        compute="_compute_manual_payments",
        currency_field="currency_id",
        store=True,
    )

    manual_payment_state = fields.Selection(
        [
            ("not_paid", "No pagado"),
            ("partial", "Parcialmente pagado"),
            ("paid", "Pagado"),
        ],
        string="Estado pago POS",
        compute="_compute_manual_payments",
        store=True,
    )

    can_register_manual_payment = fields.Boolean(
        string="Puede registrar pago POS",
        compute="_compute_manual_payments",
    )

    @api.depends(
        "manual_payment_ids.amount",
        "amount_total",
        "state",
        "payment_ids.payment_method_id.is_customer_account",
    )
    def _compute_manual_payments(self):
        """
        - Calcula total pagado manual, estado de pago POS
        - Determina si se deben mostrar las funcionalidades de pago POS
          (botón + pestaña), sólo cuando:
            * la orden NO está facturada
            * y tiene al menos un pago con método 'Cuenta de cliente'
              (payment_method_id.is_customer_account = True)
        """
        for order in self:
            # 1) Cálculo de montos manuales
            total = order.amount_total or 0.0
            paid = sum(order.manual_payment_ids.mapped("amount"))
            order.manual_paid_amount = paid

            if not paid:
                payment_status = "not_paid"
            elif paid + 0.00001 >= total:
                payment_status = "paid"
            else:
                payment_status = "partial"

            order.manual_payment_state = payment_status

            # 2) Ver si la orden tiene pagos con método "Cuenta de cliente"
            has_customer_account_payment = bool(
                order.payment_ids.filtered(
                    lambda p: p.payment_method_id
                    and getattr(p.payment_method_id, "is_customer_account", False)
                )
            )

            # 3) Mostrar o no las funcionalidades (botón + pestaña)
            #    Solo si NO está facturada y tiene pago con cuenta de cliente
            order.show_manual_payment_features = (
                has_customer_account_payment
                and order.state not in ("invoiced",)
            )

            # 4) Se puede registrar un pago POS extra si:
            #    - hay cuenta de cliente
            #    - la orden NO está facturada
            #    - y aún no está completamente pagada por Pagos POS
            order.can_register_manual_payment = (
                has_customer_account_payment
                and order.state not in ("draft", "cancel", "invoiced")
                and payment_status != "paid"
            )

    def action_open_pos_order_payment_wizard(self):
        """Abrir el wizard de registro de pago POS."""
        self.ensure_one()
        pending = max(self.amount_total - self.manual_paid_amount, 0.0)
        return {
            "name": "Registrar pago POS",
            "type": "ir.actions.act_window",
            "res_model": "pos.order.payment.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_pos_order_id": self.id,
                "default_amount": pending,
            },
        }
