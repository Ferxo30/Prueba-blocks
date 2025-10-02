
from odoo import api, fields, models

class ResPartner(models.Model):
    _inherit = "res.partner"

    partner_internal_code = fields.Char(
        string="Código interno",
        index=True,
        copy=False,
        help="Código interno para identificar al cliente/contacto. Debe ser único por compañía."
    )

    _sql_constraints = [
        ("partner_internal_code_uniq_company",
         "unique(partner_internal_code, company_id)",
         "El código interno del cliente debe ser único por compañía."),
    ]

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('partner_internal_code', operator, name), ('name', operator, name)]
        partners = self.search(domain + args, limit=limit)
        return partners.name_get()

    def name_get(self):
        res = []
        for p in self:
            label = p.name or ''
            if p.partner_internal_code:
                label = f"[{p.partner_internal_code}] {label}"
            res.append((p.id, label))
        return res
