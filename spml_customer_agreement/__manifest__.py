# -*- coding: utf-8 -*-
{
    'name': "spml_customer_agreement",
    'summary': """
        spml_customer_agreement""",
    'description': """
        spml_customer_agreement
    """,
    'author': "Magdy, helcon",
    'website': "http://www.yourcompany.com",
    'category': 'sale',
    'version': '0.1',
    'depends': ['sale'],
    'data': [
        # 'security/security.xml',
        'security/ir.model.access.csv',
        'views/sale_order.xml',
        'views/customer_agreement.xml',
    ],
}
