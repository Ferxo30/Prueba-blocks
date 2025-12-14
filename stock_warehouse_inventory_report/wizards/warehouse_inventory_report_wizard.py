# -*- coding: utf-8 -*-
import io
import json
import base64
import xlsxwriter

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class StockWarehouseInventoryReportWizard(models.TransientModel):
    _name = "stock.warehouse.inventory.report.wizard"
    _description = "Reporte existencias por bodega (a una fecha) PDF/XLSX"

    to_date = fields.Datetime(string="Inventario a la fecha")
    warehouse_ids = fields.Many2many("stock.warehouse", string="Bodegas")
    price_basis = fields.Selection(
        [("standard_price", "Costo (standard_price)"), ("list_price", "Precio de venta (list_price)")],
        string="Precio a usar",
        default="standard_price",
        required=True,
    )
    include_zero = fields.Boolean(string="Incluir saldo 0", default=True)
    include_negative = fields.Boolean(string="Incluir negativos", default=True)

    domain_json = fields.Text(string="Dominio (filtros actuales)")
    line_ids = fields.One2many(
        "stock.warehouse.inventory.report.wizard.line",
        "wizard_id",
        string="Líneas",
        readonly=True,
    )

    file_data = fields.Binary(string="Archivo", readonly=True)
    file_name = fields.Char(string="Nombre de archivo", readonly=True)

    def action_open_form(self):
        return {
            "type": "ir.actions.act_window",
            "name": _("Imprimir existencias por bodega"),
            "res_model": self._name,
            "view_mode": "form",
            "res_id": self.id,
            "target": "new",
        }

    def _get_products_from_domain(self):
        domain = []
        if self.domain_json:
            try:
                domain = json.loads(self.domain_json) or []
            except Exception:
                domain = []
        # El reporte original es sobre product.product (Variante del producto)
        products = self.env["product.product"].search(domain)
        return products

    def _get_warehouses(self):
        whs = self.warehouse_ids
        if not whs:
            whs = self.env["stock.warehouse"].search([("company_id", "=", self.env.company.id)])
        return whs

    def _compute_qty_available(self, products, location_id, to_date):
        """
        Intenta usar cómputo batch si existe; si no, cae a qty_available con contexto.
        """
        ctx = dict(self.env.context, location=location_id)
        if to_date:
            ctx["to_date"] = to_date

        # Intento batch (varía por versión); fallback seguro
        qty_map = {}
        try:
            # En muchas versiones existe _compute_quantities_dict
            qdict = products.with_context(ctx)._compute_quantities_dict(to_date=to_date)
            for pid, vals in qdict.items():
                qty_map[pid] = vals.get("qty_available", 0.0)
            return qty_map
        except Exception:
            for p in products:
                qty_map[p.id] = p.with_context(ctx).qty_available
            return qty_map

    def action_compute_lines(self):
        self.ensure_one()
        self.line_ids.unlink()

        products = self._get_products_from_domain()
        if not products:
            raise UserError(_("No hay productos para imprimir con los filtros actuales."))

        whs = self._get_warehouses()
        if not whs:
            raise UserError(_("No hay bodegas configuradas."))

        lines = []
        for wh in whs:
            location_id = wh.view_location_id.id
            qty_map = self._compute_qty_available(products, location_id, self.to_date)

            for p in products:
                qty = float(qty_map.get(p.id, 0.0))
                if not self.include_zero and qty == 0.0:
                    continue
                if not self.include_negative and qty < 0.0:
                    continue

                unit_price = p.standard_price if self.price_basis == "standard_price" else p.list_price
                total = qty * unit_price

                lines.append((0, 0, {
                    "warehouse_name": wh.name,
                    "warehouse_code": wh.code or "",
                    "product_code": p.default_code or "",
                    "product_name": p.display_name,
                    "qty": qty,
                    "unit_price": unit_price,
                    "total": total,
                }))

        self.write({"line_ids": lines})
        return True

    def action_print_pdf(self):
        self.ensure_one()
        if not self.line_ids:
            self.action_compute_lines()
        return self.env.ref("stock_warehouse_inventory_report.action_swir_pdf").report_action(self)

    def action_export_xlsx(self):
        self.ensure_one()
        if not self.line_ids:
            self.action_compute_lines()

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {"in_memory": True})
        sheet = workbook.add_worksheet("Saldos")

        fmt_title = workbook.add_format({"bold": True, "align": "center", "valign": "vcenter"})
        fmt_hdr = workbook.add_format({"bold": True, "border": 1})
        fmt_cell = workbook.add_format({"border": 1})
        fmt_num = workbook.add_format({"border": 1, "num_format": "#,##0.00"})
        fmt_money = workbook.add_format({"border": 1, "num_format": "#,##0.00"})

        company = self.env.company.name or ""
        date_txt = fields.Datetime.to_string(self.to_date) if self.to_date else ""

        # Encabezado estilo “reporte”
        sheet.merge_range(0, 2, 0, 6, company, fmt_title)
        sheet.merge_range(1, 2, 1, 6, "Saldos por Bodega", fmt_title)
        sheet.merge_range(2, 2, 2, 6, f"Inventario a la fecha: {date_txt}", fmt_title)

        headers = ["BODEGA", "COD BOD", "COD", "PRODUCTO", "SALDO", "PRECIO", "TOTAL"]
        for col, h in enumerate(headers):
            sheet.write(4, col, h, fmt_hdr)

        row = 5
        for l in self.line_ids:
            sheet.write(row, 0, l.warehouse_name, fmt_cell)
            sheet.write(row, 1, l.warehouse_code, fmt_cell)
            sheet.write(row, 2, l.product_code, fmt_cell)
            sheet.write(row, 3, l.product_name, fmt_cell)
            sheet.write_number(row, 4, l.qty, fmt_num)
            sheet.write_number(row, 5, l.unit_price, fmt_money)
            sheet.write_number(row, 6, l.total, fmt_money)
            row += 1

        # Anchos
        sheet.set_column(0, 0, 22)
        sheet.set_column(1, 1, 10)
        sheet.set_column(2, 2, 14)
        sheet.set_column(3, 3, 40)
        sheet.set_column(4, 6, 14)

        workbook.close()
        output.seek(0)

        filename = "saldos_por_bodega.xlsx"
        self.write({
            "file_name": filename,
            "file_data": base64.b64encode(output.read()),
        })

        return {
            "type": "ir.actions.act_url",
            "url": f"/web/content/?model={self._name}&id={self.id}&field=file_data&filename_field=file_name&download=true",
            "target": "self",
        }


class StockWarehouseInventoryReportWizardLine(models.TransientModel):
    _name = "stock.warehouse.inventory.report.wizard.line"
    _description = "Líneas reporte existencias por bodega"

    wizard_id = fields.Many2one("stock.warehouse.inventory.report.wizard", required=True, ondelete="cascade")

    warehouse_name = fields.Char(readonly=True)
    warehouse_code = fields.Char(readonly=True)

    product_code = fields.Char(readonly=True)
    product_name = fields.Char(readonly=True)

    qty = fields.Float(readonly=True)
    unit_price = fields.Float(readonly=True)
    total = fields.Float(readonly=True)
