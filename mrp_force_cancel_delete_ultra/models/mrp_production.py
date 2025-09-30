from odoo import api, models, _
from odoo.exceptions import UserError

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    def _related_stock_moves(self):
        self.ensure_one()
        moves = self.move_raw_ids | self.move_finished_ids
        if 'move_byproduct_ids' in self._fields:
            moves |= self.move_byproduct_ids
        if 'workorder_ids' in self._fields:
            for wo in self.workorder_ids:
                if 'move_raw_ids' in wo._fields:
                    moves |= wo.move_raw_ids
        return moves

    def _related_pickings(self):
        self.ensure_one()
        return self._related_stock_moves().mapped('picking_id')

    def action_force_cancel_only(self):
        for mo in self.sudo():
            try:
                mo.button_cancel()
            except Exception:
                mo.write({'state': 'cancel'})
        return True

    def action_force_cancel_and_delete(self):
        for mo in self.sudo():
            mo._soft_cleanup()
            try:
                mo.button_cancel()
            except Exception:
                mo.write({'state': 'cancel'})
            mo.sudo().unlink()
        return True

    def _soft_cleanup(self):
        SVL = self.env['stock.valuation.layer']
        Move = self.env['stock.move']
        MLine = self.env['stock.move.line']

        for p in self._related_pickings().filtered(lambda x: x.state in ('waiting','confirmed','assigned')):
            try:
                p.action_cancel()
            except Exception:
                try:
                    p.write({'state': 'cancel'})
                except Exception:
                    pass

        moves = self._related_stock_moves().sudo()
        try:
            svls = SVL.search([('stock_move_id','in', moves.ids)])
            svls.unlink()
        except Exception:
            pass

        lines = MLine.search([('move_id','in', moves.ids)]).sudo()
        try:
            lines.unlink()
        except Exception:
            try:
                lines.write({'qty_done': 0})
                lines.unlink()
            except Exception:
                pass

        for m in moves:
            try:
                if m.state not in ('cancel',):
                    m._action_cancel()
            except Exception:
                try:
                    m.write({'state': 'cancel'})
                except Exception:
                    pass
        try:
            moves.unlink()
        except Exception:
            pass

        for p in self._related_pickings().sudo():
            try:
                if p.state not in ('cancel',):
                    p.action_cancel()
            except Exception:
                pass
            try:
                p.unlink()
            except Exception:
                pass

        if 'workorder_ids' in self._fields and self.workorder_ids:
            try:
                self.workorder_ids.sudo().unlink()
            except Exception:
                pass
        if 'move_byproduct_ids' in self._fields and self.move_byproduct_ids:
            try:
                self.move_byproduct_ids.sudo().unlink()
            except Exception:
                pass

    def action_ultra_erase_everything(self):
        cr = self.env.cr
        for mo in self.sudo():
            moves = mo._related_stock_moves().sudo()
            move_ids = moves.ids or [0]
            line_ids = self.env['stock.move.line'].sudo().search([('move_id','in', move_ids)]).ids
            picking_ids = (mo._related_pickings().sudo().ids) or [0]
            svl_ids = self.env['stock.valuation.layer'].sudo().search([('stock_move_id','in', move_ids)]).ids

            am_model = self.env['account.move'].sudo()
            aml_model = self.env['account.move.line'].sudo()
            am_to_delete = am_model.search(['|', ('ref','ilike', mo.name), ('line_ids.stock_move_id','in', move_ids)])

            for am in am_to_delete:
                try:
                    if hasattr(am, 'button_draft') and am.state == 'posted':
                        am.button_draft()
                    elif am.state == 'posted':
                        am.write({'state':'draft'})
                except Exception:
                    try:
                        am.write({'state':'draft'})
                    except Exception:
                        pass
            try:
                am_to_delete.unlink()
            except Exception:
                aml_model.search([('move_id','in', am_to_delete.ids)]).unlink()
                try:
                    am_to_delete.unlink()
                except Exception:
                    pass

            if line_ids:
                cr.execute("DELETE FROM stock_move_line WHERE id = ANY(%s)", (line_ids,))
            if svl_ids:
                cr.execute("DELETE FROM stock_valuation_layer WHERE id = ANY(%s)", (svl_ids,))
            if move_ids:
                cr.execute("DELETE FROM stock_move WHERE id = ANY(%s)", (move_ids,))
            if picking_ids:
                cr.execute("DELETE FROM stock_picking WHERE id = ANY(%s)", (picking_ids,))

            if 'workorder_ids' in mo._fields and mo.workorder_ids:
                cr.execute("DELETE FROM mrp_workorder WHERE id = ANY(%s)", (mo.workorder_ids.ids,))
            if 'move_byproduct_ids' in mo._fields and mo.move_byproduct_ids:
                cr.execute("DELETE FROM stock_move WHERE id = ANY(%s)", (mo.move_byproduct_ids.ids,))

            try:
                mo.unlink()
            except Exception:
                cr.execute("DELETE FROM mrp_production WHERE id = %s", (mo.id,))
        return True
