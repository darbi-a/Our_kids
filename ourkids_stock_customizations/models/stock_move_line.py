from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    @api.constrains('product_qty','qty_done')
    def check_qty_done(self):
        for rec in self:
            if rec.move_id.picking_code == 'internal' and rec.move_id.product_qty > 0 and rec.qty_done > rec.move_id.product_qty:
                raise ValidationError(_('Initial demand can not be less than quantity done'))
