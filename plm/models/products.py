from datetime import datetime, timedelta

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class FactoryProducts(models.Model):
    _name = "factory.product"
    _description = "the products model that stores all the details about the product"

    name = fields.Text(string="name", required=True)
    price = fields.Float('Price', required=True)
    # the processes status bar that the process goes through
    actual_price = fields.Integer(compute="total_cost", string="actual cost", readonly=True, copy=False)
    # the different processes that the product goes through
    states = fields.Many2one("processes", tracking=True, index=True, required=True,
                             domain="[('id','in',process)]")
    # the processes table that the product goes through
    process = fields.Many2many("processes", string="processes")
    # the log of the product with the processes that the product went through and their consumption
    actual_process = fields.Many2many("log", string="log", readonly=True, copy=False)
    # a field that detects the state of the product completed,pause or finalized
    status = fields.Selection([("running", "Running"), ("pause", "Paused"), ("completed", "Completed")],
                              default="pause", copy=False)
    # a variable that is used to store the value of the timestamp of when the process started running
    process_time = fields.Datetime(string="process timing", store=True, copy=False)
    # calculate Duration of the process
    duration = fields.Integer(string="duration", store=True, copy=False)
    # output duration in text
    duration_text = fields.Text(string="duration_text", store=True, copy=False)
    # a boolean field that is a marker when the product is completed
    complete = fields.Boolean(string="completed", default=False, copy=False)

    def write(self, vals):
        if self.complete:
            raise ValidationError("لا تستطيع ان تعدل منتج مكتمل")
        return super(FactoryProducts, self).write(vals)

    @api.onchange('process')
    def set_states_domain(self):
        return {'domain': {'states': [('name', 'in', [i.name for i in self.process])]}}

    @api.onchange('actual_process')
    @api.depends('actual_process')
    def total_cost(self):
        self.actual_price = sum([i.cost for i in self.actual_process])

    @api.onchange('states')
    def check_state(self):
        if self.states and self.process:
            # if the process isn't completed you can't move to another process
            if self.status != "completed" and self.create_date:
                raise ValidationError("لا يمكنك الاانتفال قبل انهاء العمليه الاولي")
            # checks if the process has been completed before
            elif self.states.name in [i.name for i in self.actual_process]:
                raise ValidationError("هذه العمله تمت بالفعل")
            else:
                # all of the behaviour here happens when the product is created
                if self.create_date:
                    current_product = self.env['factory.product'].browse(self.ids[0])
                    # whenever a process is selected the status is set to running
                    current_product.status = "running"
                    # the process_time is reset so that the new process running time is calculated
                    current_product.process_time = datetime.now()
                    # the duration is set to 0 so that the new process time is calculated
                    current_product.duration = 0

    @api.constrains('price')
    def check_quantity(self):
        if self.price <= 0:
            raise ValidationError("money can't be zero")

    def start(self):
        if self.create_date:
            if self.status == "completed" and self.states:
                raise ValidationError("لا تستطيع تغير الحاله بعد ان تمت العمليه")
            self.process_time = datetime.now()
            self.status = "running"

    def pause(self):
        if self.create_date:
            if self.status == "completed" and self.states:
                raise ValidationError("لا تستطيع تغير الحاله بعد ان تمت العمليه")
            self.process_timing()
            self.status = "pause"

    # a function that does the subtraction from the store after the process transition is done
    def end(self):
        if not self.create_date:
            raise ValidationError("لا يمكن الاستهلاك قبل ان تحفظ العمليه")
        elif self.status == "completed":
            raise ValidationError("لا يمكنك السحب بعد ما انتهت العمليه")
        elif not self.process_time:
            raise ValidationError("هذه العمليه لم يتم تنفيذها من قبل")
        else:
            content = self.env['submission']
            return {
                'name': 'Actual consumption',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'submission',
                'res_id': content.id,
                'type': 'ir.actions.act_window',
                'target': 'new',
            }

    # a function that calculates the running time and stores it in the duration field and converts it into a string
    # for display
    def process_timing(self):
        if self.process_time:
            current_product = self.env['factory.product'].browse(self.ids[0])
            time = (datetime.now() - self.process_time).total_seconds()
            time = current_product.duration + time
            current_product.duration = time
            time_text = str(timedelta(seconds=int(time)))
            current_product.duration_text = time_text
