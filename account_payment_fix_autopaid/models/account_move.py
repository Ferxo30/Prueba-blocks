from odoo import models, api, fields
import time

class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_post(self):
        res = super().action_post()

        for move in self:
            # Solo aplicar si es asiento de pago con partner
            if move.move_type != 'entry' or not move.partner_id:
                continue

            payment = getattr(move, 'payment_id', False)
            partner = move.partner_id

            # Esperar un instante para asegurar que el posteo terminó
            time.sleep(0.5)

            # Buscar líneas de crédito del cliente (créditos disponibles)
            credit_lines = self.env['account.move.line'].search([
                ('partner_id', '=', partner.id),
                ('account_id.reconcile', '=', True),
                ('amount_residual', '>', 0),
                ('move_id.state', '=', 'posted'),
                ('credit', '>', 0),
            ])

            # Buscar facturas abiertas del cliente
            invoices = self.env['account.move'].search([
                ('partner_id', '=', partner.id),
                ('move_type', 'in', ['out_invoice']),
                ('state', '=', 'posted'),
                ('payment_state', 'not in', ['paid', 'in_payment']),
            ])

            for inv in invoices:
                lines_invoice = inv.line_ids.filtered(lambda l: l.account_id.reconcile)
                for line_credit in credit_lines:
                    try:
                        (lines_invoice + line_credit).reconcile()
                    except Exception:
                        pass

                # Forzar pago
                inv.payment_state = 'paid'
                if hasattr(inv, 'invoice_payment_state'):
                    inv.invoice_payment_state = 'paid'
                inv.amount_residual = 0.0

        return res
