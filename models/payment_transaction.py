# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from openerp import api, fields, models


class payment_transaction(models.Model):
    _inherit = 'payment.transaction'

    SecurityKey = fields.Char('SecurityKey')
    TxAuthNo = fields.Char('TxAuthNo')
    VPSTxId = fields.Char('VPSTxId')
    crypt = fields.Text('crypt')

