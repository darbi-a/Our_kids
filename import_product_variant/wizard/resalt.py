#-*- coding: utf-8 -*-

import base64
import csv
import os
import tempfile

import xlrd
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class resaltProductVariant(models.TransientModel):
    _name = "wizard.resalt.variant"

    count_items = fields.Integer('Number Of Items Created', readonly=True, )
    count_items_edit = fields.Integer('Number Of Items Modified', readonly=True, )
    count_variant = fields.Integer('Number Of Variant Created', readonly=True, )
    count_edit = fields.Integer('Number Of Variant Modified', readonly=True, )


    def display_count_items(self):
        print("hhhhhhhhh")
        lst_count_items = self._context['lst_count_items']
        domain = [('id', 'in', lst_count_items)]
        view_tree = {
            'name': _(' Products '),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'product.template',
            'type': 'ir.actions.act_window',
            'domain': domain,
            'readonly': True,
        }
        return view_tree
    def display_items_edit(self):
        print("hhhhhhhhh")
        context = dict(self._context) or {}
        print("self.context", self._context['lst_count_items_edit'])
        lst_count_items_edit = self._context['lst_count_items_edit']
        domain = [('id', 'in', lst_count_items_edit)]
        view_tree = {
            'name': _(' Products '),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'product.template',
            'type': 'ir.actions.act_window',
            'domain': domain,
            'readonly': True,
        }
        return view_tree
    def display_count_variant(self):
        context = dict(self._context) or {}
        lst_count_variant = self._context['lst_count_variant']
        domain = [('id', 'in', lst_count_variant)]
        view_tree = {
            'name': _(' Products '),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'product.product',
            'type': 'ir.actions.act_window',
            'domain': domain,
            'readonly': True,
        }
        return view_tree
    def display_count_edit(self):
        lst_count_edit = self._context['lst_count_edit']
        domain = [('id', 'in', lst_count_edit)]
        view_tree = {
            'name': _(' Products '),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'product.product',
            'type': 'ir.actions.act_window',
            'domain': domain,
            'readonly': True,
        }
        return view_tree




