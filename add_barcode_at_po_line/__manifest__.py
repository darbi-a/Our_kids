
# -*- coding: utf-8 -*-
{
    'name': "Add Barcode At Po Line",
    'summary': """ inherit barcode and season feilds at Po Line  & 
    hide duplicate action and inherit in Requests for Quotation qty_received field at tree view """,
    'author': "khalil al shareef, ITSS <https://www.itss-c.com>",
    'category': 'purchase',
    'version': '12.0.0',
    'depends': ['product_season','purchase'],
    'data': [

        #'security/ir.model.access.csv',
        'views/purchase_order.xml',
    ]
}
