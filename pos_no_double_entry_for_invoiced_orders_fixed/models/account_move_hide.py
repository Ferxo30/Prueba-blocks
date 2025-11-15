# -*- coding: utf-8 -*-
from odoo import api, fields, models

# =======================================================
#  ASIENTOS: flag calculado y ALMACENADO para cerrar la
#  puerta en TODAS las rutas de lectura/búsqueda.
#  True  -> es un asiento de cierre POS (POSS/…)
#  False -> cualquier otro
# =======================================================
class AccountMove(models.Model):
    _inherit = 'account.move'

    is_poss_move = fields.Boolean(
        string='POS Closing Entry',
        compute='_compute_is_poss_move',
        store=True,
        index=True,
    )

    @api.depends('name')
    def _compute_is_poss_move(self):
        for rec in self:
            name = (rec.name or '').upper()
            rec.is_poss_move = name.startswith('POSS/')


# =======================================================
#  APUNTES: fix para ocultar líneas de cierres POS
# =======================================================
class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    def _pos_hide_move_lines_domain(self):
        """Excluir líneas si el asiento es de cierre POS.

        Permitimos también move_id = False para no romper líneas
        sueltas (ej. borradores raros).
        """
        return ['|', ('move_id', '=', False), ('move_id.is_poss_move', '=', False)]

    @api.model
    def search(self, args=None, offset=0, limit=None, order=None, count=False):
        args = list(args or [])
        args += self._pos_hide_move_lines_domain()
        if count:
            return super(AccountMoveLine, self).search_count(args)
        return super(AccountMoveLine, self).search(
            args, offset=offset, limit=limit, order=order
        )

    @api.model
    def search_count(self, args=None, limit=None):  # aceptar limit e ignorarlo
        args = list(args or [])
        args += self._pos_hide_move_lines_domain()
        return super(AccountMoveLine, self).search_count(args)

    def read_group(self, domain, fields, groupby,
                   offset=0, limit=None, orderby=False, lazy=True):
        domain = list(domain or [])
        domain += self._pos_hide_move_lines_domain()
        return super(AccountMoveLine, self).read_group(
            domain, fields, groupby,
            offset=offset, limit=limit, orderby=orderby, lazy=lazy
        )

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = list(args or [])
        args += self._pos_hide_move_lines_domain()
        return super(AccountMoveLine, self).name_search(
            name=name, args=args, operator=operator, limit=limit
        )
