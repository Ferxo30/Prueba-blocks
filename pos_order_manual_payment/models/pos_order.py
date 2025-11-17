# -*- coding: utf-8 -*-
from odoo import api, fields, models


class PosOrder(models.Model):
    _inherit = 'pos.order'

    payment_state = fields.Selection(
        [
            ('not_paid', 'No pagado'),
            ('partial', 'Parcialmente pagado'),
            ('paid', 'Pagado'),
        ],
        string='Estado de pago',
        compute='_compute_payment_state',
        store=False,
    )

    @api.depends('amount_total', 'amount_paid')
    def _compute_payment_state(self):
        for order in self:
            if not order.amount_total:
                order.payment_state = 'not_paid'
            elif order.amount_paid + 1e-6 >= order.amount_total:
                order.payment_state = 'paid'
            elif order.amount_paid > 0:
                order.payment_state = 'partial'
            else:
                order.payment_state = 'not_paid'

    def action_open_pos_order_payment_wizard(self):
        self.ensure_one()
        return {
            'name': 'Registrar pago POS',
            'type': 'ir.actions.act_window',
            'res_model': 'pos.order.payment.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_pos_order_id': self.id,
            },
        }
