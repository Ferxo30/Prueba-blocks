# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class PosOrderPayment(models.Model):
    _name = "pos.order.payment"
    _description = "Pago manual de POS"

    # Correlativo interno (secuencia)
    name = fields.Char(
        string="Correlativo interno",
        readonly=True,
        copy=False,
        default=lambda self: _("New"),
    )

    pos_order_id = fields.Many2one(
        "pos.order",
        string="Orden POS",
        required=True,
        ondelete="cascade",
    )

    date = fields.Datetime(
        string="Fecha del pago",
        default=fields.Datetime.now,
        required=True,
    )

    payment_method_id = fields.Many2one(
        "pos.payment.method",
        string="Método de pago",
        required=True,
    )

    journal_id = fields.Many2one(
        "account.journal",
        string="Diario",
    )

    amount = fields.Monetary(
        string="Importe",
        required=True,
        currency_field="currency_id",
    )

    currency_id = fields.Many2one(
        "res.currency",
        string="Moneda",
        related="pos_order_id.pricelist_id.currency_id",
        store=True,
        readonly=True,
    )

    reference = fields.Char(
        string="Referencia",
    )

    note = fields.Text(
        string="Nota",
    )

    @api.model
    def create(self, vals):
        """Asignar secuencia al correlativo interno."""
        if not vals.get("name") or vals.get("name") == _("New"):
            # 1) Intentar usar la secuencia del módulo por xml_id
            seq = self.env.ref(
                "pos_order_manual_payment.seq_pos_order_manual_payment",
                raise_if_not_found=False,
            )
            if seq:
                vals["name"] = seq.next_by_id()
            else:
                # 2) Respaldo: usar el code por si acaso
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code("pos.order.payment")
                    or _("New")
                )
        return super().create(vals)
