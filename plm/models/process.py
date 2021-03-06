from odoo import models, fields, api
from odoo.exceptions import ValidationError


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
    output = fields.Text()
    quantity = fields.Float(string="output quantity")

    @api.model
    def create(self, values):
        if values['output']:
            self.env['inventory.parts'].create(
                {'name': values['output'], 'quantity': 0, 'half_processed': True})
        return super().create(values)

    @api.constrains('quantity')
    def check_quantity(self):
        if self.output and self.quantity <= 0:
            raise ValidationError("select a quantity for the output")

    @api.constrains('quantity')
    def check_quantity_price(self):
        if self.quantity and not self.output:
            raise ValidationError("enter a product")

    @api.constrains('time')
    def check_time(self):
        if self.time <= 0:
            raise ValidationError("time can't be zero")

    @api.constrains('output')
    def check_if_exists(self):
        raw_materials = [i for i in
                         self.env['inventory.parts'].search([('name', '=', self.output)])]
        if len(raw_materials) > 1:
            raise ValidationError('this part already exists')

    # goes through the process_parts and then checks the count of each element and raised an error if a part is
    # duplicated
    # goes through the quantity of each part and raises an error if the quantity of the part was set to 0
    @api.constrains('process_parts')
    def checking_parts_errors(self):
        if self.process_parts:
            parts = [i for i in self.process_parts]
            parts_names = [i.name for i in self.process_parts]
            for i in parts:
                if parts_names.count(i.name) > 1:
                    raise ValidationError("القطع مكرره")
                elif i.quantity <= 0:
                    raise ValidationError("الكميه لا يمكن ان تكون اقل من او تساوي صفر")
                elif not i.name.name:
                    raise ValidationError("لا يمكنك ادخال قطعه خاليه")
        else:
            raise ValidationError("لا يمكن ترك القطه خاليه")

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
    quantity = fields.Float(required=True, string="quantity")
    # connection between the processes and process.parts table
    process_parts = fields.Many2one("processes", "process_parts")
    # another connection between the product and the inventory.part table to allow the entry of the actual number
    forum_actual_parts = fields.Many2one("submission", "actual_parts")
    forum_standard_parts = fields.Many2one('submission', "standard_parts")
