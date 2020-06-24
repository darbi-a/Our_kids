# -*- coding: utf-8 -*-
import math
from dateutil.relativedelta import relativedelta
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from odoo.tools import float_is_zero


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.constrains('partner_id','move_ids_without_package')
    def check_picking_moves_vendor(self):
        if self.picking_type_id.code == 'incoming':
            vendor_num = self.partner_id.ref
            if vendor_num and self.partner_id.supplier:
                for move in self.move_ids_without_package:
                    product_vendor_num = move.product_id.vendor_num
                    if product_vendor_num and vendor_num != product_vendor_num:
                        raise ValidationError(_('The product %s is not belong to this partner' %self.product_id.display_name))

    # @api.constrains('picking_type_id','move_ids_without_package','state')
    # def check_internal_transfer(self):
    #     for pick in self:
    #         if pick.picking_type_id.code == 'internal':
    #             for move in pick.move_ids_without_package:
    #                 if move.product_uom_qty < move.quantity_done :
    #                     raise ValidationError(_('Initial demand can not be less than quantity done'))

    @api.multi
    def action_confirm(self):
        print('new picking')
        new_picking = self.improve_manual_route()
        res = super(StockPicking,self).action_confirm()
        if new_picking:
            super(StockPicking, new_picking).action_confirm()
        return res

    @api.multi
    def improve_manual_route(self):
        rule = self.env['stock.rule'].search([('location_src_id','=',self.location_dest_id.id),('action','=','push'),('auto','=','manual')],limit=1)
        route = rule.route_id
        moves = self.move_lines.filtered(lambda move: move.state == 'draft')
        new_picking = self.env['stock.picking']
        i = 0
        print(moves)
        print(rule)
        if self.picking_type_id.code == 'internal' and rule and moves:

            picking_values = {
                'origin': self.name ,
                'company_id': rule.company_id.id,
                'move_type': self.group_id and self.group_id.move_type or 'direct',
                'partner_id': self.partner_id.id,
                'picking_type_id': rule.picking_type_id.id,
                'location_id': self.location_dest_id.id,
                'location_dest_id': rule.location_id.id,
            }
            new_picking = self.env['stock.picking'].create(picking_values)
            for move in moves:
                move._action_confirm_without_push()

            moves_limit = 300
            num_pages = int(math.ceil(len(moves)/moves_limit))
            for p in range(num_pages):
                sql_query = ""
                insert_values = ""
                separator = " "
                for move in moves[p*moves_limit:(p+1)*moves_limit]:
                    new_date = fields.Datetime.to_string(move.date_expected + relativedelta(days=rule.delay))
                    if insert_values:
                        separator = ' , '
                    insert_values += separator + " (nextval('stock_move_id_seq'), %s, (now() at time zone 'UTC'), %s, (now() at time zone 'UTC'), %s, %s, '%s', '%s', %s, %s, %s, %s, '%s', '%s', '%s', %s, %s, %s, %s, %s, '%s', %s, %s, %s, %s, %s, %s, %s, %s, %s, '%s', %s, %s, %s, '%s')" %(
                        self.env.uid,
                        self.env.uid,
                        move.additional,
                        rule.company_id.id,
                        new_date,
                        new_date,
                        move.group_id.id or 'NULL',
                        move.inventory_id.id or 'NULL',
                        rule.location_id.id or 'NULL',
                        move.location_dest_id.id or 'NULL',
                        move.name,
                        move.note or '',
                        move.origin or '',
                        move.package_level_id.id or 'NULL',
                        move.partner_id.id or 'NULL',
                        new_picking.id or 'NULL',
                        rule.picking_type_id.id or 'NULL',
                        move.priority,
                        move.procure_method,
                        move.product_id.id or 'NULL',
                        move.product_packaging.id or 'NULL',
                        move.product_uom.id or 'NULL',
                        move.product_uom_qty,
                        rule.propagate,
                        move.restrict_partner_id.id or 'NULL',
                        move.rule_id.id or 'NULL',
                        move.scrapped,
                        move.sequence,
                        'draft',
                        rule.warehouse_id.id or 'NULL',
                        move.id or 'NULL',
                        move.product_qty,
                        new_picking.name or ''
                    )
                    sql_query = "INSERT INTO stock_move (id, create_uid, create_date, write_uid, write_date, additional, company_id, date, date_expected, group_id, inventory_id, location_dest_id, location_id, name, note, origin, package_level_id, partner_id, picking_id, picking_type_id, priority, procure_method, product_id, product_packaging, product_uom, product_uom_qty, propagate, restrict_partner_id, rule_id, scrapped, sequence, state, warehouse_id, push_move_id, product_qty, reference) VALUES %s RETURNING id " %(insert_values)
                self._cr.execute(sql_query)
                new_move_ids = []
                for l in self._cr.fetchall():
                    new_move_ids.append(l[0])
                new_moves = self.env['stock.move'].browse(new_move_ids)
                for move in new_moves:
                    print(i)
                    i += 1
                    move.push_move_id.write({'move_dest_ids': [(4, move.id)]})
        self.invalidate_cache()
        moves._merge_moves(merge_into=False)
        # new_picking.mapped('move_lines')._compute_product_qty()
        return new_picking





