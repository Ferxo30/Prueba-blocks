# -*- coding: utf-8 -*-

from odoo import fields, models


class PosOrderPayment(models.Model):
    _inherit = "pos.order.payment"

    master_id = fields.Many2one(
        comodel_name="pos.order.payment.master",
        string="Pago maestro",
        ondelete="set null",
        index=True,
    )
