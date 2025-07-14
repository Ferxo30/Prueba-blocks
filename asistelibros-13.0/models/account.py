# -*- coding: utf-8 -*-

from odoo import api, exceptions, fields, models, _
import logging

class AccountMove(models.Model):
    _inherit = "account.move"

    fauca = fields.Char('FAUCA')
    dua = fields.Char('DUA')
    cadi = fields.Char('CADI')
    cexe = fields.Char('CEXE')
    criva = fields.Char('CRIVA')
    valor_constancia = fields.Float('Valor de constancia')
