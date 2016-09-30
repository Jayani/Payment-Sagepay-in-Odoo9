# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from openerp import  api, fields, models
from openerp.tools.translate import _


class account_invoice(models.Model):
    _inherit = 'account.invoice'

    refund_sagepay = fields.Char('Refund Amount Sagepay')

    @api.multi
    def sagepay_refund(self):
        view_id = self.env.ref('payment_sagepay.view_wiz_refund_sagepay_form').id
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wiz.refund.sagepay',
            'views': [(view_id, 'form')],
            'view_id': view_id,
            'target': 'new',
        }

