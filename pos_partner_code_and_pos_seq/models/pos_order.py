from odoo import api, fields, models

class PosOrder(models.Model):
    _inherit = "pos.order"

    internal_pos_sequence = fields.Char(
        string="Correlativo interno POS",
        copy=False,
        index=True,
        help="Serie interna por establecimiento (ej.: A-001, B-001, C-001)."
    )

    @api.model
    def _order_fields(self, ui_order):
        res = super()._order_fields(ui_order)

        session_id = ui_order.get('pos_session_id') or ui_order.get('session_id')
        if session_id:
            session = self.env['pos.session'].browse(session_id)
            config = session.config_id
            if config:
                config._ensure_internal_sequence()
                seq = config.pos_internal_sequence_id.sudo().with_company(config.company_id).next_by_id()
                res['internal_pos_sequence'] = seq

        return res

    @api.model
    def create(self, vals):
        # Fallback robusto: si viene sin correlativo, créalo aquí.
        if not vals.get('internal_pos_sequence'):
            session_id = vals.get('session_id')
            if session_id:
                session = self.env['pos.session'].browse(session_id)
                if session and session.config_id:
                    cfg = session.config_id
                    cfg._ensure_internal_sequence()
                    vals['internal_pos_sequence'] = cfg.pos_internal_sequence_id.sudo().with_company(cfg.company_id).next_by_id()
        return super().create(vals)

    def write(self, vals):
        res = super().write(vals)
        # Si por alguna razón quedó sin correlativo y ya tiene sesión, complétalo.
        for order in self.filtered(lambda o: not o.internal_pos_sequence and o.session_id and o.session_id.config_id):
            cfg = order.session_id.config_id
            cfg._ensure_internal_sequence()
            order.internal_pos_sequence = cfg.pos_internal_sequence_id.sudo().with_company(cfg.company_id).next_by_id()
        return res
