# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
try:
    import simplejson as json
except ImportError:
    import json
import time
import logging
import openerp
from openerp import http
from openerp.http import request
from sagepay import SagePayAPI
from sagepay import wrappers
from requests import get
from openerp import workflow
from openerp import SUPERUSER_ID

_logger = logging.getLogger(__name__)


class website_sale(openerp.addons.website_sale.controllers.main.website_sale):

    @http.route('/sagepay', type='http', auth='public', csrf=False, website=True)
    def payment_sagepay(self, transaction_id=None, sale_order_id=None, **post):
        fo = open('/tmp/sagepaytext.text', 'wb')
        fo.write(str(post))
        tran_obj = request.env['payment.acquirer']
        so_obj = request.env['sale.order']
        inv_obj = request.env['account.invoice']
        pay_acq_ids = tran_obj.sudo().search([('provider', '=', 'sagepay')])
        base_url = request.env['ir.config_parameter'].get_param('web.base.url')
        client_ip = get('https://l2.io/ip').text
        if pay_acq_ids.environment == 'test':
            environment = 'test'
        if pay_acq_ids.environment == 'prod':
            environment = 'live'
        vendor_id = pay_acq_ids.sage_pay_vendor_account
        tran_obj = request.env['payment.transaction']
        if not transaction_id:
            try:
                tx = request.website.sudo().sale_get_transaction()
            except:
                tx = tran_obj.search([('sale_order_id', '=', request.session.get('sale_last_order_id'))])
        else:
            tx = tran_obj.sudo().browse(transaction_id)
        if sale_order_id is None:
            order = request.website.sale_get_order()
        else:
            order = so_obj.sudo().browse(sale_order_id)
            assert order.id == request.session.get('sale_last_order_id')
        if post.get('SO'):
            if not post.get('Paypal'):
                response = SagePayAPI(vendor_id, environment).authorize(post.get('MD'),post.get('PaRes')).__dict__
                if response['_args'].get('3DSecureStatus') == 'OK':
                    if response.get('_args')['Status'] == 'OK':
                        order.sudo().write({'order_policy': 'prepaid'})
                        so_obj.sudo().action_confirm([order.id])
                        inv_ids = order.sudo().action_view_invoice()
                        inv_id = inv_ids['res_id']
                        acc_inv = inv_obj.sudo().browse([inv_id])
                        inv_obj.sudo().write([inv_id], {'payment_ref_id': tx.id})
                        inv_obj.sudo().signal_workflow([inv_id], 'invoice_open')
                        inv_obj.sudo().invoice_pay_customer([inv_id])
                        tran_obj.sudo().create_voucher(acc_inv)
                tx.write({'state': 'done', 'SecurityKey': response.get('_args').get('SecurityKey'), 'TxAuthNo': response.get('_args').get('TxAuthNo'), 'VPSTxId':  response.get('_args').get('VPSTxId')})
                request.website.sale_reset()
                return request.redirect("/shop/confirmation")
            if post.get('Paypal'):
                response = SagePayAPI(vendor_id, environment).paypal_capture(tx.VPSTxId, str(tx.amount), True)
                if response.__dict__.get('_args')['Status'] == 'OK':
                    so_obj.sudo().write([order.id], {'order_policy': 'prepaid'})
                    order.sudo().action_confirm()
                    inv_ids = so_obj.sudo().action_view_invoice([order.id])
                    inv_id = inv_ids['res_id']
                    acc_inv = inv_obj.sudo().browse([inv_id])
                    inv_obj.sudo().write([inv_id], {'payment_ref_id': tx.id})
                    inv_obj.sudo().signal_workflow([inv_id], 'invoice_open')
                    inv_obj.sudo().invoice_pay_customer([inv_id])
                    tran_obj.sudo().create_voucher(acc_inv)
                    response = response.__dict__
                    tx.write({'state': 'done', 'SecurityKey': response.get('_args').get('SecurityKey'), 'TxAuthNo': response.get('_args').get('TxAuthNo'), 'VPSTxId':  response.get('_args').get('VPSTxId')})
                    request.website.sale_reset()
                    return request.redirect("/shop/confirmation")
        ACCEPTED_OPTIONS = {
            'cv2': post.get('cardCVC'),
            # 'issue_number': '1',
            # 'start_date': '0514',
        }
        ACCEPTED_OPTIONS_T = {
            # Python Key / SagePay Key
            'account_type': 'E',
            'apply_3d_secure': '0',
            'apply_avs_cv2': '0',
            'client_ip_address': client_ip,
            'contact_number': order.partner_id.phone,
            'customer_name': order.partner_id.name,
            'gift_aid_payment': '0',
            'contact_email': order.partner_invoice_id.email,
            'billing_firstname': order.partner_invoice_id.name,
            'billing_surname': post.get('cardholdersurname'),
#             'billing_address': 'BillingAddress',
            'billing_address1': order.partner_invoice_id.street,
            'billing_address2': order.partner_invoice_id.street2,
            'billing_city': order.partner_invoice_id.city,
            'billing_country': order.partner_invoice_id.country_id.code,
            'billing_post_code': order.partner_invoice_id.zip,
            
            'delivery_firstname': order.partner_shipping_id.name,
            'delivery_surname': post.get('cardholdersurname'),
            'delivery_address1': order.partner_shipping_id.street,
            'delivery_address2': order.partner_shipping_id.street2,
            'delivery_city': order.partner_shipping_id.city,
            'delivery_country': order.partner_shipping_id.country_id.code,
            'delivery_post_code': order.partner_shipping_id.zip,
            'delivery_phone': order.partner_shipping_id.phone,
            'send_email': 0,
        }
        if order.partner_invoice_id.state_id:
            ACCEPTED_OPTIONS_T.update({'billing_state': order.partner_invoice_id.state_id.code})
        if order.partner_shipping_id.state_id:
            ACCEPTED_OPTIONS_T.update({'delivery_state': order.partner_shipping_id.state_id.code})
        fo = open('/tmp/sagepaytext_info.text', 'wb')
        fo.write(str(ACCEPTED_OPTIONS_T))
        if post.get('card_name') == 'PAYPAL':
            ACCEPTED_OPTIONS_T.update({'paypal_url': '%s/sagepay?SO=%s&Paypal=True' % (base_url,tx.sale_order_id.name)})
            card_request = wrappers.SagePayCard(post.get('cardholder'), post.get('cardNumber'), post.get('card_name'), post.get('cardExpiry'), **ACCEPTED_OPTIONS)
        if post.get('card_name') and post.get('card_name') != 'PAYPAL':
            card_request = wrappers.SagePayCard(post.get('cardholder'), post.get('cardNumber'), post.get('card_name'), post.get('cardExpiry').replace('/', ''), **ACCEPTED_OPTIONS)
        if not post.get('card_name'):
            order.write({'name': order.name + 'Re'})
            return request.redirect("/shop/payment")
        order_name = order.name + '-' + time.strftime('%Y%m%d%H%M%S')
        payment_request = wrappers.SagePayTransaction('PAYMENT', order_name, str(tx.amount), order.currency_id.name, tx.sale_order_id.name, card_request, **ACCEPTED_OPTIONS_T)
        response = SagePayAPI(vendor_id, environment).register(payment_request).__dict__
        if response.get('_args')['Status'] == 'INVALID' and '4042' in str(response.get('_args')['StatusDetail']):
            order.write({'name': order.name + 'Re'})
            payment_request = wrappers.SagePayTransaction('PAYMENT', order.name, str(tx.amount), order.currency_id.name, tx.sale_order_id.name, card_request, **ACCEPTED_OPTIONS_T)
            response = SagePayAPI(vendor_id, environment).register(payment_request).__dict__
        if response.get('_args')['Status'] == 'INVALID' and '4042' not in str(response.get('_args')['StatusDetail']):
            error = str(response.get('_args')['StatusDetail']).replace(':', '')
            kwargs = {
                'error': error,
            }
            return request.website.render('payment_sagepay.Failed', kwargs)
        if response.get('_args')['Status'] == 'PPREDIRECT':
            tx.write({'VPSTxId': response.get('_args')['VPSTxId']})
            return request.redirect(response.get('_args')['PayPalRedirectURL'])
        if response.get('_args')['Status'] == '3DAUTH':
            kwargs = {
                'ACSURL': response['_args'].get('ACSURL'),
                'MD': response['_args'].get('MD'),
                'PaReq': response['_args'].get('PAReq'),
                'TermUrl': '%s/sagepay?SO=%s' % (base_url, tx.sale_order_id.name)
            }
            return request.website.render("payment_sagepay.Thank_you", kwargs)
        if response.get('_args')['Status'] == 'OK':
            tx.write({'state':'done'})
        order.sudo().write({'order_policy': 'prepaid'})
        so_line = request.env['sale.order.line']
        line = so_line.sudo().search([('order_id', '=', order.id)])
        for item in line:
            item.qty_delivered = item.product_uom_qty
        order.sudo().action_confirm()
        inv = order.sudo().action_invoice_create(grouped=False, final=False)
        workflow.trg_validate(SUPERUSER_ID, 'account.invoice', inv[0], 'invoice_open', request.cr)
        payment_obj = request.env['account.payment']
        payment_vals = payment_obj.sudo().with_context({'default_invoice_ids': [(4, inv[0], None)]}).default_get(list(payment_obj._fields))
        journal = request.env['account.journal'].sudo().search([('type', '=', 'bank')])
        payment_vals.update({'journal_id': journal.id, 'payment_method_id': journal.inbound_payment_method_ids[0].id})
        payment = payment_obj.sudo().create(payment_vals)
        payment.post()
        tx.write({'SecurityKey': response.get('_args').get('SecurityKey'), 'TxAuthNo': response.get('_args').get('TxAuthNo'), 'VPSTxId': response.get('_args').get('VPSTxId')})
        request.website.sale_reset()
        return request.redirect("/shop/confirmation")
