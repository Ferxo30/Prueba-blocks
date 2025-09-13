from odoo import models, _
from odoo.exceptions import UserError

EPSILON = 1e-6

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def _has_posted_vendor_bills(self):
        self.ensure_one()
        moves = self.env["account.move"].search([
            ("move_type", "in", ("in_invoice", "in_refund")),
            ("state", "=", "posted"),
            ("invoice_line_ids.purchase_line_id.order_id", "=", self.id),
        ], limit=1)
        return bool(moves)

    def _net_received_is_zero(self):
        self.ensure_one()
        for line in self.order_line:
            qty = line.qty_received or 0.0
            if abs(qty) > EPSILON:
                return False
        return True

    def _cancel_open_pickings(self):
        open_pickings = self.picking_ids.filtered(lambda p: p.state in ("waiting", "confirmed", "assigned"))
        if open_pickings:
            open_pickings.action_cancel()

    def action_force_cancel_only(self):
        for po in self:
            if po.state not in ("purchase", "done", "to approve"):
                raise UserError(_("La orden debe estar confirmada/aprobada para forzar la cancelación."))
            if po._has_posted_vendor_bills():
                raise UserError(_("No se puede forzar: hay facturas de proveedor posteadas vinculadas."))
            if not po._net_received_is_zero():
                raise UserError(_("No se puede forzar: el neto recibido no es cero. "
                                  "Primero registra la devolución hasta compensar las recepciones."))
            po._cancel_open_pickings()
            try:
                po.button_cancel()
            except Exception:
                po.write({"state": "cancel"})
        return True

    def action_force_cancel_and_delete(self):
        self.action_force_cancel_only()
        for po in self:
            po.unlink()
        return True
