# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Usuarios que podrán ver los cierres POS (POSS/…)
    pos_closing_allowed_user_ids = fields.Many2many(
        'res.users',
        string='Users allowed to see POS closing entries',
        help='Users selected here will be able to see POS session closing journal entries (POSS/...).',
    )

    @api.model
    def get_values(self):
        """Cargar usuarios que actualmente tienen el grupo."""
        res = super().get_values()
        group = self.env.ref(
            'pos_no_double_entry_for_invoiced_orders_fixed.group_pos_see_closing_moves',
            raise_if_not_found=False,
        )
        if group:
            res['pos_closing_allowed_user_ids'] = [(6, 0, group.users.ids)]
        return res

    def set_values(self):
        """Actualizar el grupo según lo que se seleccione en ajustes."""
        super().set_values()
        group = self.env.ref(
            'pos_no_double_entry_for_invoiced_orders_fixed.group_pos_see_closing_moves',
            raise_if_not_found=False,
        )
        if not group:
            return
        for settings in self:
            group.users = [(6, 0, settings.pos_closing_allowed_user_ids.ids)]
