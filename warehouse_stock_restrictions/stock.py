# -*- coding: utf-8 -*-

from openerp import models, fields, api, _
from openerp.exceptions import Warning

class ResUsers(models.Model):
    _inherit = 'res.users'

    restrict_locations = fields.Boolean('Restrict Location')

    stock_location_ids = fields.Many2many(
        'stock.location',
        'location_security_stock_location_users',
        'user_id',
        'location_id',
        'Stock Locations')

    default_location_id = fields.Many2one(comodel_name="stock.location" )

    default_picking_type_ids = fields.Many2many(
        'stock.picking.type', 'stock_picking_type_users_rel',
         column2='user_id',  column1='picking_type_id', string='Default Warehouse Operations')


class stock_move(models.Model):
    _inherit = 'stock.move'

    @api.one
    @api.constrains('state', 'location_id', 'location_dest_id')
    def check_user_location_rights(self):
        if self.state == 'draft' or self.picking_type_id.code == 'internal':
            return True
        user_locations = self.env.user.stock_location_ids
        if self.env.user.restrict_locations and self.picking_type_id.code != 'internal':
            message = _(
                'Invalid Location. You cannot process this move since you do '
                'not control the location "%s". '
                'Please contact your Adminstrator.')
            if self.location_id not in user_locations:
                raise Warning(message % self.location_id.name)
            elif self.location_dest_id not in user_locations:
                raise Warning(message % self.location_dest_id.name)


class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    allowed_users = fields.Many2many(comodel_name="res.users", relation="stock_picking_type_users_rel", column1="user_id", column2="picking_type_id")

    def _get_action(self, action_xmlid):
        action = self.env.ref(action_xmlid).read()[0]
        pickings = self.env['stock.picking'].search([('picking_type_id','=',self.id)])
        action['domain'] = [('id','in',pickings.ids)]
        if self:
            action['display_name'] = self.display_name
        return action


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    allowed_users = fields.Many2many(related='picking_type_id.allowed_users')




