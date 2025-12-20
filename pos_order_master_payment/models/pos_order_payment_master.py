# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class PosOrderPaymentMaster(models.Model):
    _name = "pos.order.payment.master"
    _description = "Pago maestro POS (multi-orden)"
    _order = "date desc, id desc"

    name = fields.Char(
        string="Correlativo maestro",
        readonly=True,
        copy=False,
        default=lambda self: _("New"),
    )

    company_id = fields.Many2one(
        "res.company",
        string="Compañía",
        default=lambda self: self.env.company,
        required=True,
        readonly=True,
    )

    currency_id = fields.Many2one(
        "res.currency",
        string="Moneda",
        required=True,
        readonly=True,
    )

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

    payment_ids = fields.One2many(
        comodel_name="pos.order.payment",
        inverse_name="master_id",
        string="Pagos por orden",
        readonly=True,
    )

    amount_total = fields.Monetary(
        string="Importe total",
        compute="_compute_amount_total",
        store=True,
        currency_field="currency_id",
    )

    order_ids = fields.Many2many(
        comodel_name="pos.order",
        string="Órdenes POS",
        compute="_compute_order_ids",
        store=True,
        readonly=True,
    )

    order_count = fields.Integer(
        string="# Órdenes",
        compute="_compute_order_ids",
        store=True,
    )

    partner_id = fields.Many2one(
        "res.partner",
        string="Cliente",
        compute="_compute_partner",
        store=False,
        readonly=True,
    )

    @api.depends("payment_ids.pos_order_id")
    def _compute_order_ids(self):
        for rec in self:
            orders = rec.payment_ids.mapped("pos_order_id")
            rec.order_ids = [(6, 0, orders.ids)]
            rec.order_count = len(orders)

    @api.depends("payment_ids.amount")
    def _compute_amount_total(self):
        for rec in self:
            rec.amount_total = sum(rec.payment_ids.mapped("amount"))

    @api.depends("order_ids.partner_id")
    def _compute_partner(self):
        for rec in self:
            partners = rec.order_ids.mapped("partner_id").filtered(lambda p: p)
            if partners and len(partners) == 1:
                rec.partner_id = partners[0]
            else:
                rec.partner_id = False

    @api.model
    def create(self, vals):
        if not vals.get("name") or vals.get("name") == _("New"):
            seq = self.env.ref(
                "pos_order_master_payment.seq_pos_order_master_payment",
                raise_if_not_found=False,
            )
            if seq:
                vals["name"] = seq.next_by_id()
            else:
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code("pos.order.payment.master")
                    or _("New")
                )
        return super().create(vals)

    def action_view_orders(self):
        self.ensure_one()
        return {
            "name": _("Órdenes POS"),
            "type": "ir.actions.act_window",
            "res_model": "pos.order",
            "view_mode": "list,form",
            "domain": [("id", "in", self.order_ids.ids)],
            "context": {"create": False},
        }
