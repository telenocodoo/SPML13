# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare, float_is_zero


class ProductCategory(models.Model):
    _inherit = 'product.category'

    raw_material = fields.Boolean()


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    raw_material = fields.Boolean()


class Stock(models.Model):
    _inherit = 'stock.picking'

    def action_assign(self):
        res = super(Stock, self).action_assign()
        print("custom", self.custom_requisition_id)
        for rec in self:
            for line in rec.move_ids_without_package:
                if line.product_uom_qty != line.reserved_availability:
                    rec.custom_requisition_id.state = 'prepare'
                    break
                else:
                    rec.custom_requisition_id.state = 'stock'
        return res

    def button_validate(self):
        self.ensure_one()
        if not self.move_lines and not self.move_line_ids:
            raise UserError(_('Please add some items to move.'))

        # If no lots when needed, raise error
        picking_type = self.picking_type_id
        precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        no_quantities_done = all(float_is_zero(move_line.qty_done, precision_digits=precision_digits) for move_line in self.move_line_ids.filtered(lambda m: m.state not in ('done', 'cancel')))
        no_reserved_quantities = all(float_is_zero(move_line.product_qty, precision_rounding=move_line.product_uom_id.rounding) for move_line in self.move_line_ids)
        if no_reserved_quantities and no_quantities_done:
            raise UserError(_('You cannot validate a transfer if no quantites are reserved nor done. To force the transfer, switch in edit more and encode the done quantities.'))

        if picking_type.use_create_lots or picking_type.use_existing_lots:
            lines_to_check = self.move_line_ids
            if not no_quantities_done:
                lines_to_check = lines_to_check.filtered(
                    lambda line: float_compare(line.qty_done, 0,
                                               precision_rounding=line.product_uom_id.rounding)
                )

            for line in lines_to_check:
                product = line.product_id
                if product and product.tracking != 'none':
                    if not line.lot_name and not line.lot_id:
                        raise UserError(_('You need to supply a Lot/Serial number for product %s.') % product.display_name)

        # Propose to use the sms mechanism the first time a delivery
        # picking is validated. Whatever the user's decision (use it or not),
        # the method button_validate is called again (except if it's cancel),
        # so the checks are made twice in that case, but the flow is not broken
        sms_confirmation = self._check_sms_confirmation_popup()
        if sms_confirmation:
            return sms_confirmation
        print("CCCCCCCCCCCC", self._context)
        if 'requisition' in self._context:
            # if 'model' in self._context.get('params'):
                if self._context.get('requisition'):
                    # == 'material.purchase.requisition':
                    pick_to_backorder = self.env['stock.picking']
                    pick_to_do = self.env['stock.picking']
                    for picking in self:
                        # If still in draft => confirm and assign
                        if picking.state == 'draft':
                            picking.action_confirm()
                            if picking.state != 'assigned':
                                picking.action_assign()
                                if picking.state != 'assigned':
                                    raise UserError(_(
                                        "Could not reserve all requested products. Please use the \'Mark as Todo\' button to handle the reservation manually."))
                        for move in picking.move_lines.filtered(lambda m: m.state not in ['done', 'cancel']):
                            for move_line in move.move_line_ids:
                                move_line.qty_done = move_line.product_uom_qty
                        if picking._check_backorder():
                            pick_to_backorder |= picking
                            continue
                        pick_to_do |= picking
                else:
                    if no_quantities_done:
                        view = self.env.ref('stock.view_immediate_transfer')
                        wiz = self.env['stock.immediate.transfer'].create({'pick_ids': [(4, self.id)]})
                        return {
                            'name': _('Immediate Transfer?'),
                            'type': 'ir.actions.act_window',
                            'view_mode': 'form',
                            'res_model': 'stock.immediate.transfer',
                            'views': [(view.id, 'form')],
                            'view_id': view.id,
                            'target': 'new',
                            'res_id': wiz.id,
                            'context': self.env.context,
                        }
        else:
            if no_quantities_done:
                view = self.env.ref('stock.view_immediate_transfer')
                wiz = self.env['stock.immediate.transfer'].create({'pick_ids': [(4, self.id)]})
                return {
                    'name': _('Immediate Transfer?'),
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',
                    'res_model': 'stock.immediate.transfer',
                    'views': [(view.id, 'form')],
                    'view_id': view.id,
                    'target': 'new',
                    'res_id': wiz.id,
                    'context': self.env.context,
                }

        if self._get_overprocessed_stock_moves() and not self._context.get('skip_overprocessed_check'):
            view = self.env.ref('stock.view_overprocessed_transfer')
            wiz = self.env['stock.overprocessed.transfer'].create({'picking_id': self.id})
            return {
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'stock.overprocessed.transfer',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'res_id': wiz.id,
                'context': self.env.context,
            }

        # Check backorder should check for other barcodes
        if self._check_backorder():
            return self.action_generate_backorder_wizard()
        self.action_done()
        return


class MaterialPurchaseRequisition(models.Model):
    _inherit = 'material.purchase.requisition'
    type = fields.Selection([
        ('raw_material', 'Raw Material'),
        ('finished_good', 'Finished Good'),
    ], string='Type', default='raw_material')

    location_id = fields.Many2one('stock.location', string='Source Location',
                                  copy=True, default=lambda self: self.env.user.company_id.purchase_source_id)

    custom_picking_type_id = fields.Many2one('stock.picking.type', string='Picking Type',
                                             copy=False,
                                             default=lambda self: self.env.user.company_id.picking_type_id)
    debit_account_id = fields.Many2one('account.account',
                                       default=lambda self: self.env.user.company_id.debit_account_id)
    credit_account_id = fields.Many2one('account.account',
                                        default=lambda self: self.env.user.company_id.credit_account_id)
    purchase_journal_id = fields.Many2one('account.journal',
                                          default=lambda self: self.env.user.company_id.purchase_journal_id)
    label = fields.Char(default=lambda self: self.env.user.company_id.label)

    picking_number = fields.Integer(compute="get_picking_number")
    purchase_number = fields.Integer(compute="get_purchase_number")
    state = fields.Selection([
        ('draft', 'New'),
        ('ir_approve', 'Requested'),
        ('approve', 'Approved'),
        ('prepare', 'Preparing Transfer'),
        ('stock', 'Transfer Ready'),
        ('receive', 'Received'),
        ('cancel', 'Cancelled'),
        ('reject', 'Rejected')],
        default='draft',
        track_visibility='onchange',
    )

    def get_picking_number(self):
        for record in self:
            picking_id = self.env['stock.picking'].search_count([('custom_requisition_id', '=', record.id)])
            self.picking_number = picking_id

    def get_purchase_number(self):
        for record in self:
            purchase_number = self.env['purchase.order'].search_count([('custom_requisition_id', '=', record.id)])
            self.purchase_number = purchase_number

    def request_stock(self):
        res = super(MaterialPurchaseRequisition, self).request_stock()
        self.state = 'prepare'
        return res

    def get_product_price(self, product, quantity):
        product_obj = self.env['product.product'].browse([product])
        total = product_obj.standard_price * quantity
        return total

    def action_received(self):
        # res = super(MaterialPurchaseRequisition, self).action_received()
        for record in self:
            picking_id = self.env['stock.picking'].search([('custom_requisition_id', '=', record.id)])
            if picking_id:
                for p in picking_id:
                    if p.state in ['draft', 'confirmed', 'waiting']:
                        raise UserError(_("This picking %s State Isn't Ready "
                                          "The State Of Picking Order Must Be "
                                          "Ready To Be Validated" % p.name))
                    elif p.state == 'assigned':
                        p = p.with_context(requisition=True)
                        p.action_assign()
                        p.button_validate()

            account_move_obj = self.env['account.move']
            account_move_line_obj = self.with_context(dict(self._context, check_move_validity=False)).env[
                'account.move.line']
            account_obj = account_move_obj.create({
                'journal_id': record.purchase_journal_id.id,
                'date': fields.date.today(),
            })
            t = []
            if record.requisition_line_ids:
                for line in record.requisition_line_ids:
                    account_move_line_obj.create({
                        'move_id': account_obj.id,
                        'account_id': record.debit_account_id.id,
                        'analytic_account_id': record.analytic_account_id.id,
                        'partner_id': record.employee_id.address_id.id,
                        'name': record.label,
                        'debit': record.get_product_price(line.product_id.id, line.qty),
                        'credit': 0.0,
                    })
                    t.append(record.get_product_price(line.product_id.id, line.qty))
                account_move_line_obj.create({
                    'move_id': account_obj.id,
                    'account_id': record.credit_account_id.id,
                    'analytic_account_id': record.analytic_account_id.id,
                    'partner_id': record.employee_id.address_id.id,
                    'name': record.label,
                    'debit': 0.0,
                    'credit': sum(t),
                })

            print(account_obj.id)
            record.receive_date = fields.Date.today()
            record.state = 'receive'


class MaterialPurchaseRequisitionLine(models.Model):
    _inherit = "material.purchase.requisition.line"

    state = fields.Selection([
        ('draft', 'New'),
        ('ir_approve', 'Waiting IR Approval'),
        ('approve', 'Approved'),
        ('stock', 'Purchase Order Created'),
        ('receive', 'Received'),
        ('cancel', 'Cancelled'),
        ('reject', 'Rejected')],
        default='draft', related='requisition_id.state'
    )

    type = fields.Selection([
        ('raw_material', 'Raw Material'),
        ('finished_good', 'Finished Good'),
    ], string='Type', default='raw_material', related='requisition_id.type')

    requisition_type = fields.Selection(
        selection=[
                    ('internal','Internal Picking'),
                    ('purchase','Purchase Order'),
        ],
        string='Requisition Action',
        default='internal',
        required=True,
    )

    @api.onchange('product_id')
    def onchange_product_id(self):
        for rec in self:
            # if rec.type == 'raw_material':
            product_ids = self.env['product.product'].search(['|', ('raw_material', '=', True),
                                                              ('categ_id.raw_material', '=', True)])
            products = []
            for p in product_ids:
                products.append(p.id)
            domain = {'product_id': [('id', 'in', products)]}
            rec.description = rec.product_id.name
            rec.uom = rec.product_id.uom_id.id
            return {'domain': domain}
            # else:
            #     rec.description = rec.product_id.name
            #     rec.uom = rec.product_id.uom_id.id
