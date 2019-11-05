# -*- coding: utf-8 -*-

from odoo import api, fields, models, _,exceptions
from datetime import timedelta
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError


# class pricelist_item(models.Model):
#     _inherit = 'product.pricelist.item'
#
#     @api.constrains('name')
#     def _check_fields(self):
#         print ("*** 999  duplicate****")
#         rec = {
#             'name': self.name,
#             'quantity': self.min_quantity,
#             'date_start': self.date_start,
#             'date_end': self.date_end,
#             'price': self.price,
#             'applied_on': self.applied_on,
#             'compute_price': self.compute_price,
#         }
#         lst_values = self.pricelist_id.check_item_value()
#         print("lst_value == ", lst_values)
#         if rec in lst_values:
#             print ("*** duplicate****")
#         else:
#             print ("*** NO duplicate****")


class price_list(models.Model):
    _inherit = 'product.pricelist'

    def check_item_value(self,price_list,ex_line):
        items=[]

        if 'name' in ex_line:
            del ex_line['name']
        if 'applied_on' in ex_line:
            del ex_line['applied_on']
        if 'compute_price' in ex_line:
            del ex_line['compute_price']
        if 'date_start' in ex_line:
            del ex_line['date_start']
        if 'date_end' in ex_line:
            del ex_line['date_end']
        if price_list.item_ids:
            for line in price_list.item_ids:
                rec={
                    'categ_id':line.categ_id.name or '',
                    'product_barcode':line.product_tmpl_id.barcode or '',
                    'variant_barcode':line.product_id.barcode or '',
                    'fixed':line.fixed_price or '',
                    'percentage':line.percent_price or '',
                    'qty':line.min_quantity or '',
                }
                items.append(rec)
        if items.count(ex_line) >= 1:
            return True
        else:
            return False



