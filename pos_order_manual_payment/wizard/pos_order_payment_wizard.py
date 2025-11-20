# -*- coding: utf-8 -*-
from odoo import api, fields, models


class PosOrderPaymentWizard(models.TransientModel):
    _name = "pos.order.payment.wizard"
    _description = "Wizard pago manual POS"

    pos_order_id = fields.Many2one(
        "pos.order",
        string="Orden POS",
        required=True,
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

    def action_confirm(self):
        self.ensure_one()
        self.env["pos.order.payment"].create({
            "pos_order_id": self.pos_order_id.id,
            "date": self.date,
            "payment_method_id": self.payment_method_id.id,
            "journal_id": self.journal_id.id,
            "amount": self.amount,
            "reference": self.reference,
            "note": self.note,
        })
        return {"type": "ir.actions.act_window_close"}
