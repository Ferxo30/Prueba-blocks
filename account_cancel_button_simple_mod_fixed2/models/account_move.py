
from odoo import models

class AccountMoveForceCancel(models.Model):
    _inherit = "account.move"

    def button_cancel(self):
        """Force-cancel the move regardless of its current state.
        Best-effort: tries to revert to draft, clears reconciliations, then sets state=cancel.
        WARNING: This bypasses normal accounting safeguards. Use with caution.
        """
        for move in self.sudo():
            # Try to remove reconciliations to avoid blockers
            try:
                # Odoo >=13 has remove_move_reconcile on aml records
                move.line_ids.remove_move_reconcile()
            except Exception:
                pass

            # Try to bring back to draft first (safer path)
            if move.state == "posted":
                try:
                    move.button_draft()
                except Exception:
                    # Fallback: write with lenient context if button_draft is blocked
                    try:
                        move.with_context(skip_account_move_synchronization=True, bypass_workflow=True).write({"state": "draft"})
                    except Exception:
                        pass

            # Finally, force cancel state ignoring validity checks
            try:
                move.with_context(check_move_validity=False, bypass_workflow=True).write({"state": "cancel"})
            except Exception:
                # Last resort: direct write
                move.write({"state": "cancel"})
        return True
