from odoo import models, fields, api
from odoo.exceptions import ValidationError


# trial
# hello
class Process(models.Model):
    _name = "processes"
    _description = """ a model that  describes the standard template of the process that the product goes through
    so that it could be used later for comparison against actual product"""

    name = fields.Text(required=True, string="process")
    time = fields.Integer(string="minutes")
    # a relation between inventory parts and the process through an intermediate table which is process_parts and it's
    # not linked directly with the inventory parts because if you include a part it will be allocated directly with
    # the number of the parts in the inventory but here we reassign the quantity so that it could fit the need of the
    # process
    process_parts = fields.One2many("process.parts", "process_parts", string="process parts")
    workers = fields.Many2many("workers", string="workers")
    output = fields.Many2one("inventory.parts")
    quantity = fields.Integer(string="output quantity")

    @api.constrains('quantity')
    def check_quantity(self):
        if self.output and self.quantity <= 0:
            raise ValidationError("select a quantity for the output")

    @api.constrains('time')
    def check_time(self):
        if self.time <= 0:
            raise ValidationError("time can't be zero")

    # goes through the process_parts and then checks the count of each element and raised an error if a part is
    # duplicated
    @api.constrains('process_parts')
    def checking_parts_repetition(self):
        if self.process_parts:
            parts = [i.name for i in self.process_parts]
            for i in parts:
                if parts.count(i) > 1:
                    raise ValidationError("parts are repeated !!")

    # goes through the quantity of each part and raises an error if the quantity of the part was set to 0
    @api.constrains('process_parts')
    def check_quantity(self):
        if self.process_parts:
            parts = [i.quantity for i in self.process_parts]
            for i in parts:
                if i <= 0:
                    raise ValidationError("quantity can't be less than or equal to zero")

    # prevents any two processes to have the same name
    _sql_constraints = [
        ('name_unique',
         'UNIQUE(name)',
         "this process name already exists")
    ]


class ProcessParts(models.Model):
    _name = "process.parts"
    _description = """an intermediate table between processes and inventory.parts models to allow the setting of the 
    part quantity which fits this process"""

    name = fields.Many2one("inventory.parts")
    quantity = fields.Integer(required=True, string="quantity")
    # connection between the processes and process.parts table
    process_parts = fields.Many2one("processes", "process_parts")
    # another connection between the product and the inventory.part table to allow the entry of the actual number
    # of parts used in the process
    actual_parts = fields.Many2one("factory.product", "actual_parts")
    forum_parts = fields.Many2one("submission", "actual_parts")
