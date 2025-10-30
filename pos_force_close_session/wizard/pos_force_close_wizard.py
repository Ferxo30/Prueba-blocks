# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class PosForceCloseWizard(models.TransientModel):
    _name = "pos.force.close.wizard"
    _description = "Forzar cierre de sesión de PdV"

    session_id = fields.Many2one("pos.session", required=True, ondelete="cascade")
    action_mode = fields.Selection(
        [
            ("post", "Publicar todas las facturas en borrador"),
            ("cancel_unlink", "Anular y desvincular de la sesión"),
        ],
        string="Acción a ejecutar",
        default="cancel_unlink",
        required=True,
        help=(
            "• Publicar: intentará publicar todas las facturas en borrador.\n"
            "• Anular y desvincular: pondrá en cancel las facturas en borrador y quitará "
            "la relación con la sesión; las ya 'cancel' sólo se desvinculan."
        ),
    )
    count_draft = fields.Integer(readonly=True)
    count_cancel = fields.Integer(readonly=True)

    def action_apply(self):
        self.ensure_one()
        session = self.session_id.sudo()
        moves = session._get_blocking_moves().sudo()

        if not moves:
            return session._try_close_after_cleanup()

        # 1) Si el modo es 'post', intentamos publicar todos los draft
        if self.action_mode == "post":
            drafts = moves.filtered(lambda m: m.state == "draft")
            if drafts:
                # Publica facturas (puede fallar si faltan datos/impuestos/partner)
                drafts._post()

            # Tras publicar, reobtén bloqueadores (para ver si solo quedan cancel)
            moves = session._get_blocking_moves().sudo()

       # 2) Para lo que quede en 'draft' o 'cancel' => cancelar (si draft) y DESVINCULAR desde pos.order
        to_unlink = moves

        # Cancela borradores (los deja en 'cancel')
        drafts = to_unlink.filtered(lambda m: m.state == "draft")
        if drafts:
            drafts.button_cancel()

        # Quita el vínculo a la factura desde los pedidos POS de la sesión
        orders = self.env["pos.order"].sudo().search([("session_id", "=", session.id)])
        # Filtra solo los que apuntan a estas facturas
        orders_to_clear = orders.filtered(
            lambda o: (o.account_move and o.account_move.id in to_unlink.ids) or
                    ("account_move_id" in o._fields and o.account_move_id and o.account_move_id.id in to_unlink.ids)
        )

        vals_clear = {}
        if "account_move" in orders._fields:
            vals_clear["account_move"] = False
        if "account_move_id" in orders._fields:
            vals_clear["account_move_id"] = False
        if vals_clear and orders_to_clear:
            orders_to_clear.write(vals_clear)

        # Intentar cerrar nuevamente
        return session._try_close_after_cleanup()
