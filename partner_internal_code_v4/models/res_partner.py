# -*- coding: utf-8 -*-
from odoo import api, fields, models

class ResPartner(models.Model):
    _inherit = "res.partner"

    internal_code = fields.Char(
        string="Código interno",
        index=True,
        copy=False,
        help="Código interno manual para identificar al contacto (cliente/proveedor)."
    )

    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        args = args or []
        if name:
            recs = self.search(["|", ("internal_code", operator, name), ("name", operator, name)] + args, limit=limit)
            if recs:
                return recs.name_get()
        return super().name_search(name=name, args=args, operator=operator, limit=limit)