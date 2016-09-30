 # -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from openerp import api, fields, models


class wiz_partner(models.TransientModel):
    _name = 'wiz.partner'

    mailing_list_id = fields.Many2one('mail.mass_mailing.list', 'Create/Edit Mailing List', required=True, help="Create/Edit Mailing List")

    @api.multi
    def create_record(self):
        mailing_contact_obj = self.env['mail.mass_mailing.contact']
        res_partner_obj = self.env['res.partner']
        for rec in self.browse():
            mass_mailing_list_id = rec.mailing_list_id.id
            for customer in res_partner_obj.browse(self._context.get('active_ids')):
                mailing_contact_obj.create({'name': customer.name,
                                            'last_name': customer.surname,
                                            'email': customer.email,
                                            'list_id': mass_mailing_list_id
                                           })
        return True

