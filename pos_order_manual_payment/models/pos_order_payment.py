# -*- coding: utf-8 -*-
from odoo import api, fields, models


class PosOrderPayment(models.Model):
    _name = "pos.order.payment"
    _description = "Pago manual de POS"

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

