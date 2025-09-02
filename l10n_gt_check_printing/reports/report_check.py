# -*- coding: utf-8 -*-
from odoo import api, models

class ReportCheckGT(models.AbstractModel):
    _name = "report.l10n_gt_check_printing.report_check"
    _description = "Report: Guatemala Check"

    # === HELPERS EXPUESTOS AL QWEB ===
    def _amount_words_line(self, payment):
        """Devuelve 'Quinientos Con 00/100' (sin moneda)."""
        amount = payment.amount or 0.0
        integer = int(amount)
        cents = int(round((amount - integer) * 100))
        # Palabras del entero usando la moneda (soporta localización si existe)
        words = ""
        try:
            # algunas versiones aceptan lang, otras no
            try:
                words = payment.currency_id.amount_to_text(integer, lang=self.env.user.lang)
            except TypeError:
                words = payment.currency_id.amount_to_text(integer)
        except Exception:
            words = str(integer)

        if isinstance(words, str):
            words = words.strip()
            if words:
                words = words[0].upper() + words[1:]  # Capitalizar primera letra
            words = words.replace(" y ", " Con ")    # '... y ...' -> '... Con ...'
        return f"{words} {cents:02d}/100"

    def _fmt_date(self, d):
        """dd/mm/YYYY"""
        return d.strftime("%d/%m/%Y") if d else ""

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env["account.payment"].browse(docids)
        return {
            "docs": docs,
            # helpers disponibles en QWeb:
            "amount_words_line": self._amount_words_line,
            "fmt_date": self._fmt_date,
            "upper": lambda s: (s or "").upper(),
        }
    def _is_void_payment(self, payment):
        """True si el pago/asiento está anulado en Odoo 17/18."""
        st = (getattr(payment, "state", "") or "").lower()
        if st in {"cancelled", "cancel"}:
            return True
        move = getattr(payment, "move_id", False)
        if move and (getattr(move, "state", "") or "").lower() == "cancel":
            return True
        return False

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env["account.payment"].browse(docids)
        return {
            "docs": docs,
            "amount_words_line": self._amount_words_line,  # tu helper actual
            "fmt_date": self._fmt_date,                    # tu helper actual
            "upper": lambda s: (s or "").upper(),          # tu helper actual
            "is_void_payment": self._is_void_payment,      # <-- exportamos helper
        }



    # ... (deja aquí tus otros helpers como _amount_words_line y _fmt_date)

    def _is_void_payment(self, payment):
        """Devuelve True si el pago/asiento está anulado, cubriendo variantes:
        'canceled', 'cancelled', 'cancel' (y el asiento en 'cancel')."""
        st = ((getattr(payment, "state", "") or "")).lower()
        if st in {"canceled", "cancelled", "cancel"}:
            return True
        move = getattr(payment, "move_id", False)
        if move and ((getattr(move, "state", "") or "").lower() in {"cancel", "canceled", "cancelled"}):
            return True
        return False

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env["account.payment"].browse(docids)
        return {
            "docs": docs,
            "amount_words_line": self._amount_words_line,  # ya lo tienes
            "fmt_date": self._fmt_date,                    # ya lo tienes
            "upper": lambda s: (s or "").upper(),          # ya lo tienes
            "is_void_payment": self._is_void_payment,      # <-- exporta el helper
        }


   

