# -*- coding: utf-8 -*-
# from odoo import models

#class PosSession(models.Model):
 #   _inherit = 'pos.session'

 #   def _get_pos_ui_partner_fields(self):
  #      """Añadimos internal_code a la lista de campos que se cargan al POS."""
   #     fields = super()._get_pos_ui_partner_fields()
    #    if 'internal_code' not in fields:
     #       fields.append('internal_code')
      #  return fields

#    def _loader_params_res_partner(self):
#        """Por si acaso, también lo inyectamos en los search_params."""
#        res = super()._loader_params_res_partner()
#        search_params = res.get('search_params', {}) or {}
#        fields = search_params.get('fields', []) or []
#        if 'internal_code' not in fields:
#            fields.append('internal_code')
#        search_params['fields'] = fields
#        res['search_params'] = search_params
#        return res
