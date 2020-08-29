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
    # the actual parts that was taken by the process
    actual_parts = fields.One2many("process.parts", "actual_parts", string="actual parts")
    # the log of the product with the processes that the product went through and their consumption
    actual_process = fields.Many2many("log", string="log", readonly=True, copy=False)
    # a field that detects the state of the product completed,pause or finalized
    status = fields.Selection([("running", "Running"), ("pause", "Paused"), ("completed", "Completed")],
                              default="pause", copy=False)
    # a variable that is used to store the value of the timestamp of when the process started running
    process_time = fields.Datetime(string="process timing", store=True)
    # calculate Duration of the process
    duration = fields.Integer(string="duration", store=True)
    # output duration in text
    duration_text = fields.Text(string="duration_text", store=True)
    # worker who worked on this process
    worker = fields.Text(string="text", store=True, copy=False)
    # a boolean field that is a marker when the product is completed
    complete = fields.Boolean(string="completed", default=False, compute="complete_check", store=True)

    @api.depends('process', 'actual_process')
    def complete_check(self):
        if [i.name for i in self.process] == [i.name for i in self.actual_process]:
            self.complete = True

    @api.onchange('process')
    def set_states_domain(self):
        return {'domain': {'states': [('name', 'in', [i.name for i in self.process])]}}

    @api.onchange('actual_process')
    @api.depends('actual_process')
    def total_cost(self):
        self.actual_price = sum([i.cost for i in self.actual_process])

    @api.onchange('status')
    def check_status(self):
        # this statement is to make sure that the record is created and the onchange method is not going to execute
        # anything unless the record is already stored in the model
        if self.create_date:
            # a variable that is created to store the previous value of status so we can't move to another status
            # if the current status was completed
            previous = self.env['factory.product'].browse(self.ids[0]).status
            if previous == "completed" and self.states:
                raise ValidationError("لا تستطيع تغير العمليه بعد ان تمت")
            elif self.status == "running":
                # when the process status is changed to running a datetime stamp is created to document when the
                # process started running
                self.env['factory.product'].browse(self.ids[0]).process_time = datetime.now()
            elif self.status == "completed":
                raise ValidationError("عليك الاستهلاك من المخزن اولا")
            else:
                # this function will store the time difference when the process state changed from running to any
                # other state and store it in the duration field to calculate how much time did the process take
                self.process_timing()
        else:
            if self.status != "pause":
                raise ValidationError("لا يمكن ان تغير حاله العمليه فبل ان تحفظها")

    # this checks if the process was completed or if it was a current state and prohibits removing it if that's the case
    @api.onchange('process')
    def check_process(self):
        if self.create_date:
            if self.states.name not in [i.name for i in self.process]:
                raise ValidationError("لا يمكنك حذف العمليه")
            elif self.actual_process:
                completed_processes = list(set([process.name for process in self.actual_process]))
                for process in self.process:
                    if process.name in completed_processes:
                        raise ValidationError("لا يمكن حذف عمليه مكتمله")

    @api.onchange('states')
    def check_state(self):
        if self.states and self.process:
            # if the current state isn't in the standard processes table it can't be selected
            if self.states.name not in [process.name for process in self.process]:
                raise ValidationError("process doesn't exist for this product")
            # if the process isn't completed you can't move to another process
            elif self.status != "completed" and self.create_date:
                raise ValidationError("لا يمكنك الاانتفال قبل انهاء العمليه الاولي")
            # checks if the process has been completed before
            elif self.states.name in list(set([i.name for i in self.actual_process])):
                raise ValidationError("هذه العمله تمت بالفعل")
            else:
                # all of the behaviour here happens when the product is created
                if self.create_date:
                    # whenever a process is selected the status is set to running
                    self.env['factory.product'].browse(self.ids[0]).status = "running"
                    # the process_time is reset so that the new process running time is calculated
                    self.env['factory.product'].browse(self.ids[0]).process_time = datetime.now()
                    # the duration is set to 0 so that the new process time is calculated
                    self.env['factory.product'].browse(self.ids[0]).duration = 0
                    # remove the old worker to assign new one for the new process
                    self.env['factory.product'].browse(self.ids[0]).worker = False
                    # making the actual parts table empty so that the actual parts are edited for each process
                    self.actual_parts = [(6, 0, [])]
        elif self.states and not self.process:
            raise ValidationError("process doesn't exist")

    @api.constrains('price')
    def check_quantity(self):
        if self.price <= 0:
            raise ValidationError("money can't be zero")

    @api.constrains('actual_parts')
    def checking_parts_repetition(self):
        if self.actual_parts:
            parts = [i.name for i in self.actual_parts]
            for i in parts:
                if parts.count(i) > 1:
                    raise ValidationError("parts are repeated !!")

    # a function that does the subtraction from the store after the process transition is done
    def order(self):
        if not self.create_date:
            raise ValidationError("لا يمكن الاستهلاك قبل ان تحفظ العمليه")
        elif self.status == "completed":
            raise ValidationError("لا يمكنك السحب بعد ما انتهت العمليه")
        elif not self.worker:
            raise ValidationError("ادخل العامل اولا")
        elif not self.process_time:
            raise ValidationError("هذه العمليه لم يتم تنفيذها من قبل")
        elif self.actual_parts:
            """this is executed if there exists actual parts which differ from the standard parts of the process
            and the try statement here is to make sure that the parts that exist in the standard process template
            is in the actual parts template"""
            if self.status == "running":
                self.process_timing()
            parts_names = [i.name.name for i in self.states.process_parts]
            standard_quantity = dict([tuple((i.name.name, i.quantity)) for i in self.states.process_parts])
            actual_quantity = dict([tuple((i.name.name, i.quantity)) for i in self.actual_parts])
            self.subtract_from_database(self.actual_parts, 'inventory.parts')
            # this is done outside cause self.duration_text fails inside the try and except clause
            for name in parts_names:
                try:
                    difference = standard_quantity[name] - actual_quantity[name]
                    actual_processes_names = [process.name for process in self.actual_process]
                    cost = self.cost(name, actual_quantity[name], self.worker, int(self.duration),
                                     actual_processes_names)
                    self.fill_log_table(actual_processes_names, self.states.name, name, actual_quantity[name], cost,
                                        self.worker, difference, self.duration_text, self.time_difference())
                    # add the worker time to his working hours
                    self.worker_time()
                except KeyError:
                    raise ValidationError("لم تختر كل القطع الموجوده في هذه العمليه")
            # increase the parts quantity when the process is completed
            self.increase_inventory("inventory.parts", self.states.quantity)
        elif self.states.process_parts:
            """this if statement is executed if there is no actual_parts and then the standard is subtracted
                    and the values are added to the actual process table through the [(0,0,values)] command"""
            if self.status == "running":
                # this will allow the storing of the time of the process when the purchase button is clicked
                self.process_timing()
            self.subtract_from_database(self.states.process_parts, 'inventory.parts')
            for part in self.states.process_parts:
                self.worker_time()
                actual_processes_names = [process.name for process in self.actual_process]
                cost = self.cost(part.name.name, part.quantity, self.worker, int(self.duration),
                                 actual_processes_names)
                self.fill_log_table(actual_processes_names, self.states.name, part.name.name, part.quantity, cost,
                                    self.worker, 0, self.duration_text, self.time_difference())
            # increase the parts quantity when the process is completed
            self.increase_inventory("inventory.parts", self.states.quantity)
        else:
            raise ValidationError("nothing to subtract")

    # a function that calculates the running time and stores it in the duration field and converts it into a string
    # for display
    def process_timing(self):
        if self.process_time:
            time = datetime.now() - self.process_time
            time = time.total_seconds()
            time = self.env['factory.product'].browse(self.ids[0]).duration + time
            self.env['factory.product'].browse(self.ids[0]).duration = time
            time_text = str(timedelta(seconds=int(time)))
            self.env['factory.product'].browse(self.ids[0]).duration_text = time_text

    # a function that allows the time to be added to the worker's time to increase his salary
    def worker_time(self):
        text_time = str(timedelta(seconds=int(self.duration))).split(":")
        hours_time = int(text_time[1]) / 60 + int(text_time[2])
        for worker in self.worker.split(":"):
            worker_hours = self.env['workers'].search([('name', '=', worker)]).number_hours + int(hours_time)
            self.env['workers'].search([('name', '=', worker)]).number_hours = worker_hours

    # a function that subtracts from the database and sets the process to complete
    def subtract_from_database(self, processes, model_name):
        for part in processes:
            # the logic for subtracting the consumption from the inventory
            final_quantity = self.env[model_name].browse(part.name.id).quantity - part.quantity
            if final_quantity <= 0:
                raise ValidationError("you don't have enough quantity")
            self.env[model_name].browse(part.name.id).quantity = final_quantity
            self.status = "completed"

    def cost(self, part, quantity, worker, duration, processes):
        parts_cost = self.env['inventory.parts'].search([('name', '=', part)]).item_price * quantity
        worker_cost = 0
        for worker in worker.split(":"):
            worker_cost += self.env['workers'].search([('name', '=', worker)]).hour_salary * int(duration / 3600)
        if self.states.name in processes:
            return parts_cost
        else:
            return parts_cost + worker_cost

    def fill_log_table(self, processes, process_name, part_name, part_quantity, cost, worker_name, difference, time
                       , time_difference):
        if self.states.name in processes:
            values = {"part": part_name, "value": part_quantity,
                      "cost": cost}
        else:
            values = {"name": process_name, "part": part_name, "value": part_quantity, "difference": difference,
                      "time": time, "worker_name": worker_name, "cost": cost, "time_difference": time_difference}
        self.actual_process = [(0, 0, values)]

    def increase_inventory(self, model_name, quantity):
        if self.states.output:
            self.env[model_name].search([('name', '=', self.states.output.name)]).quantity += quantity

    def time_difference(self):
        if self.duration:
            time_difference = self.states.time - (self.duration / 60)
            return int(time_difference)
