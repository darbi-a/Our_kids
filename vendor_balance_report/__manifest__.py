# -*- coding: utf-8 -*-
{
    'name': "Vendor Balance Report",

    'summary': """
        Vendor Balance Report """,


    'author': "ITSS , Mahmoud Naguib",
    'website': "http://www.itss-c.com",

    'category': 'account',
    'version': '1.3',

    # any module necessary for this one to work correctly
    'depends': ['account','stock'],

    # always loaded
    'data': [
        'views/res_partner.xml',
        'wizard/vendor_balance_report_wizard.xml',
        'report/report_vendor_balance.xml',
    ],



}