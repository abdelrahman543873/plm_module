from odoo import models, fields


class Log(models.Model):
    _name = "log"
    _description = "a model that is used to store the log of each product and it's time,raw material and cost " \
                   "consumption "

    name = fields.Text(string="process")
    # the part that the process used
    part = fields.Text(required=True, string="part")
    # the quantity of the part used
    value = fields.Float(string="quantity", required=True)
    # the difference between the standard value and the actual one
    difference = fields.Float(string="difference in materials")
    # the time taken by the process
    time = fields.Text(string="time")
    # worker who worked in the process
    worker_name = fields.Text(string="Worker")
    # the total cost of the process
    cost = fields.Integer(string="cost", store=True)
    # calculating the time difference
    time_difference = fields.Integer(string="time difference")
