# -*- coding: utf-8 -*-
from odoo import models, api, _
from odoo.exceptions import UserError

class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_force_cancel_to_draft(self):
        """
        For Accounting Managers:
        - If move is posted, un-reconcile all move lines.
        - Try to cancel if needed.
        - Set to draft.
        Notes:
        * Doesn't delete payments; only breaks reconciliations.
        * Will still respect period locks and company rules.
        """
        for move in self:
            # Only allow on non-entry and not already in draft
            if move.state == 'draft':
                continue

            # 1) Un-reconcile
            for line in move.line_ids:
                # remove_move_reconcile handles both full & partial
                line.remove_move_reconcile()

            # 2) If posted, try cancel
            if move.state == 'posted':
                # Odoo 18 uses button_cancel on account.move
                try:
                    move.button_cancel()
                except Exception as e:
                    # If some custom modules changed the flow, still attempt fallback
                    raise UserError(_('No se pudo cancelar el asiento antes de pasar a borrador: %s') % (e,))

            # 3) Back to draft
            try:
                # Odoo 18
                move.button_draft()
            except AttributeError:
                # Some backports/variants name it action_draft
                move.action_draft()

        return True