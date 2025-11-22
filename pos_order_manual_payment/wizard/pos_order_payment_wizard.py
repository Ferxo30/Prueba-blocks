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

    available_payment_method_ids = fields.Many2many(
        "pos.payment.method",
        string="Métodos de pago disponibles",
        compute="_compute_available_payment_method_ids",
    )

    @api.depends("pos_order_id")
    def _compute_available_payment_method_ids(self):
        for wizard in self:
            methods = self.env["pos.payment.method"]
            order = wizard.pos_order_id
            if order:
                # Intentar obtener la config desde la sesión o desde config_id (según versión)
                config = order.session_id.config_id or getattr(order, "config_id", False)
                if config:
                    methods = config.payment_method_ids
            wizard.available_payment_method_ids = methods

    payment_method_id = fields.Many2one(
        "pos.payment.method",
        string="Método de pago",
        required=True,
        domain="[('id', 'in', available_payment_method_ids)]",
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
