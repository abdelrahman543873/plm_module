from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta


class Submission(models.Model):
    _name = "submission"
    _description = "the model of the submission form"

    current_workers = fields.One2many("submission.intermediate", "current_workers")
    standard_parts = fields.One2many("process.parts", "something", readonly=True,
                                     compute="parts")
    actual_parts = fields.One2many("process.parts", "forum_parts")
    notes = fields.Text(string="notes")
    rating = fields.Integer(string="rating")

    @api.constrains('rating')
    def check_rating(self):
        if self.rating < 0 or self.rating > 10:
            raise ValidationError("ادخل رقم اصغر من او يساوي 10 و اكبر من او يساوي 0")

    @api.onchange('current_workers')
    def parts(self):
        process_id = self.env['factory.product'].browse(self._context.get('active_id')).states
        self.standard_parts = process_id.process_parts

    def submit(self):
        if not self.current_workers:
            raise ValidationError("ادخل العمال اولا")
        current_product = self.env['factory.product'].browse(self._context.get('active_id'))
        workers = ':'.join([i.name.name for i in self.current_workers])
        if self.actual_parts:
            """this is executed if there exists actual parts which differ from the standard parts of the process
            and the try statement here is to make sure that the parts that exist in the standard process template
            is in the actual parts template"""
            # this is done outside cause self.duration_text fails inside the try and except clause
            if current_product.status == "running":
                self.process_timing(current_product)
            parts_names = [i.name.name for i in self.standard_parts]
            standard_quantity = dict([tuple((i.name.name, i.quantity)) for i in self.standard_parts])
            actual_quantity = dict([tuple((i.name.name, i.quantity)) for i in self.actual_parts])
            for name in parts_names:
                try:
                    difference = standard_quantity[name] - actual_quantity[name]
                    actual_processes_names = [process.name for process in current_product.actual_process]
                    cost = self.cost(name, actual_quantity[name], workers, int(current_product.duration),
                                     actual_processes_names, current_product)
                    self.fill_log_table(actual_processes_names, current_product.states.name, name,
                                        actual_quantity[name], cost,
                                        workers, difference, current_product.duration_text,
                                        self.time_difference(current_product),
                                        current_product, self.notes, self.rating)
                    self.complete_check(current_product)
                    # add the worker time to his working hours
                    self.worker_time(current_product)
                except KeyError:
                    raise ValidationError("لم تختر كل القطع الموجوده في هذه العمليه")
            self.subtract_from_database(self.actual_parts, 'inventory.parts', current_product)
            # increase the parts quantity when the process is completed
            self.increase_inventory("inventory.parts", current_product.states.quantity, current_product)
        elif self.standard_parts:
            """this if statement is executed if there is no actual_parts and then the standard is subtracted
                    and the values are added to the actual process table through the [(0,0,values)] command"""
            if current_product.status == "running":
                # this will allow the storing of the time of the process when the purchase button is clicked
                self.process_timing(current_product)
            self.subtract_from_database(self.standard_parts, 'inventory.parts', current_product)
            for part in self.standard_parts:
                self.worker_time(current_product)
                actual_processes_names = [process.name for process in current_product.actual_process]
                cost = self.cost(part.name.name, part.quantity, workers, int(current_product.duration),
                                 actual_processes_names, current_product)
                self.fill_log_table(actual_processes_names, current_product.states.name, part.name.name, part.quantity,
                                    cost,
                                    workers, 0, current_product.duration_text, self.time_difference(current_product),
                                    current_product, self.notes, self.rating)
                self.complete_check(current_product)
            # increase the parts quantity when the process is completed
            self.increase_inventory("inventory.parts", current_product.states.quantity, current_product)
        else:
            raise ValidationError("nothing to subtract")

    # a function that calculates the running time and stores it in the duration field and converts it into a string
    # for display
    def process_timing(self, current):
        if current.process_time:
            time = (datetime.now() - current.process_time).total_seconds()
            current.duration = current.duration + time
            time_text = str(timedelta(seconds=int(time)))
            current.duration_text = time_text

    # a function that allows the time to be added to the worker's time to increase his salary
    def worker_time(self, current):
        text_time = str(timedelta(seconds=int(current.duration))).split(":")
        hours_time = int(text_time[1]) / 60 + int(text_time[2])
        for worker in self.current_workers:
            worker_hours = self.env['workers'].search([('name', '=', worker.name.name)]).number_hours + int(hours_time)
            self.env['workers'].search([('name', '=', worker.name.name)]).number_hours = worker_hours

    # a function that subtracts from the database and sets the process to complete
    def subtract_from_database(self, processes, model_name, current):
        for part in processes:
            # the logic for subtracting the consumption from the inventory
            final_quantity = self.env[model_name].browse(part.name.id).quantity - part.quantity
            if final_quantity <= 0:
                raise ValidationError("you don't have enough quantity")
            self.env[model_name].browse(part.name.id).quantity = final_quantity
            current.status = "completed"

    def cost(self, part, quantity, worker, duration, processes, current):
        parts_cost = self.env['inventory.parts'].search([('name', '=', part)]).item_price * quantity
        worker_cost = 0
        for worker in worker.split(":"):
            worker_cost += self.env['workers'].search([('name', '=', worker)]).hour_salary * int(duration / 3600)
        if current.states.name in processes:
            return parts_cost
        else:
            return parts_cost + worker_cost

    def fill_log_table(self, processes, process_name, part_name, part_quantity, cost, worker_name, difference, time,
                       time_difference, current, notes, rating):
        if current.states.name in processes:
            values = {"part": part_name, "value": part_quantity,
                      "cost": cost}
        else:
            values = {"name": process_name, "part": part_name, "value": part_quantity, "difference": difference,
                      "time": time, "worker_name": worker_name, "cost": cost, "time_difference": time_difference,
                      "rating": rating, "notes": notes}
        current.actual_process = [(0, 0, values)]

    def increase_inventory(self, model_name, quantity, current):
        if current.states.output:
            self.env[model_name].search([('name', '=', current.states.output.name)]).quantity += quantity

    def time_difference(self, current):
        if current.duration:
            time_difference = current.states.time - (current.duration / 60)
            return int(time_difference)

    def complete_check(self, current):
        if [i.name for i in current.process] == [i.name for i in current.actual_process]:
            current.complete = True


class SubmissionIntermediate(models.Model):
    _name = "submission.intermediate"
    _description = "a model to allow the selection of workers"

    name = fields.Many2one("workers")
    current_workers = fields.Many2one("submission", "current_workers")
