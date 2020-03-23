# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.tools.float_utils import float_is_zero, float_compare
from odoo.exceptions import UserError
import datetime

class SingleModel(models.Model):

	_inherit = 'stock.picking'
	
	fiscal_position_id = fields.Many2one('account.fiscal.position', string='Fiscal Position',
										 domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")


class SingleMove(models.Model):
	_inherit = 'stock.move'



	taxes_id = fields.Many2many('account.tax', string='Taxes',
								domain=['|', ('active', '=', False), ('active', '=', True)])

class SingleVendorBill(models.TransientModel):

	_name = 'single.vendor.bill'

	# Return created Invoices

	def create_return_vendor_bill(self):
		vendor_bill_id  = self.create_single_vendor_bill()
		tree_view_ref = self.env.ref('account.invoice_supplier_tree',False)
		form_view_ref = self.env.ref('account.invoice_supplier_form',False)
		return {
					'name':'Invoices',
					'res_model':'account.move',
					'view_type':'form',
					'view_mode':'tree,form',
					'target':'current',
					'domain':[('id','=',vendor_bill_id.id)],
					'type':'ir.actions.act_window',
					'views': [(tree_view_ref and tree_view_ref.id or False,'tree'),(form_view_ref and form_view_ref.id or False,'form')],
				}

	# Create single Invoice from multiple orders

	def create_single_vendor_bill(self):
		purchase_orders = self.env['stock.picking'].browse(self._context.get('active_ids'))
		name_orders = [order.name for order in purchase_orders]
		partners = [order.partner_id.id for order in purchase_orders]
		fiscal_positions = [order.fiscal_position_id.id for order in purchase_orders]
		not_confirmed_order = []
		for order in purchase_orders:
			if order.state != 'assigned':
				not_confirmed_order.append(order.name)
			else:
				pass
		if (len(purchase_orders)) < 2:
			raise UserError(_('Please select atleast two Delivery Order to create Single Invoice'))
		else:
			if(len(set(partners))!=1):
				raise UserError(_('Please select Delivery Order whose "Contacts" are same to create Single Invoice.'))
			else:
				if (len(set(fiscal_positions))!=1):
					raise UserError(_('Please select Delivery Order whose "Fiscal Poistions" are same to create Single Invoice.'))
				else:
					if any(order.state != 'assigned' for order in purchase_orders):
						raise UserError(_('Please select Delivery Order which are in "Ready State" state to create Single Invoice.%s is not confirmed yet.') % ','.join(map(str, not_confirmed_order)))
					else:
						vendor_bill_id = self.prepare_vendor_bill()
						return vendor_bill_id


	def prepare_vendor_bill(self):
		invoice_line = self.env['account.move.line']
		purchase_orders = self.env['stock.picking'].browse(self._context.get('active_ids'))
		name_orders = [order.name for order in purchase_orders]
		journal_id = self.env['account.journal'].search([('type','=','assigned')])
		partner_ids = [order.partner_id for order in purchase_orders if order.partner_id.id]
		invoice_lines = []
		for order in purchase_orders:
			for line in order.move_ids_without_package:
				account_id = line.product_id.property_account_expense_id or line.product_id.categ_id.property_account_expense_categ_id
				invoice_lines.append(((0,0,{
							'name': line.name,
							'display_name': line.picking_id.name,
							'account_id': account_id.id,
							'price_unit': line.product_id.lst_price,
							'quantity': line.product_qty,
							'product_uom_id': line.product_uom.id,
							'product_id': line.product_id.id or False,
							'tax_ids': [(6, 0, line.product_id.taxes_id.ids)],
						})))
		vendor_bill_vals = {
							'name': ','.join(map(str, name_orders)),
							'invoice_origin':','.join(map(str, name_orders)),
							'invoice_date':datetime.datetime.now().date(),
							'type': 'in_invoice',
							'state':'draft',
							'partner_id': order.partner_id.id,
							'invoice_line_ids': invoice_lines,
							# 'journal_id': journal_id.id or False,
							# 'invoice_payment_term_id': order.payment_term_id.id,
							# 'fiscal_position_id': order.fiscal_position_id.id,
							'company_id': order.company_id.id,
							'user_id': order.activity_user_id and order.activity_user_id.id,
						}
		vendor_bill_id = self.env['account.move'].create(vendor_bill_vals)
		if vendor_bill_id:
			precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
			for order in purchase_orders:
				if order.state not in ('assigned'):
					order.invoice_status = 'no'
					continue
				if any(float_compare(line.quantity_done, line.product_qty if line.state == 'assigned' else line.product_uom_qty, precision_digits=precision) == -1 for line in order.move_ids_without_package):
					order.invoice_status = 'to invoice'
				elif all(float_compare(line.quantity_done, line.product_qty if line.state == 'assigned' else line.product_uom_qty, precision_digits=precision) >= 0 for line in order.move_ids_without_package):
					order.invoice_status = 'invoiced'
				else:
					order.invoice_status = 'no'
		vendor_bill_id._onchange_invoice_line_ids()
		return vendor_bill_id
