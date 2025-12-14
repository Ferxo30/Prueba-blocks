# -*- coding: utf-8 -*-
import json
from odoo import api, models, _
from odoo.exceptions import UserError


class ProductProduct(models.Model):
    _inherit = "product.product"

    def _swir_get_active_domain(self):
        ctx = self.env.context
        # Odoo suele pasar el dominio con alguna de estas llaves dependiendo del flujo
        domain = ctx.get("active_domain") or ctx.get("domain") or ctx.get("search_domain") or []
        return domain

    def _swir_get_to_date_from_context(self):
        ctx = self.env.context
        # Inventario a la fecha (según configuración/versión puede variar)
        return ctx.get("to_date") or ctx.get("inventory_datetime") or ctx.get("history_date") or False

    def _swir_get_default_warehouse_ids_from_context(self):
        ctx = self.env.context
        wid = (
            ctx.get("warehouse_id")
            or ctx.get("default_warehouse_id")
            or ctx.get("search_default_warehouse_id")
        )
        if wid:
            return [wid]
        return []

    def action_swir_open_wizard_pdf(self):
        return self._swir_open_wizard(default_output="pdf")

    def action_swir_open_wizard_xlsx(self):
        return self._swir_open_wizard(default_output="xlsx")

    def _swir_open_wizard(self, default_output="pdf"):
        domain = self._swir_get_active_domain()
        to_date = self._swir_get_to_date_from_context()
        warehouse_ids = self._swir_get_default_warehouse_ids_from_context()

        # Validación básica: si no hay dominio y tampoco active_ids, igual se puede
        # (el wizard permitirá todas las existencias), pero normalmente sí hay.
        wiz = self.env["stock.warehouse.inventory.report.wizard"].create({
            "domain_json": json.dumps(domain or []),
            "to_date": to_date,
        })
        if warehouse_ids:
            wiz.warehouse_ids = [(6, 0, warehouse_ids)]

        action = wiz.action_open_form()
        action["context"] = dict(self.env.context, default_output=default_output)
        return action
