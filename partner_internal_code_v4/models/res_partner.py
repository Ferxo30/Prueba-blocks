# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = "res.partner"

    # ----------------- Campo y constraint -----------------
    internal_code = fields.Char(
        string="Código interno",
        index=True,
        copy=False,
        readonly=True,
        help="Código interno secuencial exclusivo para clientes.",
    )

    _sql_constraints = [
        (
            "unique_internal_code",
            "unique(internal_code)",
            "El código interno debe ser único.",
        ),
    ]

    # ----------------- Helpers -----------------
    def _is_top_level_customer(self):
        """Solo clientes (customer_rank>0) y solo el partner comercial principal."""
        self.ensure_one()
        return self.customer_rank > 0 and self.commercial_partner_id == self

    def _next_internal_code(self):
        """Single-company: usa la secuencia global por code."""
        return self.env["ir.sequence"].next_by_code("res.partner.internal.code")

    def _assign_internal_code_if_needed(self):
        """Asigna código si aplica (solo clientes top-level, sin código aún)."""
        for partner in self:
            if not partner.internal_code and partner._is_top_level_customer():
                code = partner._next_internal_code()
                partner.with_context(skip_internal_code_guard=True).write(
                    {"internal_code": code}
                )

    # ----------------- Overrides create / write -----------------
    @api.model
    def create(self, vals):
        partner = super().create(vals)
        partner._assign_internal_code_if_needed()
        return partner

    def write(self, vals):
        prev_ranks = {p.id: p.customer_rank for p in self}
        res = super().write(vals)
        for p in self:
            # Si antes no era cliente y ahora sí, asignar código
            if prev_ranks.get(p.id, 0) == 0 and p.customer_rank > 0:
                p._assign_internal_code_if_needed()
        return res

    # ----------------- Búsqueda por código o nombre -----------------
    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        args = args or []
        if name:
            recs = self.search(
                ["|", ("internal_code", operator, name), ("name", operator, name)]
                + args,
                limit=limit,
            )
            if recs:
                return recs.name_get()
        return super().name_search(name=name, args=args, operator=operator, limit=limit)

    # ----------------- Acción masiva para asignar códigos -----------------
    def action_assign_internal_code(self):
        """Asigna código interno al/los partner(s) seleccionados si aplica."""
        count = 0
        for p in self:
            # Solo al partner comercial (no direcciones) y solo clientes sin código
            if (
                p.customer_rank > 0
                and not p.internal_code
                and p.commercial_partner_id == p
            ):
                p._assign_internal_code_if_needed()
                count += 1
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Códigos internos"),
                "message": _("Asignados: %s") % count,
                "sticky": False,
                "type": "success",
            },
        }

    # ----------------- Campos que viajan al POS -----------------
    @api.model
    def _load_pos_data_fields(self, config_id):
        """
        Extiende los campos de partner que se envían al POS para incluir internal_code.
        Odoo 18 usa este método para decidir qué campos cargar al frontend.
        """
        fields_list = super()._load_pos_data_fields(config_id)
        if "internal_code" not in fields_list:
            fields_list.append("internal_code")
        return fields_list
