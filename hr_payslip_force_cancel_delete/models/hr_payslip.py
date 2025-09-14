from odoo import models, _
from odoo.exceptions import UserError

EPSILON = 1e-6

class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    def _get_linked_move(self):
        """Return an account.move linked to this payslip if present (posted or not)."""
        self.ensure_one()
        move = getattr(self, 'move_id', False) or getattr(self, 'account_move_id', False)
        return move

    def _has_posted_moves(self):
        self.ensure_one()
        Move = self.env['account.move']
        move = self._get_linked_move()
        if move and move.state == 'posted':
            return True
        # Defensive search by reference fields
        ref_vals = set(filter(None, [getattr(self, 'number', None), self.name, self.display_name]))
        if ref_vals:
            dom = [('state', '=', 'posted'), ('ref', 'in', list(ref_vals))]
            if Move.search(dom, limit=1):
                return True
        return False

    def _cancel_draft_moves(self):
        for slip in self:
            move = slip._get_linked_move()
            if move and move.state != 'posted':
                try:
                    if hasattr(move, 'button_cancel'):
                        move.button_cancel()
                except Exception:
                    pass
                try:
                    move.unlink()
                except Exception:
                    pass

    def action_force_cancel_only(self):
        for slip in self:
            if slip.state in ('cancel',):
                continue
            if slip._has_posted_moves():
                raise UserError(_("No se puede forzar: existen asientos contables posteados vinculados a esta nómina. "
                                  "Primero anule/revierta esos asientos."))
            slip._cancel_draft_moves()
            try:
                if hasattr(slip, 'action_payslip_cancel'):
                    slip.action_payslip_cancel()
                else:
                    slip.write({'state': 'cancel'})
            except Exception:
                slip.write({'state': 'cancel'})
        return True

    def action_force_cancel_and_delete(self):
        self.action_force_cancel_only()
        for slip in self:
            try:
                if hasattr(slip, 'payslip_run_id') and slip.payslip_run_id:
                    slip.write({'payslip_run_id': False})
            except Exception:
                pass
            slip.unlink()
        return True
