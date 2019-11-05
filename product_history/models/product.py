# -*- coding: utf-8 -*-
""" init object """
from odoo import fields, models, api


import logging

LOGGER = logging.getLogger(__name__)

class ProductProduct(models.Model):
    _inherit = 'product.template'

    activity = fields.Text(string="Activitys", required=False, compute='onchange_method',store=True)

    @api.one
    @api.depends('activity_ids')
    def onchange_method(self):
        for rec in self:
            lst_text = []
            txt = 'Update By '
            if not rec.activity_ids:
                txt = 'No update'
                rec.activity = txt
                return True
            else:

                rec.activity = txt
                last=len(rec.activity_ids.ids)-1
                print('## ******************  ####,rec.activity_ids == ', rec.activity_ids)
                print('## ******************  ####,lenth ids == ',len(rec.activity_ids.ids) )
                print('## ******************  ####,Last ids == ',rec.activity_ids[last] )
                last_update=rec.activity_ids[last]
                # date1 = datetime.strptime(line.date_deadline, "%Y-%m-%d")
                print('## ******************  ', last_update)
                date2 = last_update.create_date.strftime("%d/%m/%Y, %H:%M:%S")
                rec.activity += 'User:[' + last_update.user_id.name + '] Make activity Of Type:[' + last_update.activity_type_id.name + '] In Date:[' + date2 + "] And It's State is:[" + last_update.state +']'

