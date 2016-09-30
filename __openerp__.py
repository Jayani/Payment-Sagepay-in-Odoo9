# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Payment SagePay Payment Acquirer',
    'category': 'Hidden',
    'summary': 'Payment Acquirer: Payment SagePay Implementation',
    'version': '9.0.1.0.0',
    'description': """Payment SagePay Payment Acquirer""",
    'author': 'Serpent Consulting Services Pvt. Ltd.',
    'depends': ['payment', 'website_sale', 'sale', 'account'],
    'data': [
        'views/sagepay_button.xml',
        'views/sagepay.xml',
        'views/payment_acquirer.xml',
        'wizard/wiz_payment_sagepay_view.xml',
        'views/sale_view.xml',
        'views/account_invoice_view.xml',
        'views/payment_transaction_view.xml',
        'views/threed.xml',
        'views/failed.xml',
        'data/sage_pay.xml',
    ],
    'installable': True,
}
