from odoo import models

class PosOrder(models.Model):
    _inherit = "pos.order"

    def _prepare_invoice_vals(self):
        vals = super()._prepare_invoice_vals()
        # Detecta ambos nombres posibles en tu base
        order = self[:1]
        corr = False
        if order:
            if hasattr(order, "pos_internal_seq") and order.pos_internal_seq:
                corr = order.pos_internal_seq
            elif hasattr(order, "internal_pos_sequence") and order.internal_pos_sequence:
                corr = order.internal_pos_sequence
        if corr:
            vals["pos_internal_seq"] = corr
        return vals