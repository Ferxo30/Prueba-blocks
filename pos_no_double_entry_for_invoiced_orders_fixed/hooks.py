# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID

def set_is_poss_move_flag(cr, registry):
    """Marca retroactivamente los asientos POSS/ como is_poss_move = TRUE."""
    cr.execute("""
        UPDATE account_move
           SET is_poss_move = TRUE
         WHERE name IS NOT NULL
           AND UPPER(name) LIKE 'POSS/%'
    """)
    cr.execute("""
        UPDATE account_move
           SET is_poss_move = FALSE
         WHERE is_poss_move IS DISTINCT FROM FALSE
           AND (name IS NULL OR UPPER(name) NOT LIKE 'POSS/%')
    """)

    # invalidar caches para que la regla de registros tome efecto de inmediato
    env = api.Environment(cr, SUPERUSER_ID, {})
    env['account.move'].clear_caches()
