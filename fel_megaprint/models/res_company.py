
# -*- coding: utf-8 -*-

from odoo import models, fields

class ResCompany(models.Model):
    _inherit = "res.company"

    certificador_fel = fields.Selection([
        ('megaprint', 'Megaprint'),
        ('otro_certificador', 'Otro Certificador'),
    ], string='Certificador FEL', default='megaprint')
