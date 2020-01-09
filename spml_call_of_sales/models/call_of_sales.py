# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    is_call_of = fields.Boolean()
    # period_call_of = fields.Selection(selection=[('weekly', 'weekly'), ('monthly', 'monthly'), ])
    call_of_id = fields.Many2one("call.of.sales")

    # @api.one
    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        default = {} if default is None else default.copy()
        default.update({
            'is_call_of': False
        })
        return super(SaleOrder, self).copy(default=default)

    # @api.multi
    def call_of_sales_action(self):
        tender_id = self.env['call.of.sales']
        tender_line_id = self.env['call.of.sales.lines']
        # tender_line_id = self.env['tender.sales.lines']
        invoice_id = self.env['account.move'].search([('invoice_origin', '=', self.name)], limit=1)
        for record in self:
            tender_obj = tender_id.create({
                'sale_id': self.id,
                'period': self.period,
                'invoice_id': invoice_id.id,
            })
            for line in record.order_line:
                tender_line_id.create({
                    'call_of_id': tender_obj.id,
                    'product_id': line.product_id.id,
                    'quantity': line.product_uom_qty,
                    'cost': line.price_unit,
                    'tax_ids': [(6, 0, line.tax_id.ids)],
                    'total': line.price_subtotal,
                    # 'ordered_quantity': line.product_uom_qty,
                })
            record.is_call_of = True
            self.call_of_id = tender_obj.id
            return {
                'type': 'ir.actions.act_window',
                'name': 'Call of Sales',
                'res_model': 'call.of.sales',
                'res_id': tender_obj.id,
                'view_type': 'form',
                'view_mode': 'form',
                'target': 'current',
            }


class AccountTAx(models.Model):
    _inherit = "account.tax"

    call_of_id = fields.Many2one("call.of.sales.lines")
    # tender_id = fields.Many2one("tender.sales.lines")


class TenderWizardLines(models.TransientModel):
    _name = "call.of.sales.wizard.lines"

    tender_wiz_id = fields.Many2one('call.of.sales.wizard')
    line_id = fields.Many2one('call.of.sales.lines')
    # line_id = fields.Many2one('tender.sales.lines')
    product1_id = fields.Many2one("product.product")
    quantity1 = fields.Float()
    cost1 = fields.Float()
    total1 = fields.Float()
    product2_id = fields.Many2one("product.product")
    quantity2 = fields.Float()
    cost2 = fields.Float()
    total2 = fields.Float()
    number = fields.Integer()


class TenderWizard(models.TransientModel):
    _name = "call.of.sales.wizard"

    call_of_id = fields.Many2one("call.of.sales")
    tender_ids = fields.One2many("call.of.sales.wizard.lines", "tender_wiz_id")
    product1_id = fields.Many2one("product.product")
    quantity1 = fields.Float()
    cost1 = fields.Float()
    total1 = fields.Float()
    note1 = fields.Char()
    line_id1 = fields.Many2one('call.of.sales.lines')
    # line_id1 = fields.Many2one('tender.sales.lines')
    product2_id = fields.Many2one("product.product")
    quantity2 = fields.Float()
    cost2 = fields.Float()
    total2 = fields.Float()
    note2 = fields.Char()
    line_id2 = fields.Many2one('call.of.sales.lines')
    # line_id2 = fields.Many2one('tender.sales.lines')

    def _prepare_item(self, line):
        """prepare lines data"""
        return {
            'line_id': line.id,
            'product1_id': line.product_id.id,
            'quantity1': line.balance,
            'cost1': line.cost,
            'total1': line.total,
            'number': line.number,
        }

    @api.model
    def default_get(self, fields_list):
        """get default lines"""
        res = super(TenderWizard, self).default_get(fields_list)
        request_line_obj = self.env['call.of.sales']
        request_line_ids = self.env.context.get('active_ids', False)
        active_model = self.env.context.get('active_model', False)
        if not request_line_ids:
            return res
        assert active_model == 'call.of.sales', \
            'Bad context propagation'
        items = []
        request_lines = request_line_obj.browse(request_line_ids[0])
        for record in request_lines:
            for line in record.tender_ids:
                if line.is_move:
                    items.append([0, 0, self._prepare_item(line)])
        res['tender_ids'] = items
        return res

    # @api.multi
    def compute_product_quantity(self):
        total1 = 0
        total2 = 0
        needed_qty = 0
        cost_of_p2 = 0
        qty_needed_from_p1 = 0
        balance_p1 = 0
        for record in self:
            needed_qty = self.quantity2
            cost_of_p2 = needed_qty * record.cost2
            qty_needed_from_p1 = cost_of_p2 / record.cost1
            balance_p1 = record.quantity1 - qty_needed_from_p1
            total1 = balance_p1 * record.cost1
            total2 = needed_qty * record.cost2
        self.quantity1 = balance_p1
        self.quantity2 = needed_qty
        self.total1 = total1
        self.total2 = total2
        self.note2 += "and new quantity is " + str(needed_qty)
        self.note1 += "and we take " + str(qty_needed_from_p1)
        self.line_id1.write({
            'ordered_quantity': self.line_id1.ordered_quantity - qty_needed_from_p1,
            'note': self.note1,
        })
        self.line_id2.write({
            'ordered_quantity': self.line_id2.ordered_quantity+needed_qty,
            'note': self.note2,
        })
    # @api.multi
    # def compute_product_quantity(self):
    #     quantity1 = 0
    #     total1 = 0
    #     total2 = 0
    #     tot2 = 0
    #     balance = 0
    #     balance2 = 0
    #     remain1 = 0
    #     remain2 = 0
    #     current_qty = 0
    #     for record in self:
    #         current_qty = self.quantity2
    #         quantity1 = int(record.total2 / record.cost1)
    #         total1 = quantity1 * record.cost1
    #         total2 = record.total2 - total1
    #         balance = int(total2 / record.cost2)
    #         tot2 = balance * record.cost2
    #         remain1 = total2 - tot2
    #         balance2 = current_qty - balance
    #
    #     self.quantity1 = quantity1
    #     self.quantity2 = balance
    #     self.total1 = total1
    #     self.total2 = total2
    #     # self.remain1 = remain1
    #     # self.remain2 = remain2
    #
    #     self.note2 += "and new quantity is " + str(balance) + "and remain" + str(remain1)
    #     self.note1 += "and we add " + str(quantity1)
    #
    #     self.line_id1.write({
    #         'ordered_quantity': self.line_id1.ordered_quantity + self.quantity1,
    #         'note': self.note1,
    #     })
    #     # self.quantity2
    #     self.line_id2.write({
    #         'ordered_quantity': self.line_id2.ordered_quantity-balance2,
    #         'note': self.note2,
    #     })

    # @api.multi
    def move_product_quantity(self):
        create = False
        for rec in self:
            for line in rec.tender_ids:
                if line.number == 1:
                    self.product1_id = line.product1_id.id
                    self.quantity1 = line.quantity1
                    self.cost1 = line.cost1
                    self.total1 = line.total1
                    self.note1 = "old balance is " + str(line.quantity1)
                    self.line_id1 = line.line_id
                else:
                    self.product2_id = line.product1_id.id
                    self.quantity2 = line.quantity1
                    self.cost2 = line.cost1
                    self.total2 = line.total1
                    self.note2 = "old balance is " + str(line.quantity1)
                    self.line_id2 = line.line_id
                create = True
        # context = self.env.context
        # act_ids = context.get('active_ids', [])
        # print("dddddddd, ", act_ids)


class CallOfSales(models.Model):
    _name = "call.of.sales"
    # _name = "tender.sales"
    _rec_name = 'sale_id'

    sale_id = fields.Many2one("sale.order")
    invoice_id = fields.Many2one("account.move")
    tender_ids = fields.One2many("call.of.sales.lines", "call_of_id")
    # tender_ids = fields.One2many("tender.sales.lines", "tender_id")
    period = fields.Selection(selection=[('weekly', 'weekly'), ('monthly', 'monthly'), ])

    # @api.multi
    def transfer_quantity_to_product(self):
        print("yes")
        lst = []
        for record in self:
            for line in record.tender_ids:
                if line.is_move:
                    lst.append(line)
        if len(lst) != 2:
            raise UserError(_("The selected lines Must be two lines"))

        return {
                'type': 'ir.actions.act_window',
                'name': 'Tender Sales wizard',
                'res_model': 'call.of.sales.wizard',
                'view_type': 'form',
                'view_mode': 'form',
                'context': {'default_call_of_id': self.id},
                'target': 'current',
            }


class CallOfSalesLines(models.Model):
    _name = "call.of.sales.lines"
    # _name = "tender.sales.lines"

    call_of_id = fields.Many2one("call.of.sales")
    product_id = fields.Many2one("product.product")
    quantity = fields.Float(string="ordered Qty")
    sequence = fields.Integer()
    number = fields.Integer()
    cost = fields.Float()
    total = fields.Float(compute="compute_total_price")
    tax_ids = fields.Many2many("account.tax", "call_of_id")
    ordered_quantity = fields.Float(string="Transfer Qty")
    delivered_quantity = fields.Float()
    balance = fields.Float(store=True, compute='compute_balance')
    state = fields.Selection(selection=[('close', 'close'), ('open', 'open')], compute='compute_tender_state')
    note = fields.Char()
    is_move = fields.Boolean()

    # @api.multi
    def transfer_product_quantity(self):
        tender_delivery_id = self.env['call.of.delivered.quantity']
        tender_search_id = tender_delivery_id.search([('tender_sales_id', '=', self.id)])
        if tender_search_id:
            if tender_search_id.quantity < self.quantity + self.ordered_quantity:
                tender_search_id.quantity = self.quantity + self.ordered_quantity
            return {
                'type': 'ir.actions.act_window',
                'name': 'Call of Delivered Quantity',
                'res_model': 'call.of.delivered.quantity',
                'res_id': tender_search_id.id,
                'view_type': 'form',
                'view_mode': 'form',
                'target': 'current',
            }

        else:
            tender_id = tender_delivery_id.create({
                'tender_sales_id': self.id,
                'product_id': self.product_id.id,
                'invoice_id': self.call_of_id.invoice_id.id,
                'sale_id': self.call_of_id.sale_id.id,
                'quantity': self.quantity + self.ordered_quantity,
            })
            return {
                'type': 'ir.actions.act_window',
                'name': 'Call of Delivered Quantity',
                'res_model': 'call.of.delivered.quantity',
                'res_id': tender_id.id,
                'view_type': 'form',
                'view_mode': 'form',
                'target': 'current',
            }

    @api.constrains('balance')
    def constrains_balance(self):
        for record in self:
            if record.balance < 0:
                raise UserError(_("Balance must be greater than 0"))

    @api.depends('ordered_quantity', 'delivered_quantity')
    def compute_balance(self):
        for record in self:
            record.balance = (record.ordered_quantity + record.quantity) - record.delivered_quantity

    @api.depends('balance', 'cost')
    def compute_total_price(self):
        for record in self:
            record.total = record.balance * record.cost

    @api.depends('balance')
    def compute_tender_state(self):
        for record in self:
            if record.balance <= 0:
                record.state = 'close'
            else:
                record.state = 'open'
