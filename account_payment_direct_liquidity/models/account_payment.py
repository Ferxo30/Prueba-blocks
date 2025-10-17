# -*- coding: utf-8 -*-
from odoo import models

class AccountPayment(models.Model):
    _inherit = "account.payment"

    # Acepta force_balance y **kwargs para compatibilidad con account/base_accounting_kit
    def _prepare_move_line_default_vals(self, write_off_line_vals=None, force_balance=False, **kwargs):
        vals_list = super()._prepare_move_line_default_vals(
            write_off_line_vals=write_off_line_vals,
            force_balance=force_balance,
            **kwargs
        )

        for payment in self:
            journal = payment.journal_id
            if not journal:
                continue

            # Soporta tanto la versión "global" (sin checkbox) como la versión con checkbox en el diario
            direct_flag = True  # por defecto true para la versión global
            if hasattr(journal, "direct_liquidity_on_payment"):
                direct_flag = bool(journal.direct_liquidity_on_payment)

            if not direct_flag:
                continue

            liquidity_acc = journal.default_account_id
            if not liquidity_acc:
                # sin cuenta de liquidez definida en el diario, no tocamos nada
                continue

            # Forzar que la(s) línea(s) de liquidez usen la cuenta del diario (banco/caja)
            # En v18, las líneas vienen como una lista de dicts
            for line in vals_list:
                if "account_id" in line:
                    line["account_id"] = liquidity_acc.id

        return vals_list

    # Opcionalmente, si en tu build se usa aún este hook, lo dejamos compatible:
    def _get_liquidity_move_line_vals(self, amount, **kwargs):
        vals = super()._get_liquidity_move_line_vals(amount, **kwargs)
        # No hacemos nada aquí porque ya controlamos la cuenta en _prepare_move_line_default_vals.
        # Lo dejamos para compatibilidad (que no truene si otro módulo lo llama).
        return vals

