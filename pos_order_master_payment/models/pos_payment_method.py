# -*- coding: utf-8 -*-

from odoo import models
from odoo.osv import expression


class PosPaymentMethod(models.Model):
    _inherit = "pos.payment.method"

    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if self.env.context.get('force_non_customer_account_methods'):
            args = list(args or [])
            # Forzar exclusión de "Cuenta de cliente" sin importar otros filtros externos
            forced = [('active', '=', True), ('is_customer_account', '=', False)]
            domain = expression.AND([args, forced])
            if name:
                domain = expression.AND([domain, [('name', operator, name)]])
            recs = self.search(domain, limit=limit)
            return recs.name_get()

        return super().name_search(name=name, args=args, operator=operator, limit=limit)
