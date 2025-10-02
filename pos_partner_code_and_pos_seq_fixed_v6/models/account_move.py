from odoo import fields, models

class AccountMove(models.Model):
    _inherit = "account.move"

    pos_internal_seq = fields.Char(
        string="Correlativo interno POS",
        index=True,
        copy=False,
        help="Correlativo interno asignado por el POS (ej. A-002).",
    )