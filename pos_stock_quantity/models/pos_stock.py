# -*- coding: utf-8 -*-

from odoo import api, fields, models
from collections import deque

# class product_temp(models.Model):
#     _inherit = 'product.template'
#
#
#     qty_available = fields.Float(
#     'Quantity On Hand', compute='_compute_quantities2', search='_search_qty_available',)
#
#     def _compute_quantities2(self):
#
#         for rec in self:
#             qty = 0.0
#             qun = self.env['stock.quant'].search([('product_id', '=', rec.id)])
#             print('qun == >> ',qun)
#             for q in qun:
#                 if q.location_id.usage == 'internal':
#                     qty +=q.quantity
#             print('qty == >> ', qty)
#             rec.qty_available = qty
#
class product_prod(models.Model):
    _inherit = 'product.product'

    @api.multi
    def get_qty_available(self,location_id):
        return self.with_context(location=location_id).read(['qty_available'])

#
#     qty_available = fields.Float(
#     'Quantity On Hand', compute='_compute_quantities2', search='_search_qty_available',)
#
#     def _compute_quantities2(self):
#
#         for rec in self:
#             qty = 0.0
#             qun = self.env['stock.quant'].search([('product_id', '=', rec.id)])
#             print('qun == >> ',qun)
#             for q in qun:
#                 if q.location_id.usage == 'internal':
#                     qty +=q.quantity
#             print('qty == >> ', qty)
#             rec.qty_available = qty
#



class StockQuantity(models.Model):
    _inherit = 'stock.quant'

    @api.model
    def get_qty_available(self, location_id, location_ids=None, product_ids=None):
        if location_id:
            root_location = self.env['stock.location'].search([('id', '=', location_id)])
            all_location = [root_location.id]
            queue = deque([])
            self.location_traversal(queue, all_location, root_location)
            stock_quant = self.search_read([('location_id', 'in', all_location)], ['product_id', 'quantity', 'location_id'])
            return stock_quant
        else:
            stock_quant = self.search_read([('location_id', 'in', location_ids), ('product_id', 'in', product_ids)],
                                           ['product_id', 'quantity', 'location_id'])
            return stock_quant

    def location_traversal(self, queue, res, root):
        for child in root.child_ids:
            if child.usage == 'internal':
                queue.append(child)
                res.append(child.id)
        while queue:
            pick = queue.popleft()
            res.append(pick.id)
            self.location_traversal(queue, res, pick)

    @api.model
    def create(self, vals):
        print('location_id == ',vals['location_id'])
        root_location = self.env['stock.location'].search([('id', '=', vals['location_id'])])
        if root_location.usage != 'internal':
            return True

        res = super(StockQuantity, self).create(vals)
        if res.location_id.usage == 'internal':
            self.env['pos.stock.channel'].broadcast(res)
        if res.location_id.usage != 'internal':
            print("Deleted Rec")
            res.unlink()
            return True
        return res

    @api.multi
    def write(self, vals):
        record = self.filtered(lambda x: x.location_id.usage == 'internal')
        self.env['pos.stock.channel'].broadcast(record)
        return super(StockQuantity, self).write(vals)


class PosConfig(models.Model):
    _inherit = 'pos.config'

    show_qty_available = fields.Boolean(string='Display Stock in POS')
    location_only = fields.Boolean(string='Only in POS Location')
    allow_out_of_stock = fields.Boolean(string='Allow Out-of-Stock')
    limit_qty = fields.Integer(string='Deny Order when Quantity Available lower than')
    hide_product = fields.Boolean(string='Hide Products not in POS Location')


class PosStockChannel(models.TransientModel):
    _name = 'pos.stock.channel'
    _description = 'Pos Stock Channel'

    def broadcast(self, stock_quant):
        data = stock_quant.read(['product_id', 'location_id', 'quantity'])
        for d in data:
            d['type'] = 'pos.stock.channel'
        partners = self.env['res.users'].search([]).mapped('partner_id')
        for partner in partners:
            self.env['bus.bus'].sendone((self._cr.dbname, 'res.partner',partner.id), data)
