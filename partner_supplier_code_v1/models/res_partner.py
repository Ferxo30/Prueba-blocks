# -*- coding: utf-8 -*-
from odoo import api, models

class ResPartner(models.Model):
    _inherit = "res.partner"

    # ---------- Helpers ----------
    def _is_top_level_supplier(self):
        """Solo corre en el partner comercial (no hijos) y si es proveedor."""
        self.ensure_one()
        return self.supplier_rank > 0 and self.commercial_partner_id == self

    def _next_prv_code(self):
        return self.env['ir.sequence'].next_by_code('res.partner.vendor.code')

    def _assign_internal_code_for_supplier_if_needed(self):
        """Asigna PRV-xxxxx en internal_code SOLO si es proveedor y está vacío."""
        for partner in self:
            if partner._is_top_level_supplier() and not partner.internal_code:
                code = self._next_prv_code()
                if code:
                    # forzamos write aunque sea readonly en vista
                    partner.sudo().write({'internal_code': code})

    # ---------- Overrides ----------
    @api.model
    def create(self, vals):
        partner = super().create(vals)
        # Si al crear ya es proveedor, asignamos
        partner._assign_internal_code_for_supplier_if_needed()
        return partner

    def write(self, vals):
        # memoriza supplier_rank previo para detectar el cambio 0 -> >0
        prev = {p.id: p.supplier_rank for p in self}
        res = super().write(vals)
        for p in self:
            if (prev.get(p.id, 0) == 0 and p.supplier_rank > 0) or 'supplier_rank' in vals:
                p._assign_internal_code_for_supplier_if_needed()
        return res



    # ---------- Búsqueda por código o nombre (opcional) ----------
    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        args = args or []
        if name:
            recs = self.search(["|", ("internal_code", operator, name), ("name", operator, name)] + args, limit=limit)
            if recs:
                return recs.name_get()
        return super().name_search(name=name, args=args, operator=operator, limit=limit)
