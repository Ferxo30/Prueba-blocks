# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class PosOrderPaymentWizard(models.TransientModel):
    _name = 'pos.order.payment.wizard'
    _description = 'Registrar pago en orden POS sin factura'

    pos_order_id = fields.Many2one(
        'pos.order',
        string='Orden POS',
        required=True,
        readonly=True,
    )
    customer_account_residual = fields.Monetary(
        string='Saldo en cuenta cliente',
        readonly=True,
        currency_field='currency_id',
    )
    amount = fields.Monetary(
        string='Monto a pagar',
        required=True,
        currency_field='currency_id',
    )
    payment_method_id = fields.Many2one(
        'pos.payment.method',
        string='Método de pago',
        required=True,
    )
    note = fields.Char(
        string='Referencia / comentario',
        help='Comentario para identificar este pago manual.',
    )
    currency_id = fields.Many2one(
        'res.currency',
        related='pos_order_id.currency_id',
        readonly=True,
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        order_id = (
            self.env.context.get('default_pos_order_id')
            or self.env.context.get('active_id')
        )
        if order_id:
            order = self.env['pos.order'].browse(order_id)
            res['pos_order_id'] = order.id
            customer_payments = order.payment_ids.filtered(
                lambda p: (
                    getattr(p.payment_method_id, 'is_customer_account', False)
                    or (p.payment_method_id.name or '').strip().lower() in ('cuenta de cliente', 'customer account')
                )
            )
            residual = sum(customer_payments.mapped('amount'))
            res['customer_account_residual'] = residual
            if residual and 'amount' not in res:
                res['amount'] = residual
        return res

    def _get_customer_account_payments(self):
        self.ensure_one()
        order = self.pos_order_id
        customer_payments = order.payment_ids.filtered(
            lambda p: (
                getattr(p.payment_method_id, 'is_customer_account', False)
                or (p.payment_method_id.name or '').strip().lower() in ('cuenta de cliente', 'customer account')
            )
        )
        if not customer_payments:
            raise UserError(_('La orden no tiene pagos en "Cuenta de cliente".'))
        return customer_payments

    def action_confirm(self):
        for wizard in self:
            wizard._action_confirm_single()
        return {'type': 'ir.actions.act_window_close'}

    def _action_confirm_single(self):
        self.ensure_one()
        order = self.pos_order_id

        if not order.partner_id:
            raise UserError(_('La orden debe tener un cliente para registrar este pago.'))

        if getattr(order, 'account_move', False):
            raise UserError(_('Esta opción solo es para órdenes POS sin factura relacionada.'))

        if self.amount <= 0:
            raise UserError(_('El monto a pagar debe ser mayor que cero.'))

        customer_payments = self._get_customer_account_payments()
        residual = sum(customer_payments.mapped('amount'))

        if self.amount > residual:
            raise UserError(_(
                'El monto a pagar (%(amount)s) no puede ser mayor al saldo en cuenta cliente (%(residual)s).'
            ) % {'amount': self.amount, 'residual': residual})

        PosPayment = self.env['pos.payment'].with_context(
            allow_pos_registered_payment_edit=True
        )

        new_payment_vals = {
            'pos_order_id': order.id,
            'amount': self.amount,
            'payment_method_id': self.payment_method_id.id,
            'session_id': order.session_id.id,
            'currency_id': order.currency_id.id,
            'name': self.note or _('Pago manual POS'),
        }
        PosPayment.create(new_payment_vals)

        remaining = self.amount
        customer_payments_ctx = customer_payments.with_context(
            allow_pos_registered_payment_edit=True
        )
        for pay in customer_payments_ctx:
            if remaining <= 0:
                break
            if pay.amount <= remaining:
                remaining -= pay.amount
                pay.unlink()
            else:
                pay.amount = pay.amount - remaining
                remaining = 0
