import sagepay
from sagepay import SagePayAPI

from sagepay import wrappers
ACCEPTED_OPTIONS = {
		'cv2': '555',
		# 'issue_number': '1',
		'start_date': '0514',
	}
ACCEPTED_OPTIONS_T = {
		# Python Key / SagePay Key
		'account_type': 'M',
		'apply_3d_secure': '0',
		'apply_avs_cv2': '0',
		'basket': '',
		'client_ip_address': '202.131.126.142',
		'contact_number': '7804333130',
		'contact_fax': '',
		'contact_email': 'k@m.com',
		'customer_name': 'Mirza',
		'gift_aid_payment': '0',

		'billing_firstname': 'Kazim',
		'billing_surname': 'Mirza',
		#'billing_address': 'BillingAddress',
		'billing_address1': '29',
		'billing_city': 'Nelson',
		'billing_country': 'GB',
		'billing_post_code': 'BB90SH',

		'delivery_firstname': 'Kazim',
		'delivery_surname': 'Mirza',
		'delivery_address1': '29',
		'delivery_city': 'Nelson',
		'delivery_country': 'GB',
		'delivery_post_code': 'BB90SH',

		# Special attribute for PayPal intergration. Can only
		# be used is Card has a type 'PAYPAL'
		# 'paypal_url': '',
	}
aaa = wrappers.SagePayCard('kazim', '5404000000000001', 'MC', '0715',**ACCEPTED_OPTIONS)
bbb = wrappers.SagePayTransaction('PAYMENT', 'kkkkkk', '100', 'GBP', 'asasas',aaa,**ACCEPTED_OPTIONS_T)