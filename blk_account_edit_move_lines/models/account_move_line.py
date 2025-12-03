# -*- coding: utf-8 -*-
from odoo import models, fields


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    # Quitamos el "readonly duro" de account_id a nivel de modelo.
    # El resto de atributos (domain, required, states, etc.) se heredan del original.
    account_id = fields.Many2one(readonly=False)
