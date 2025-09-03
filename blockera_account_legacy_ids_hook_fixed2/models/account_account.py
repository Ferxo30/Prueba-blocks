from odoo import models, fields, api

class AccountAccount(models.Model):
    _inherit = "account.account"

    old_code = fields.Char(string="Código antiguo", index=True)
    old_name = fields.Char(string="Nombre antiguo", index=True)
    legacy_source = fields.Selection(
        [("bloquera", "Bloquera"), ("ferreteria", "Ferretería")],
        string="Origen legacy"
    )
    legacy_notes = fields.Char(string="Notas legacy")

    _sql_constraints = [
        ("account_old_code_company_uniq",
         "unique(company_id, old_code)",
         "El código antiguo ya existe en esta compañía.")
    ]

    @api.model
    def name_search(self, name, args=None, operator="ilike", limit=100):
        args = args or []
        if name:
            domain = ["|", "|",
                      ("old_code", operator, name),
                      ("old_name", operator, name),
                      "|", ("code", operator, name), ("name", operator, name)]
            recs = self.search(domain + args, limit=limit)
            return recs.name_get()
        return super().name_search(name, args=args, operator=operator, limit=limit)