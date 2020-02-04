# -*- coding: utf-8 -*-

{
    "name": "Price List By Vendor",
    'version': '12.0.1.0.0',
    "author" : "Ahmed Amen",

    'summary': """
       This addon allow to make price-list for vendors  """,
    'category': 'Sales',
    "depends": ['base',"product",'sale','import_product_variant','point_of_sale'],
    "license": "LGPL-3",
    "data": [
        #'views/product_view.xml',
        'views/pricelist_view.xml'
    ],

    "installable": True,
}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
