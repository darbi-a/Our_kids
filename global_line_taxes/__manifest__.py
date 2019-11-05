# coding: utf-8
##############################################################################
#
#
##############################################################################

{
    'name': 'Global Taxes',
    'version': '12.2',
    'author': 'Ahmed Amen',
    'license': 'AGPL-3',
    'category': 'Sales',
    'summary': 'this addons add global tax in SO,PO,Customer Invoice and Vendor Bill',
    'depends': ['base',
                'sale',
                ],
    'data': [
        # 'views/sales_team.xml',
        # 'security/lead.xml',

        'views/sales.xml',
        'views/purchase.xml',
        'views/invoice.xml',
        # 'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': True,
    'demo': [],
    'test': []
}
