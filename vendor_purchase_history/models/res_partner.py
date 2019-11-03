# © 2018-Today Aktiv Software (http://www.aktivsoftware.com).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models, fields ,_


class ResPartner(models.Model):
    _inherit = "res.partner"
    vendor_purchase_count = fields.Integer(string='',
                                           compute='_compute_vendor_purchase_count')

    @api.multi
    def _compute_vendor_purchase_count(self):
        PurchaseOrder = self.env['purchase.order.line']
        for partner in self:
            partner.vendor_purchase_count = PurchaseOrder.search_count(
                [('partner_id', 'child_of', partner.id)])



class stock_return_picking(models.TransientModel):
    _inherit = "stock.return.picking"


    purchase_count = fields.Integer(string='Purchase',compute='_compute_purchase_count')
    ven_purchase_count = fields.Integer(string='Purchase count ',compute='_compute_purchase_count')


    @api.one
    @api.depends('product_return_moves')
    def _compute_purchase_count(self):
        prod_ids = []
        for line in self.product_return_moves:
            prod_ids.append(line.product_id.id)
        PurchaseOrder = self.env['purchase.order.line']
        self.purchase_count = PurchaseOrder.search_count([('partner_id', 'child_of', self.picking_id.partner_id.id),('product_id','in',prod_ids)])

    @api.multi
    def action_open_history(self):
        for rec in self:
            prod_ids = []
            for line in rec.product_return_moves:
                prod_ids.append(line.product_id.id)
            purchase = self.env['purchase.order.line'].search([('partner_id', 'child_of', rec.picking_id.partner_id.id),('product_id','in',prod_ids)])
            domain = [('id', 'in',purchase.ids )]
            view_tree = {
                'name': _(' Purchase History '),
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'purchase.order.line',
                'type': 'ir.actions.act_window',
                'domain': domain,
                'readonly': True,
            }
            return view_tree
