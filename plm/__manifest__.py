# -*- coding: utf-8 -*-
{
    'name': 'waleed_factory',
    'summary': "waleed factory",
    'description': """
        origanising the process of the factory from a to z
    """,
    'author': "abdelrhman",
    'website': "http://www.yourcompany.com",
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Marketing',
    'version': '0.1',
    # any module necessary for this one to work correctly
    'depends': ['base'],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'wizard/submission.xml',
        'views/parts.xml',
        'views/process.xml',
        'views/products.xml',
        'views/workers.xml',
    ],
    "sequence": 1,
    'application': True,
}
