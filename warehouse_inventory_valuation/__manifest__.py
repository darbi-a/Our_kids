{
    'name': 'Inventory Valuation Report By Warehouse',
    'version': '12.3',
    'category': 'Inventory',
    'summary': 'Calculate Inventory Valuation Report By Warehouse',
    'description': """ Using this module you can get  Inventory Valuation Report By Warehouse.
    """,
    'author': 'Ahmed Amin',
    'depends': ['base', 'stock',],
    'data': [
             'wizard/warehouse_product_wizard_view.xml',
             'report/report.xml',
             'report/report_stock_inventory.xml',
    ],
    'qweb': [
        ],
    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': False,
}
