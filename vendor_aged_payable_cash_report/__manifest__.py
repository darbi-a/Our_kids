# -*- coding: utf-8 -*-
{
    'name': "Vendor Aged Payable Cash",

    'summary': """
        Vendor Aged Payable Cash """,


    'author': "ITSS , Mahmoud Naguib",
    'website': "http://www.itss-c.com",

    'category': 'account',
    'version': '1.3',

    # any module necessary for this one to work correctly
    'depends': ['account','sale','purchase'],

    # always loaded
    'data': [
        'wizard/vendor_aged_payable_cash_report_wizard.xml',
        'report/report_vendor_aged_payable_cash.xml',
    ],



}