
from odoo import api, fields, models

class PosConfig(models.Model):
    _inherit = "pos.config"

    pos_series_prefix = fields.Char(
        string="Prefijo de serie interna (A/B/C)",
        help="Prefijo para el correlativo interno del POS, p.ej. 'A-'",
        default="A-"
    )
    pos_internal_sequence_id = fields.Many2one(
        "ir.sequence",
        string="Secuencia interna de ventas POS",
        readonly=True,
        copy=False,
        help="Secuencia usada para generar el correlativo interno por orden POS."
    )

    def _ensure_internal_sequence(self):
        for config in self:
            if not config.pos_internal_sequence_id:
                seq = self.env["ir.sequence"].create({
                    "name": f"POS {config.display_name} Internal Seq",
                    "implementation": "standard",
                    "prefix": (config.pos_series_prefix or "A-"),
                    "padding": 3,
                    "code": f"pos.order.internal.seq.{config.id}",
                    "company_id": config.company_id.id,
                })
                config.pos_internal_sequence_id = seq.id

    def write(self, vals):
        res = super().write(vals)
        if 'pos_series_prefix' in vals:
            for cfg in self:
                if cfg.pos_internal_sequence_id:
                    cfg.pos_internal_sequence_id.prefix = vals['pos_series_prefix'] or "A-"
        self._ensure_internal_sequence()
        return res

    
@api.model_create_multi
def create(self, vals_list):
    # Auto-asignar prefijo A/B/C si no viene definido.
    for vals in vals_list:
        if not vals.get('pos_series_prefix'):
            # ordenar por id existentes y asignar A/B/C al contador
            existing = self.search([], order='id asc')
            # next index (0-based)
            idx = len(existing) % 3
            vals['pos_series_prefix'] = ['A-', 'B-', 'C-'][idx]
    records = super().create(vals_list)
    records._ensure_internal_sequence()
    return records

