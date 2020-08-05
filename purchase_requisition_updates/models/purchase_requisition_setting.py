import time
import datetime
from dateutil.relativedelta import relativedelta

import odoo
from odoo import SUPERUSER_ID
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo import api, fields, models, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    # source_id = fields.Many2one('stock.location')
    purchase_source_id = fields.Many2one('stock.location')
    picking_type_id = fields.Many2one('stock.picking.type')
    debit_account_id = fields.Many2one('account.account')
    credit_account_id = fields.Many2one('account.account')
    purchase_journal_id = fields.Many2one('account.move')
    label = fields.Char()


class RequisitionConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.user.company_id)
    purchase_source_id = fields.Many2one('stock.location',
                                         default=lambda self: self.env.user.company_id.purchase_source_id)
    picking_type_id = fields.Many2one('stock.picking.type',
                                      default=lambda self: self.env.user.company_id.picking_type_id)
    debit_account_id = fields.Many2one('account.account',
                                       default=lambda self: self.env.user.company_id.debit_account_id)
    credit_account_id = fields.Many2one('account.account',
                                        default=lambda self: self.env.user.company_id.credit_account_id)
    purchase_journal_id = fields.Many2one('account.journal',
                                        default=lambda self: self.env.user.company_id.purchase_journal_id)
    label = fields.Char(default=lambda self: self.env.user.company_id.label)

    @api.model
    def create(self, vals):
        if 'company_id' in vals\
                or 'purchase_source_id' in vals or 'picking_type_id' in vals or 'debit_account_id' in vals \
                or 'credit_account_id' in vals:
            self.env.user.company_id.write({
                    'purchase_source_id': vals['purchase_source_id'],
                    'picking_type_id': vals['picking_type_id'],
                    'debit_account_id': vals['debit_account_id'],
                    'credit_account_id': vals['credit_account_id'],
                    'purchase_journal_id': vals['purchase_journal_id'],
                    'label': vals['label'],
                 })
        res = super(RequisitionConfigSettings, self).create(vals)
        return res
