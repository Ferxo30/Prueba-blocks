from odoo import models

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def button_cancel_remaining_delivery(self):
        for purchase in self:
            pickings = purchase.picking_ids.filtered(lambda p: p.picking_type_id.code == "incoming")
            to_cancel = pickings.filtered(lambda p: p.state in ("waiting", "confirmed", "assigned"))
            if to_cancel:
                to_cancel.action_cancel()
        return True
