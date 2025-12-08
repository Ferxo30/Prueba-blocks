# -*- coding: utf-8 -*-
from odoo import models
from .wizard.bak_report_xlsx_mixin import BakReportXlsxMixin


# ---------------------------------------------------------------------------
# LIBRO DE VENTAS - report.l10n_gt_extra.reporte_ventas
# ---------------------------------------------------------------------------

class ReporteVentasXlsx(BakReportXlsxMixin):
    _inherit = "report.l10n_gt_extra.reporte_ventas"

    def action_export_xlsx(self, data):
        result = self.lineas(data["form"])
        lineas = result.get("lineas", []) if isinstance(result, dict) else result
        # totales = result.get("totales", {})  # Si luego quieres usar totales

        header = [
            "Fecha",
            "Tipo",
            "Número",
            "Serie FEL",
            "Número FEL",
            "Cliente",
            "NIT",
            "Compra Neto",
            "Compra Exento",
            "Servicio Neto",
            "Servicio Exento",
            "Combustible Neto",
            "Combustible Exento",
            "Importación Neto",
            "Importación Exento",
            "Base",
            "IVA",
            "Total",
        ]
        rows = []

        if not lineas:
            rows.append([
                "",
                "",
                "",
                "",
                "",
                "No hay datos para mostrar",
                "",
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
            ])
        else:
            for l in lineas:
                rows.append([
                    str(l.get("fecha") or ""),
                    l.get("tipo") or "",
                    l.get("numero") or "",
                    l.get("serie_fel") or "",
                    l.get("numero_fel") or "",
                    l.get("cliente") or "",
                    l.get("nit") or "",
                    l.get("compra") or 0.0,
                    l.get("compra_exento") or 0.0,
                    l.get("servicio") or 0.0,
                    l.get("servicio_exento") or 0.0,
                    l.get("combustible") or 0.0,
                    l.get("combustible_exento") or 0.0,
                    l.get("importacion") or 0.0,
                    l.get("importacion_exento") or 0.0,
                    l.get("base") or 0.0,
                    l.get("iva") or 0.0,
                    l.get("total") or 0.0,
                ])

        return self._export_to_xlsx(
            header,
            rows,
            filename="Libro_Ventas_GT.xlsx",
            sheet_name="Libro Ventas",
        )


# ---------------------------------------------------------------------------
# LIBRO DE COMPRAS - report.l10n_gt_extra.reporte_compras
# ---------------------------------------------------------------------------

class ReporteComprasXlsx(BakReportXlsxMixin):
    _inherit = "report.l10n_gt_extra.reporte_compras"

    def action_export_xlsx(self, data):
        result = self.lineas(data["form"])
        lineas = result.get("lineas", []) if isinstance(result, dict) else result
        # totales = result.get("totales", {})

        header = [
            "Fecha",
            "Tipo",
            "Número",
            "Serie FEL",
            "Número FEL",
            "Proveedor",
            "NIT",
            "Compra Neto",
            "Compra Exento",
            "Servicio Neto",
            "Servicio Exento",
            "Combustible Neto",
            "Combustible Exento",
            "Importación Neto",
            "Importación Exento",
            "Pequeño Neto",
            "Pequeño Exento",
            "Base",
            "IVA",
            "Total",
        ]
        rows = []

        if not lineas:
            rows.append([
                "",
                "",
                "",
                "",
                "",
                "No hay datos para mostrar",
                "",
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
            ])
        else:
            for l in lineas:
                proveedor = ""
                nit = ""
                if l.get("proveedor"):
                    proveedor = getattr(l["proveedor"], "name", "") or ""
                    nit = getattr(l["proveedor"], "vat", "") or ""

                rows.append([
                    str(l.get("fecha") or ""),
                    l.get("tipo") or "",
                    l.get("numero") or "",
                    l.get("serie_fel") or "",
                    l.get("numero_fel") or "",
                    proveedor,
                    nit,
                    l.get("compra") or 0.0,
                    l.get("compra_exento") or 0.0,
                    l.get("servicio") or 0.0,
                    l.get("servicio_exento") or 0.0,
                    l.get("combustible") or 0.0,
                    l.get("combustible_exento") or 0.0,
                    l.get("importacion") or 0.0,
                    l.get("importacion_exento") or 0.0,
                    l.get("pequeño") or 0.0,
                    l.get("pequeño_exento") or 0.0,
                    l.get("base") or 0.0,
                    l.get("iva") or 0.0,
                    l.get("total") or 0.0,
                ])

        return self._export_to_xlsx(
            header,
            rows,
            filename="Libro_Compras_GT.xlsx",
            sheet_name="Libro Compras",
        )


# ---------------------------------------------------------------------------
# LIBRO MAYOR - report.l10n_gt_extra.reporte_mayor
# ---------------------------------------------------------------------------

class ReporteMayorXlsx(BakReportXlsxMixin):
    _inherit = "report.l10n_gt_extra.reporte_mayor"

    def action_export_xlsx(self, data):
        result = self.lineas(data["form"])
        lineas = result.get("lineas", []) if isinstance(result, dict) else result
        # totales = result.get("totales", {})

        header = [
            "Código",
            "Cuenta",
            "Saldo inicial",
            "Debe",
            "Haber",
            "Saldo final",
        ]
        rows = []

        if not lineas:
            rows.append([
                "",
                "No hay datos para mostrar",
                0.0,
                0.0,
                0.0,
                0.0,
            ])
        else:
            for l in lineas:
                debe = l.get("debe", l.get("total_debe", 0.0)) or 0.0
                haber = l.get("haber", l.get("total_haber", 0.0)) or 0.0
                rows.append([
                    l.get("codigo") or "",
                    l.get("cuenta") or "",
                    l.get("saldo_inicial") or 0.0,
                    debe,
                    haber,
                    l.get("saldo_final") or 0.0,
                ])

        return self._export_to_xlsx(
            header,
            rows,
            filename="Libro_Mayor_GT.xlsx",
            sheet_name="Libro Mayor",
        )


# ---------------------------------------------------------------------------
# REPORTE DIARIO - report.l10n_gt_extra.reporte_diario
# ---------------------------------------------------------------------------

class ReporteDiarioXlsx(BakReportXlsxMixin):
    _inherit = "report.l10n_gt_extra.reporte_diario"

    def action_export_xlsx(self, data):
        form = data.get("form", {}) or {}

        # Detectar si NO hay cuentas seleccionadas en el asistente
        posibles_campos_cuentas = [
            "cuentas_ids",
            "cuenta_ids",
            "account_ids",
            "accounts_ids",
            "cuentas",
            "cuenta",
        ]

        cuentas_vacias = True
        for field in posibles_campos_cuentas:
            value = form.get(field)
            if not value:
                continue

            # M2M suele venir como [(6, 0, [1,2,3])] o lista de ids
            if isinstance(value, (list, tuple, set)):
                if not value:
                    continue

                # Caso comandos ORM: [(6, 0, [1,2])]
                first = value[0]
                if isinstance(first, (list, tuple)) and len(first) >= 3 and isinstance(first[2], (list, tuple, set)):
                    ids = first[2]
                    if ids:
                        cuentas_vacias = False
                        break
                else:
                    # Lista simple de ids
                    if len(value) > 0:
                        cuentas_vacias = False
                        break
            else:
                # Algún otro formato no vacío
                cuentas_vacias = False
                break

        header = [
            "Fecha",
            "Código",
            "Cuenta",
            "Saldo inicial",
            "Debe",
            "Haber",
            "Saldo final",
        ]
        rows = []

        # Si no hay cuentas seleccionadas, NO llamamos al reporte original
        if cuentas_vacias:
            rows.append([
                "",
                "",
                "No hay cuentas seleccionadas / no hay datos para mostrar",
                0.0,
                0.0,
                0.0,
                0.0,
            ])
            return self._export_to_xlsx(
                header,
                rows,
                filename="Libro_Diario_GT.xlsx",
                sheet_name="Libro Diario",
            )

        # Aquí ya es seguro llamar a la lógica original (no habrá IN ())
        result = self.lineas(form)
        lineas = result.get("lineas", []) if isinstance(result, dict) else result

        lineas_list = list(lineas)
        if lineas_list and isinstance(lineas_list[0], dict) and "cuentas" in lineas_list[0]:
            # Agrupado por día
            for grupo in lineas_list:
                fecha = str(grupo.get("fecha") or "")
                for c in grupo.get("cuentas", []):
                    rows.append([
                        fecha,
                        c.get("codigo") or "",
                        c.get("cuenta") or "",
                        c.get("saldo_inicial") or 0.0,
                        c.get("debe") or 0.0,
                        c.get("haber") or 0.0,
                        c.get("saldo_final") or 0.0,
                    ])
        else:
            # Modo simple
            for c in lineas_list:
                rows.append([
                    "",
                    c.get("codigo") or "",
                    c.get("cuenta") or "",
                    c.get("saldo_inicial") or 0.0,
                    c.get("debe") or 0.0,
                    c.get("haber") or 0.0,
                    c.get("saldo_final") or 0.0,
                ])

        return self._export_to_xlsx(
            header,
            rows,
            filename="Libro_Diario_GT.xlsx",
            sheet_name="Libro Diario",
        )


# ---------------------------------------------------------------------------
# REPORTE INVENTARIO - report.l10n_gt_extra.reporte_inventario
# ---------------------------------------------------------------------------

class ReporteInventarioXlsx(BakReportXlsxMixin):
    _inherit = "report.l10n_gt_extra.reporte_inventario"

    def action_export_xlsx(self, data):
        result = self.lineas(data["form"])
        lineas = result.get("lineas", {}) if isinstance(result, dict) else {}
        # totales = result.get("totales", {})

        header = [
            "Grupo",
            "Código",
            "Cuenta",
            "Saldo inicial",
            "Debe",
            "Haber",
            "Saldo final",
        ]
        rows = []

        if not lineas:
            rows.append([
                "",
                "",
                "No hay datos para mostrar",
                0.0,
                0.0,
                0.0,
                0.0,
            ])
        else:
            for grupo in ("activo", "pasivo", "capital"):
                for l in lineas.get(grupo, []):
                    rows.append([
                        grupo.capitalize(),
                        l.get("codigo") or "",
                        l.get("cuenta") or "",
                        l.get("saldo_inicial") or 0.0,
                        l.get("debe") or 0.0,
                        l.get("haber") or 0.0,
                        l.get("saldo_final") or 0.0,
                    ])

        return self._export_to_xlsx(
            header,
            rows,
            filename="Inventario_GT.xlsx",
            sheet_name="Inventario",
        )


# ---------------------------------------------------------------------------
# REPORTE BANCO - report.l10n_gt_extra.reporte_banco
# ---------------------------------------------------------------------------

class ReporteBancoXlsx(BakReportXlsxMixin):
    _inherit = "report.l10n_gt_extra.reporte_banco"

    def action_export_xlsx(self, data):
        form = data.get("form", {}) or {}

        lineas = self.lineas(form)
        balance_ini = self.balance_inicial(form)

        header = [
            "Fecha",
            "Documento",
            "Nombre",
            "Concepto",
            "Débito",
            "Crédito",
            "Balance",
        ]
        rows = []

        # Fila de saldo inicial
        rows.append([
            "",
            "",
            "",
            "Saldo inicial",
            "",
            "",
            balance_ini.get(
                "balance_moneda" if balance_ini.get("usar_balance_moneda") else "balance",
                0.0,
            ),
        ])

        if not lineas:
            rows.append([
                "",
                "",
                "",
                "No hay datos para mostrar",
                0.0,
                0.0,
                rows[-1][6],  # mismo saldo que la fila anterior
            ])
        else:
            # Líneas de movimientos
            for l in lineas:
                rows.append([
                    str(l.get("fecha") or ""),
                    l.get("documento") or "",
                    l.get("nombre") or "",
                    l.get("concepto") or "",
                    l.get("debito") or 0.0,
                    l.get("credito") or 0.0,
                    l.get("balance") or 0.0,
                ])

        return self._export_to_xlsx(
            header,
            rows,
            filename="Libro_Bancos_GT.xlsx",
            sheet_name="Bancos",
        )


# ---------------------------------------------------------------------------
# REPORTE PARTIDA - report.l10n_gt_extra.reporte_partida
# ---------------------------------------------------------------------------

class ReportePartidaXlsx(BakReportXlsxMixin):
    _inherit = "report.l10n_gt_extra.reporte_partida"

    def action_export_xlsx(self, data):
        model = "account.move"
        docs = self.env[model].browse(data.get("docids") or [])

        header = [
            "Partida",
            "Fecha",
            "Journal",
            "Cuenta",
            "Label",
            "Partner",
            "Débito",
            "Crédito",
        ]
        rows = []

        if not docs:
            rows.append([
                "No hay datos para mostrar",
                "",
                "",
                "",
                "",
                "",
                0.0,
                0.0,
            ])
        else:
            for move in docs:
                for line in move.line_ids:
                    rows.append([
                        move.name or "",
                        str(move.date or ""),
                        move.journal_id.display_name or "",
                        f"{line.account_id.code or ''} {line.account_id.name or ''}".strip(),
                        line.name or "",
                        line.partner_id.display_name or "",
                        line.debit or 0.0,
                        line.credit or 0.0,
                    ])

        return self._export_to_xlsx(
            header,
            rows,
            filename="Reporte_Partida_GT.xlsx",
            sheet_name="Partidas",
        )
