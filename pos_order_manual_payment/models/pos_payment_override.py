# -*- coding: utf-8 -*-

from odoo import api, models, _
from odoo.exceptions import ValidationError


class PosPayment(models.Model):
    _inherit = "pos.payment"

    @api.constrains("amount")
    def _check_amount(self):
        """Misma validación que Odoo, pero permite bypass por contexto.

        Cuando el contexto trae ``allow_pos_registered_payment_edit=True``
        no se bloquea la edición de pagos aunque la orden esté registrada.
        """
        if self.env.context.get("allow_pos_registered_payment_edit"):
            return

        for payment in self:
            order = payment.pos_order_id
            pos_session = getattr(payment, "pos_session_id", False)
            if order and order.state in ["invoiced", "done"]:
                if order.session_id == pos_session:
                    raise ValidationError(
                        _("You cannot edit a payment for a posted order.")
                    )
