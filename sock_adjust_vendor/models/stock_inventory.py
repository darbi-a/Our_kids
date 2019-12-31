# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from datetime import datetime
from dateutil.relativedelta import relativedelta
import logging

LOGGER = logging.getLogger(__name__)


class StockInventory(models.Model):
    _inherit = 'stock.inventory'

    # filter = fields.Selection(selection_add=[('vendors','Vendors')])

    vendor_ids = fields.Many2many(comodel_name="res.partner",domain=[('supplier','=',True)])

    @api.model
    def _selection_filter(self):
        res_filter = super(StockInventory,self)._selection_filter()
        res_filter.append(('vendors','Vendors'))
        return res_filter

    @api.onchange('filter')
    def _onchange_filter(self):
        res = super(StockInventory, self)._onchange_filter()
        if self.filter != 'vendors':
            self.vendor_ids = False
        return res

    @api.one
    @api.constrains('filter', 'product_id', 'lot_id', 'partner_id', 'package_id')
    def _check_filter_product(self):
        super(StockInventory,self)._check_filter_product()
        if self.filter != 'vendors' and self.vendor_ids:
            raise ValidationError(_('The selected vendors don\'t have the proprietary of that product.'))

    def _get_inventory_lines_values(self):
        if self.vendor_ids:
            locations = self.env['stock.location'].search([('id', 'child_of', [self.location_id.id])])
            domain = ' location_id in %s AND quantity != 0 AND active = TRUE'
            args = (tuple(locations.ids),)

            vals = []
            Product = self.env['product.product']
            # Empty recordset of products available in stock_quants
            quant_products = self.env['product.product']
            # Empty recordset of products to filter
            products_to_filter = self.env['product.product']

            # case 0: Filter on company
            if self.company_id:
                domain += ' AND company_id = %s'
                args += (self.company_id.id,)

            if self.vendor_ids:
                vendor_nums = self.vendor_ids.filtered(lambda v:v.ref).mapped('ref')
                vendor_products = Product.search([('vendor_num', 'in', vendor_nums)])
                vendor_product_info = self.env['product.supplierinfo'].search([('name', 'in', self.vendor_ids.ids)])
                vendor_products |= vendor_product_info.mapped('product_id')
                domain += ' AND product_id = ANY (%s)'
                args += (vendor_products.ids,)
                products_to_filter |= vendor_products

            self.env.cr.execute("""SELECT product_id, sum(quantity) as product_qty, location_id, lot_id as prod_lot_id, package_id, owner_id as partner_id
                FROM stock_quant
                LEFT JOIN product_product
                ON product_product.id = stock_quant.product_id
                WHERE %s
                GROUP BY product_id, location_id, lot_id, package_id, partner_id """ % domain, args)

            for product_data in self.env.cr.dictfetchall():
                # replace the None the dictionary by False, because falsy values are tested later on
                for void_field in [item[0] for item in product_data.items() if item[1] is None]:
                    product_data[void_field] = False
                product_data['theoretical_qty'] = product_data['product_qty']
                if product_data['product_id']:
                    product_data['product_uom_id'] = Product.browse(product_data['product_id']).uom_id.id
                    quant_products |= Product.browse(product_data['product_id'])
                vals.append(product_data)
            if self.exhausted:
                exhausted_vals = self._get_exhausted_inventory_line(products_to_filter, quant_products)
                vals.extend(exhausted_vals)
        else:
            vals = super(StockInventory,self)._get_inventory_lines_values()

        return vals