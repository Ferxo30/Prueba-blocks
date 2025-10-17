# -*- coding: utf-8 -*-
from odoo import fields, models

class AccountJournal(models.Model):
    _inherit = "account.journal"

    direct_liquidity_on_payment = fields.Boolean(
        string="Postear pagos directamente a banco",
        help=(
            "Si está activo, los pagos registrados con este diario "
            "usan la cuenta de liquidez del diario en lugar de 'Pagos pendientes'."
        ),
        default=True,
    )
