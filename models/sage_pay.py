# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from openerp import api, fields, models
from openerp.addons.web.http import request
from openerp import http


class AcquirerSage_pay(models.Model):
    _inherit = 'payment.acquirer'
    _order = 'sequence'

    @api.model
    def _get_providers(self):
        providers = super(AcquirerSage_pay, self)._get_providers()
        providers.append(['sagepay', 'Sagepay'])
        return providers

    sage_pay_vendor_account = fields.Char('Vendor Id', required_if_provider = 'paymentsagepay')
    sequence = fields.Integer('Sequence')
