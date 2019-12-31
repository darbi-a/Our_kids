from odoo import models,fields,api


class StockMove(models.Model):
    _inherit = "stock.move"

    vendor_id = fields.Many2one(related='purchase_line_id.partner_id',store=True)