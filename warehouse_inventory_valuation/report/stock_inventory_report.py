# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime, date


class stock_inventory_report(models.AbstractModel):
    _name = 'report.warehouse_inventory_valuation.report_stock_inventory'

    @api.model
    def _get_report_values(self, docids, data=None):
        report = self.env['ir.actions.report']._get_report_from_name('warehouse_inventory_valuation.report_stock_inventory')
        record_id = data['form']['id'] if data and data['form'] and data['form']['id'] else docids[0]
        records = self.env['warehouse.inventory.wizard'].browse(record_id)
        return {
           'doc_model': report.model,
           'docs': records,
           'data': data,
            'get_inventory': self.get_inventory,
            'get_valuation': self.get_valuation,
            'get_products':self._get_products,
        }

    def get_location(self, records, warehouse):
        stock_ids = []
        location_obj = self.env['stock.location']
        domain = [('company_id', '=', records.company_id.id), ('usage', '=', 'internal')]

        stock_ids.append(warehouse.view_location_id.id)
        print("stock_ids == ",stock_ids)
        print("stock_ids222 == ",warehouse.view_location_id)
        domain.append(('location_id', 'child_of', stock_ids))
        final_stock_ids = location_obj.search(domain).ids
        return final_stock_ids

    def _get_products(self, record,warehouse):
        product_ids = []
        locations = self.get_location(record,warehouse)
        for loc in locations:
            print("loc ** == ", loc)
            list_product = self.env['product.product'].with_context({'location': loc}).search([('type', '=', 'product')])
            if list_product:
                print("list_product ** == ", list_product)
                product_ids = list(set(product_ids + list_product.ids))

        products = self.env['product.product'].browse(product_ids)
        return products

    def get_valuation(self, record, product, warehouse):
        print(" ** get_valuation warehouse** ",warehouse)
        print(" ** get_valuation record** ",record)
        print(" ** get_valuation product** ",product)
        value = 0.0
        locations = self.get_location(record, warehouse)
        print(" ** get_valuation locations ** ", locations)
        lst_moves = self.env['stock.move'].search([('product_id', '=', product.id),('state', '=', 'done'),'|',('location_id', 'in', locations),('location_dest_id', '=', locations)])
        print("lst_moves ** == ", lst_moves)
        for mov in lst_moves:
            print("mov ** == ", mov)
            value += mov.value
        print("value ** == ", value)
        return value


    def get_inventory(self, record, product, warehouse):
        print("record == ",record)
        print("product == ",product)
        print("warehouse == ",warehouse)
        locations = self.get_location(record, warehouse)
        print("locations == ", locations)
        if isinstance(product, int):
            product_data = product
            print("product_data11 == ", product_data)
        else:
            product_data = product.id
            print("product_data22 == ", product_data)

        self._cr.execute(''' 
                        SELECT coalesce(sum(qty), 0.0) as qty
                        FROM
                            ((
                            SELECT pp.id, pp.default_code,m.date,
                                CASE when pt.uom_id = m.product_uom 
                                THEN u.name 
                                ELSE (select name from uom_uom where id = pt.uom_id) 
                                END AS name,

                                CASE when pt.uom_id = m.product_uom
                                THEN coalesce(sum(-m.product_qty)::decimal, 0.0)
                                ELSE coalesce(sum(-m.product_qty * pu.factor / u.factor )::decimal, 0.0) 
                                END AS qty

                            FROM product_product pp 
                            LEFT JOIN stock_move m ON (m.product_id=pp.id)
                            LEFT JOIN product_template pt ON (pp.product_tmpl_id=pt.id)
                            LEFT JOIN stock_location l ON (m.location_id=l.id)    
                            LEFT JOIN stock_picking p ON (m.picking_id=p.id)
                            LEFT JOIN uom_uom pu ON (pt.uom_id=pu.id)
                            LEFT JOIN uom_uom u ON (m.product_uom=u.id)
                            WHERE (m.location_id in %s) AND m.state='done' AND pp.active=True AND pp.id = %s
                            GROUP BY  pp.id, pt.uom_id , m.product_uom ,pp.default_code,u.name,m.date
                            ) 
                            UNION ALL
                            (
                            SELECT pp.id, pp.default_code,m.date,
                                CASE when pt.uom_id = m.product_uom 
                                THEN u.name 
                                ELSE (select name from uom_uom where id = pt.uom_id) 
                                END AS name,
                                CASE when pt.uom_id = m.product_uom 
                                THEN coalesce(sum(m.product_qty)::decimal, 0.0)
                                ELSE coalesce(sum(m.product_qty * pu.factor / u.factor )::decimal, 0.0) 
                                END  AS qty
                            FROM product_product pp 
                            LEFT JOIN stock_move m ON (m.product_id=pp.id)
                            LEFT JOIN product_template pt ON (pp.product_tmpl_id=pt.id)
                            LEFT JOIN stock_location l ON (m.location_dest_id=l.id)    
                            LEFT JOIN stock_picking p ON (m.picking_id=p.id)
                            LEFT JOIN uom_uom pu ON (pt.uom_id=pu.id)
                            LEFT JOIN uom_uom u ON (m.product_uom=u.id)
                            WHERE (m.location_dest_id in %s) AND m.state='done' AND pp.active=True AND pp.id = %s
                            GROUP BY  pp.id,pt.uom_id , m.product_uom ,pp.default_code,u.name,m.date
                            ))
                        AS foo
                        GROUP BY id
                    ''', (tuple(locations), product_data, tuple(locations), product_data))

        res = self._cr.dictfetchone()
        print("res == ",res)
        if res:
            return res.get('qty') if res.get('qty') else 0.00
        else:
            return 0.00

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: