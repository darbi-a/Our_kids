# -*- coding: utf-8 -*-
{
    'name': "Inventory Valuation Report By Vendor",

    'summary': """
        Inventory Valuation Report By Vendor """,


    'author': "ITSS , Mahmoud Naguib",
    'website': "http://www.itss-c.com",

    'category': 'account',
    'version': '1.3',

    # any module necessary for this one to work correctly
    'depends': ['stock','product_season'],

    # always loaded
    'data': [
        'views/res_partner.xml',
        'wizard/inventory_valuation_report_vendor_wizard.xml',
        'report/report_inventory_evaluation.xml',
    ],



}