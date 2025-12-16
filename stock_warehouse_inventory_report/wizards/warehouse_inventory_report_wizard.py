# -*- coding: utf-8 -*-
import io
import json
import base64
import xlsxwriter

from odoo import fields, models, _
from odoo.exceptions import UserError


class StockWarehouseInventoryReportWizard(models.TransientModel):
    _name = "stock.warehouse.inventory.report.wizard"
    _description = "Reporte existencias por bodega (a una fecha) PDF/XLSX"

    to_date = fields.Datetime(string="Inventario a la fecha")
    warehouse_ids = fields.Many2many("stock.warehouse", string="Bodegas")

    include_zero = fields.Boolean(string="Incluir saldo 0", default=True)
    include_negative = fields.Boolean(string="Incluir negativos", default=True)

    domain_json = fields.Text(string="Dominio (filtros actuales)")
    line_ids = fields.One2many(
        "stock.warehouse.inventory.report.wizard.line",
        "wizard_id",
        string="Líneas",
        readonly=True,
    )

    total_qty = fields.Float(string="Total saldo", readonly=True)
    total_value = fields.Float(string="Total neto", readonly=True)

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
        return self.env["product.product"].search(domain)

    def _get_warehouses(self):
        whs = self.warehouse_ids
        if not whs:
            whs = self.env["stock.warehouse"].search([("company_id", "=", self.env.company.id)])
        return whs

    def _compute_qty_available(self, products, location_id, to_date):
        ctx = dict(self.env.context, location=location_id)
        if to_date:
            ctx["to_date"] = to_date

        qty_map = {}
        try:
            qdict = products.with_context(ctx)._compute_quantities_dict(to_date=to_date)
            for pid, vals in qdict.items():
                qty_map[pid] = vals.get("qty_available", 0.0)
            return qty_map
        except Exception:
            for p in products:
                qty_map[p.id] = p.with_context(ctx).qty_available
            return qty_map

    def _get_unit_price_auto(self, product):
        """
        Regla:
        - Si tiene Ventas (sale_ok) => list_price
        - Si no, pero tiene Compras (purchase_ok) => standard_price
        - Si ninguno => standard_price
        """
        if getattr(product, "sale_ok", False):
            return product.list_price
        if getattr(product, "purchase_ok", False):
            return product.standard_price
        return product.standard_price

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
        sum_qty = 0.0
        sum_total = 0.0

        for wh in whs:
            location_id = wh.view_location_id.id
            qty_map = self._compute_qty_available(products, location_id, self.to_date)

            for p in products:
                qty = float(qty_map.get(p.id, 0.0))
                if not self.include_zero and qty == 0.0:
                    continue
                if not self.include_negative and qty < 0.0:
                    continue

                unit_price = self._get_unit_price_auto(p)
                total = qty * unit_price

                sum_qty += qty
                sum_total += total

                lines.append((0, 0, {
                    "warehouse_name": wh.name,
                    "warehouse_code": wh.code or "",
                    "product_code": p.default_code or "",
                    "product_name": p.display_name,
                    "qty": qty,
                    "unit_price": unit_price,
                    "total": total,
                }))

        self.write({
            "line_ids": lines,
            "total_qty": sum_qty,
            "total_value": sum_total,
        })
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
        fmt_bold = workbook.add_format({"bold": True, "border": 1})
        fmt_bold_num = workbook.add_format({"bold": True, "border": 1, "num_format": "#,##0.00"})
        fmt_bold_money = workbook.add_format({"bold": True, "border": 1, "num_format": "#,##0.00"})

        company = self.env.company.name or ""
        date_txt = fields.Datetime.to_string(self.to_date) if self.to_date else ""

        # Encabezado
        sheet.merge_range(0, 1, 0, 5, company, fmt_title)
        sheet.merge_range(1, 1, 1, 5, "Saldos por Bodega", fmt_title)
        sheet.merge_range(2, 1, 2, 5, f"Inventario a la fecha: {date_txt}", fmt_title)

        # EXCEL: Quitamos "COD BOD", dejamos solo BODEGA
        headers = ["BODEGA", "COD", "PRODUCTO", "SALDO", "PRECIO", "TOTAL"]
        for col, h in enumerate(headers):
            sheet.write(4, col, h, fmt_hdr)

        row = 5
        for l in self.line_ids:
            sheet.write(row, 0, l.warehouse_name, fmt_cell)
            sheet.write(row, 1, l.product_code, fmt_cell)
            sheet.write(row, 2, l.product_name, fmt_cell)
            sheet.write_number(row, 3, l.qty, fmt_num)
            sheet.write_number(row, 4, l.unit_price, fmt_money)
            sheet.write_number(row, 5, l.total, fmt_money)
            row += 1

        # Fila NETO (sumas)
        sheet.write(row, 2, "NETO", fmt_bold)
        sheet.write_number(row, 3, self.total_qty, fmt_bold_num)
        sheet.write(row, 4, "", fmt_bold)  # precio no suma
        sheet.write_number(row, 5, self.total_value, fmt_bold_money)

        # Anchos
        sheet.set_column(0, 0, 24)  # BODEGA
        sheet.set_column(1, 1, 14)  # COD
        sheet.set_column(2, 2, 45)  # PRODUCTO
        sheet.set_column(3, 5, 14)  # SALDO, PRECIO, TOTAL

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
    warehouse_code = fields.Char(readonly=True)  # lo dejamos por compatibilidad (no se imprime en Excel)

    product_code = fields.Char(readonly=True)
    product_name = fields.Char(readonly=True)

    qty = fields.Float(readonly=True)
    unit_price = fields.Float(readonly=True)
    total = fields.Float(readonly=True)
