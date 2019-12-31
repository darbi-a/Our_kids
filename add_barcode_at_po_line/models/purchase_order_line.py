from odoo import api, fields, models

#    inherit_project.task_addon_line_ids

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    Barcode = fields.Char(related='product_id.barcode')
    season_id = fields.Many2one(related='product_id.season_id')


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    total_qty_received = fields.Float(compute='compute_total_qty_received')

    @api.depends('order_line','order_line.qty_received')
    def compute_total_qty_received(self):
        for rec in self:
            rec.total_qty_received = sum(l.qty_received for l in rec.order_line)




