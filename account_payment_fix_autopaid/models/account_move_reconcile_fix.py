from odoo import models, api, fields

class AccountMoveReconcileFix(models.Model):
    _inherit = 'account.move'

    @api.model
    def write(self, vals):
        """Reconciliación automática y forzado de estado pagado al editar un asiento de pago."""
        res = super().write(vals)

        for move in self:
            if 'payment_id' not in move._fields or not move.payment_id:
                continue

            payment = move.payment_id

            # --- 1️⃣ Forzar estado del pago
            if payment.state != 'posted':
                payment.state = 'posted'
            payment.payment_state = 'paid'

            # --- 2️⃣ Intentar recuperar facturas vinculadas (por reconciliación o referencia)
            invoices = payment.reconciled_invoice_ids
            if not invoices and payment.ref:
                invoices = self.env['account.move'].search([
                    ('payment_reference', '=', payment.ref),
                    ('move_type', 'in', ['out_invoice', 'in_invoice']),
                ])

            # --- 3️⃣ Reconciliar líneas automáticamente
            for inv in invoices:
                # Buscar líneas conciliables (mismo partner, misma cuenta)
                pay_lines = payment.move_id.line_ids.filtered(lambda l: l.account_id.reconcile and l.partner_id == inv.partner_id)
                inv_lines = inv.line_ids.filtered(lambda l: l.account_id.reconcile and l.partner_id == inv.partner_id)

                lines_to_rec = pay_lines + inv_lines
                if len(lines_to_rec) >= 2:
                    try:
                        lines_to_rec.reconcile()
                    except Exception:
                        pass

                # --- 4️⃣ Forzar estado de factura
                if inv.state == 'posted':
                    inv.payment_state = 'paid'
                    if hasattr(inv, 'invoice_payment_state'):
                        inv.invoice_payment_state = 'paid'
                    if hasattr(inv, 'amount_residual'):
                        inv.amount_residual = 0.0

        return res
