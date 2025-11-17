# -*- coding: utf-8 -*-
from odoo import fields, models

class PosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    is_customer_account = fields.Boolean(
        string='Es cuenta de cliente',
        help='Marcar este método cuando represente pagos a cuenta/credito de cliente.',
        default=False,
    )
