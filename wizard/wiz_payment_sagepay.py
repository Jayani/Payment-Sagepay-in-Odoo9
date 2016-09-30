 # -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import time
from openerp import api, fields, models, _
from sagepay import SagePayAPI
from sagepay import wrappers
from openerp.http import request
from openerp import workflow
from openerp.exceptions import ValidationError


class wiz_payment_sagepay(models.TransientModel):
    _name = 'wiz.payment.sagepay'

    card_number = fields.Char('Card Number')
    card_type = fields.Selection([('VISA', 'Visa'), ('MC', 'Mastercard'), ('MAESTRO', 'Maestro')], 'Card Type')
    cv_code = fields.Char('CVV', size=3)
    card_expiry_month = fields.Char('Month', size=2)
    card_expiry_year = fields.Char('Year', size=2)
    card_holder_name = fields.Char('Card Holder Name')

    @api.multi
    # Method is used to do mobile payment
    def btn_sagepay_payment(self):
        tran_obj = self.env['payment.acquirer']
        payment_tran_obj = self.env['payment.transaction']
        so_obj = self.env[self._context.get('active_model')]
        inv_obj = self.env['account.invoice']
        pay_acq_ids = tran_obj.search([('provider', '=', 'sagepay')])
        if pay_acq_ids.environment == 'test':
            environment = 'test'
        if pay_acq_ids.environment == 'prod':
            environment = 'live'
        vendor_id = pay_acq_ids.sage_pay_vendor_account
        order = so_obj.browse(self._context.get('active_id'))

        for rec in self:
            ACCEPTED_OPTIONS = {
            'cv2': rec.cv_code,
            # 'issue_number': '1',
            # 'start_date': '0514',
            }
            ACCEPTED_OPTIONS_T = {
                # Python Key / SagePay Key
                'account_type': 'M',
                'apply_3d_secure': '0',
                'apply_avs_cv2': '0',
                'basket': '',
                'client_ip_address': request.httprequest.environ['REMOTE_ADDR'] or '127.0.0.1',
                'contact_number': order.partner_id.phone,
                'contact_fax': '',
                'contact_email': order.partner_id.email or 'test@rms.com',
                'customer_name': order.partner_id.name,
                'customer_email': order.partner_id.email or 'test@rms.com',
                'gift_aid_payment': '0',
                'billing_firstname': order.partner_id.name,
                'billing_surname': order.partner_id.name,
                #'billing_address': 'BillingAddress',
                'billing_address1': order.partner_id.street or order.partner_id.street2,
                'billing_address2': order.partner_id.street2,
                'billing_city': order.partner_id.city,
                'billing_country': order.partner_id.country_id.code,
                'billing_post_code': order.partner_id.zip
            }
            tx_ids = self.env['payment.transaction'].search([('sale_order_id', '=', self._context.get('active_id'))])
            if tx_ids:
                tx = tx_ids
            if not tx_ids:
                tx = self.env['payment.transaction'].create({
                            'acquirer_id': pay_acq_ids.id,
                            'type': 'form',
                            'amount': order.amount_total,
                            'currency_id': order.pricelist_id.currency_id.id,
                            'partner_id': order.partner_id.id,
                            'partner_country_id': order.partner_id.country_id.id,
                            'reference': order.name,
                            'sale_order_id': order.id,
                        })
            card_request = wrappers.SagePayCard(rec.card_holder_name, rec.card_number, rec.card_type, str(rec.card_expiry_month)+ str(rec.card_expiry_year), **ACCEPTED_OPTIONS)
            order_name = order.name + '-' + time.strftime('%Y%m%d%H%M%S')
            payment_request = wrappers.SagePayTransaction('PAYMENT', order_name, str(tx.amount), order.currency_id.name, tx.sale_order_id.name, card_request, **ACCEPTED_OPTIONS_T)
            response = SagePayAPI(vendor_id, environment).register(payment_request).__dict__
            if response.get('_args')['Status'] == 'OK':
                inv_ids = order.action_invoice_create(grouped=False, final=False)
                tx_id = tx.id
                for acc_inv in inv_obj.browse(inv_ids):
                    acc_inv.payment_ref_id = tx_id
                    workflow.trg_validate(self._uid, 'account.invoice', acc_inv.id, 'invoice_open', self._cr)
                    payment_obj = request.env['account.payment']
                    payment_vals = payment_obj.with_context({'default_invoice_ids': [(4, inv_ids[0], None)]}).default_get(list(payment_obj._fields))
                    journal = request.env['account.journal'].search([('type', '=', 'bank')])
                    payment_vals.update({'journal_id': journal.id, 'payment_method_id': journal.inbound_payment_method_ids[0].id})
                    payment = payment_obj.create(payment_vals)
                    payment.post()
                    tx.write({'state':'done', 'SecurityKey': response.get('_args').get('SecurityKey'), 'TxAuthNo': response.get('_args').get('TxAuthNo'), 'VPSTxId':  response.get('_args').get('VPSTxId')})
            if response.get('_args')['Status'] == 'INVALID':
                raise Warning(('Error!'), ('Something Went Wrong With Payment, Error: %s ') % (response.get('_args')['StatusDetail']))
            return True


class wiz_refund_sagepay(models.TransientModel):
    _name ='wiz.refund.sagepay'

    amount = fields.Float('Amount To Be Refunded')
    description = fields.Text('Reason for Refund')

    @api.multi
    def sagepay_refund(self):
        inv_ids = self._context.get('active_ids')
        inv_obj = self.env['account.invoice']
        payacc_obj = self.env['payment.acquirer']
        tran_obj = self.env['payment.transaction']
        so_obj = self.env['sale.order']
        pay_acq_ids = payacc_obj.search([('provider', '=', 'sagepay')])
        if pay_acq_ids.environment == 'test':
            environment = 'test'
        if pay_acq_ids.environment == 'prod':
            environment = 'live'
        vendor_id =  pay_acq_ids.sage_pay_vendor_account
        VPSProtocol = "3.00"
        TxType = 'REFUND'
        tran_id = ''
        for rec in self:
            if rec.amount <= 0:
                raise ValidationError(_('Please, Enter valid amount.'))
            amount = rec.amount
            description = rec.description
            for inv in inv_obj.browse(inv_ids):
                origin = inv.origin
                currency = inv.currency_id.name
                description = 'Refund'
                so_id = so_obj.search([('name', '=', origin)])
                if so_id:
                    tran_id = tran_obj.search([('reference', '=', origin)])[0]
                    if tran_id:
                        VendorTxCode = str(inv.number).replace('/', '-')
                        RelatedVPSTxId = str(tran_id.VPSTxId).replace('{', '').replace('}', '')
                        RelatedVendorTxCode = origin
                        RelatedSecurityKey = tran_id.SecurityKey
                        RelatedTxAuthNo = tran_id.TxAuthNo
                if tran_id:
                    response = SagePayAPI(vendor_id, environment).refund(VendorTxCode, amount, currency, description, RelatedVPSTxId, RelatedVendorTxCode, RelatedSecurityKey, RelatedTxAuthNo).__dict__
                    if response.get('_args').get('Status') == 'OK':
                        amount = (inv.refund_sagepay) + (amount)
                        inv.write({'refund_sagepay': amount})
        return True
