# -*- coding: utf-8 -*-
from odoo import models, _
from odoo.exceptions import UserError

class PosSession(models.Model):
    _inherit = "pos.session"



    def action_force_close_session(self):
        """Abre el wizard si la configuración lo permite."""
        self.ensure_one()
        if not self.config_id.allow_force_close:
            raise UserError(_("Activa 'Permitir cierre forzado' en la Configuración del PdV."))

        # Reunimos movimientos vinculados a la sesión que no estén 'posted'
        moves = self._get_blocking_moves()
        if not moves:
            # Si no hay nada que bloquee, intentamos cerrar normal
            try:
                return self.action_pos_session_closing_control()
            except UserError:
                # Si por cualquier motivo sigue fallando, abrimos wizard
                pass

        return {
            "type": "ir.actions.act_window",
            "name": _("Forzar cierre de sesión"),
            "res_model": "pos.force.close.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_session_id": self.id,
                "default_count_draft": len(moves.filtered(lambda m: m.state == "draft")),
                "default_count_cancel": len(moves.filtered(lambda m: m.state == "cancel")),
            },
        }

    def _get_blocking_moves(self):
        """Devuelve las facturas (account.move) vinculadas a la sesión vía pos.order.account_move
        que no están publicadas (state in draft/cancel)."""
        self.ensure_one()
        Order = self.env["pos.order"].sudo()
        Move = self.env["account.move"].sudo()

        # Todas las órdenes de la sesión
        orders = Order.search([("session_id", "=", self.id)])

        # Toma los moves desde los campos estándar (según versión/instalación)
        move_ids = set()
        # v16+ normalmente usa 'account_move'
        move_ids.update([m.id for m in orders.mapped("account_move") if m])
        # por robustez si tu custom tiene 'account_move_id'
        if "account_move_id" in Order._fields:
            move_ids.update([m.id for m in orders.mapped("account_move_id") if m])

        if not move_ids:
            return Move.browse([])

        moves = Move.search([
            ("id", "in", list(move_ids)),
            ("move_type", "in", ("out_invoice", "out_refund")),
            ("state", "in", ("draft", "cancel")),
        ])
        return moves


    def _try_close_after_cleanup(self):
        """Intenta cerrar de nuevo y si sigue fallando, muestra el error original."""
        self.ensure_one()
        return self.action_pos_session_closing_control()
