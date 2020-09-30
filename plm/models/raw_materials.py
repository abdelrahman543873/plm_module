# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class InventoryParts(models.Model):
    _name = "inventory.parts"
    _description = "the parts that form the products"

    name = fields.Text(string="part", required=True, unique=True)
    half_processed = fields.Boolean(default=False)
    item_price = fields.Integer(string="item price")
    calculated_cost = fields.Integer(string="calculated cost ", compute="costing")
    quantity = fields.Float(string="quantity", required=True)
    total_cost = fields.Integer(string="total price", compute="calculate_cost")
    storage = fields.Many2one("storage", string="storage Area")

    @api.constrains('item_price', 'quantity')
    def check_quantity_price(self):
        if self.half_processed is False and self.item_price <= 0:
            raise ValidationError("السعر يجب ان يكون اكبر من صفر")
        elif self.quantity < 0:
            raise ValidationError("الكميه لا تكفي")

    @api.constrains('half_processed')
    def check_half_processed(self):
        if self.half_processed:
            self.item_price = 0

    @api.depends('item_price', 'quantity', 'calculated_cost', 'half_processed')
    def calculate_cost(self):
        if self.half_processed:
            self.total_cost = self.calculated_cost * self.quantity
        else:
            self.total_cost = self.item_price * self.quantity

    @api.depends('name', 'half_processed')
    def costing(self):
        if self.half_processed:
            output_processes = [i for i in
                                self.env['processes'].search([('output', '=', self.name)])]
            logs = [i.actual_process for i in
                    self.env['factory.product'].search(
                        [('actual_process', '=', output_processes[0].name), ('complete', '=', True)])]
            if output_processes and logs:
                produced_number = len(logs) * output_processes[0].quantity
                summation = 0
                for process in logs:
                    process_list = [i.name for i in process]
                    process_index = process_list.index(output_processes[0].name)
                    summation += process[process_index].cost
                    iterator = process_index + 1
                    while iterator < len(process_list) and not process_list[iterator]:
                        summation += process[iterator].cost
                        iterator += 1
                self.calculated_cost = int(summation / produced_number)
                self.half_processed = True
            else:
                self.calculated_cost = 0
        else:
            self.calculated_cost = 0

    _sql_constraints = [
        ('name_unique',
         'UNIQUE(name)',
         "this part name already exists")
    ]


class Storage(models.Model):
    _name = "storage"
    _description = "the storage area of the products"

    name = fields.Text(string="Storage", required=True)
