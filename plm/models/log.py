from odoo import models, fields


class Log(models.Model):
    _name = "log"
    _description = "a model that is used to store the log of each product and it's time,raw material and cost " \
                   "consumption "

    name = fields.Text(string="process")
    part = fields.Text(required=True, string="part")
    value = fields.Float(string="quantity", required=True)
    difference = fields.Float(string="difference in materials")
    time = fields.Text(string="time")
    worker_name = fields.Text(string="Worker")
    cost = fields.Integer(string="cost", store=True)
    time_difference = fields.Integer(string="time difference")
    notes = fields.Text(string="notes")
    rating = fields.Integer(string="rating")
