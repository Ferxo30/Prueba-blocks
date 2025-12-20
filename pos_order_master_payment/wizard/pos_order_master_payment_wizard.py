# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PosOrderMasterPaymentWizard(models.TransientModel):
    _name = "pos.order.payment.master.wizard"
    _description = "Wizard Pago Maestro POS"

    date = fields.Datetime(
        string="Fecha del pago",
        default=fields.Datetime.now,
        required=True,
    )

    payment_method_id = fields.Many2one(
        "pos.payment.method",
        string="Método de pago",
        required=True,
    )

    journal_id = fields.Many2one(
        "account.journal",
        string="Diario",
    )

    reference = fields.Char(string="Referencia")
    note = fields.Text(string="Nota")

    line_ids = fields.One2many(
        "pos.order.payment.master.wizard.line",
        "wizard_id",
        string="Órdenes",
    )

    currency_id = fields.Many2one(
        "res.currency",
        string="Moneda",
        compute="_compute_currency_id",
        store=False,
        readonly=True,
    )

    amount_total = fields.Monetary(
        string="Importe total",
        compute="_compute_amount_total",
        currency_field="currency_id",
        store=False,
        readonly=True,
    )

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    def _get_order_currency(self, order):
        """
        Resolver robusto de moneda para pos.order.
        En algunas DB pos.order.pricelist_id puede venir vacío; por eso probamos
        varias fuentes en orden de prioridad.
        """
        # 1) Si existe currency_id en pos.order (depende de versión / custom)
        cur = getattr(order, "currency_id", False)
        if cur:
            return cur

        # 2) Si existe pricelist_id
        pricelist = getattr(order, "pricelist_id", False)
        cur = getattr(pricelist, "currency_id", False) if pricelist else False
        if cur:
            return cur

        # 3) Moneda configurada en POS (session/config)
        session = getattr(order, "session_id", False)
        config = getattr(session, "config_id", False) if session else getattr(order, "config_id", False)

        cur = getattr(session, "currency_id", False) if session else False
        if cur:
            return cur

        cur = getattr(config, "currency_id", False) if config else False
        if cur:
            return cur

        # 4) Fallback final: moneda de compañía
        company = getattr(order, "company_id", False)
        cur = getattr(company, "currency_id", False) if company else False
        return cur or False

    # -------------------------------------------------------------------------
    # Computes
    # -------------------------------------------------------------------------

    @api.depends("line_ids.pos_order_id")
    def _compute_currency_id(self):
        for wiz in self:
            orders = wiz.line_ids.mapped("pos_order_id").filtered(lambda o: o)
            if not orders:
                wiz.currency_id = False
                continue

            currencies = []
            for o in orders:
                c = wiz._get_order_currency(o)
                if c:
                    currencies.append(c)

            # Normalizar por código (c.name), para evitar falsos negativos si hay duplicados
            codes = sorted({c.name for c in currencies if c and c.name})
            if len(codes) == 1 and currencies:
                wiz.currency_id = currencies[0]
            else:
                wiz.currency_id = False

    @api.depends("line_ids.amount_to_pay")
    def _compute_amount_total(self):
        for wiz in self:
            wiz.amount_total = sum(wiz.line_ids.mapped("amount_to_pay"))

    # -------------------------------------------------------------------------
    # Defaults
    # -------------------------------------------------------------------------

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_model = self.env.context.get("active_model")
        active_ids = self.env.context.get("active_ids") or []

        if active_model == "pos.order" and active_ids:
            orders = self.env["pos.order"].browse(active_ids).exists()
            lines = []
            for order in orders:
                pending = max((order.amount_total or 0.0) - (order.manual_paid_amount or 0.0), 0.0)
                lines.append((0, 0, {
                    "pos_order_id": order.id,
                    "amount_to_pay": pending,
                }))
            res["line_ids"] = lines
        return res

    # -------------------------------------------------------------------------
    # Actions
    # -------------------------------------------------------------------------

    def action_confirm(self):
        self.ensure_one()

        if not self.payment_method_id:
            raise UserError(_("Debe seleccionar un método de pago."))

        if not self.line_ids:
            raise UserError(_("No hay órdenes para procesar."))

        # BLINDAJE: ignorar líneas sin orden (por issues UI / editable list)
        valid_lines = self.line_ids.filtered(lambda l: l.pos_order_id)
        if not valid_lines:
            raise UserError(_("No hay órdenes válidas para procesar. Cierre el wizard y ábralo de nuevo."))

        pay_lines = valid_lines.filtered(lambda l: (l.amount_to_pay or 0.0) > 0)
        if not pay_lines:
            raise UserError(_("Debe ingresar un importe mayor a 0 en al menos una orden."))

        orders = pay_lines.mapped("pos_order_id").filtered(lambda o: o)
        if not orders:
            raise UserError(_("No hay órdenes válidas para procesar. Cierre el wizard y ábralo de nuevo."))

        # Moneda única (resolver robusto + normalización por código)
        currencies = []
        missing = []
        for o in orders:
            c = self._get_order_currency(o)
            if c:
                currencies.append(c)
            else:
                missing.append(o)

        if missing:
            detail = "\n".join([
                "- %s | Company: %s | Session: %s | Config: %s | Pricelist: %s"
                % (
                    o.display_name,
                    o.company_id.display_name if o.company_id else "N/A",
                    o.session_id.display_name if getattr(o, "session_id", False) else "N/A",
                    (o.session_id.config_id.display_name if (getattr(o, "session_id", False) and o.session_id.config_id) else "N/A"),
                    o.pricelist_id.display_name if getattr(o, "pricelist_id", False) else "N/A",
                )
                for o in missing
            ])
            raise UserError(_("No se pudo determinar la moneda de las órdenes.\n\n%s") % detail)

        codes = sorted({c.name for c in currencies if c and c.name})
        if len(codes) != 1:
            detail = "\n".join([
                "- %s | Moneda: %s (id=%s)"
                % (
                    o.display_name,
                    (self._get_order_currency(o).name if self._get_order_currency(o) else "N/A"),
                    (self._get_order_currency(o).id if self._get_order_currency(o) else "N/A"),
                )
                for o in orders
            ])
            raise UserError(
                _("Las órdenes seleccionadas deben compartir la misma moneda para registrar un pago maestro.\n"
                  "Códigos detectados: %s\n\nDetalle:\n%s")
                % (", ".join(codes) if codes else "N/A", detail)
            )

        currency = currencies[0]

        # Validaciones por orden
        invalid = []
        for line in pay_lines:
            order = line.pos_order_id

            if order.state in ("draft", "cancel"):
                invalid.append(order.display_name)
                continue
            if order.state == "invoiced":
                invalid.append(order.display_name)
                continue

            due = line.amount_due or 0.0
            amt = line.amount_to_pay or 0.0

            if amt > due + 0.00001:
                raise UserError(
                    _(
                        "El importe a pagar no puede ser mayor al saldo pendiente en la orden %(order)s.\n"
                        "Pendiente: %(due).2f, a pagar: %(amt).2f"
                    )
                    % {"order": order.display_name, "due": due, "amt": amt}
                )

        if invalid:
            raise UserError(
                _("Las siguientes órdenes no son válidas para registrar pagos maestros: %s")
                % ", ".join(sorted(set(invalid)))
            )

        # Crear cabecera (no contable)
        master = self.env["pos.order.payment.master"].create({
            "date": self.date,
            "payment_method_id": self.payment_method_id.id,
            "journal_id": self.journal_id.id or False,
            "reference": self.reference,
            "note": self.note,
            "currency_id": currency.id,
            "company_id": self.env.company.id,
        })

        # Crear pagos por orden (no contable)
        payment_vals = []
        for line in pay_lines:
            payment_vals.append({
                "pos_order_id": line.pos_order_id.id,
                "date": self.date,
                "payment_method_id": self.payment_method_id.id,
                "journal_id": self.journal_id.id or False,
                "amount": line.amount_to_pay,
                "reference": self.reference,
                "note": self.note,
                "master_id": master.id,
            })

        self.env["pos.order.payment"].create(payment_vals)

        return {
            "name": _("Pago maestro POS"),
            "type": "ir.actions.act_window",
            "res_model": "pos.order.payment.master",
            "view_mode": "form",
            "res_id": master.id,
        }


class PosOrderMasterPaymentWizardLine(models.TransientModel):
    _name = "pos.order.payment.master.wizard.line"
    _description = "Línea Wizard Pago Maestro POS"
    _order = "id"

    wizard_id = fields.Many2one(
        "pos.order.payment.master.wizard",
        required=True,
        ondelete="cascade",
    )

    pos_order_id = fields.Many2one(
        "pos.order",
        string="Orden POS",
        required=True,
        readonly=True,
    )

    currency_id = fields.Many2one(
        "res.currency",
        string="Moneda",
        related="pos_order_id.pricelist_id.currency_id",
        readonly=True,
    )

    amount_total = fields.Monetary(
        string="Total orden",
        related="pos_order_id.amount_total",
        currency_field="currency_id",
        readonly=True,
    )

    manual_paid_amount = fields.Monetary(
        string="Pagado (manual)",
        related="pos_order_id.manual_paid_amount",
        currency_field="currency_id",
        readonly=True,
    )

    amount_due = fields.Monetary(
        string="Saldo pendiente",
        compute="_compute_amount_due",
        currency_field="currency_id",
        readonly=True,
    )

    amount_to_pay = fields.Monetary(
        string="Importe a aplicar",
        currency_field="currency_id",
    )

    @api.depends("pos_order_id.amount_total", "pos_order_id.manual_paid_amount")
    def _compute_amount_due(self):
        for line in self:
            total = line.pos_order_id.amount_total or 0.0
            paid = line.pos_order_id.manual_paid_amount or 0.0
            line.amount_due = max(total - paid, 0.0)
