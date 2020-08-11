from odoo import models, fields, api
from odoo.exceptions import ValidationError


class Workers(models.Model):
    _name = "workers"
    _description = "workers at the factory"

    name = fields.Text(string="name")
    hour_salary = fields.Integer(string="hour price")
    number_hours = fields.Integer(string="hours number")
    image = fields.Binary(string="image", attachment=True)
    total_salary = fields.Integer(string="total salary", compute="total_money", readonly=True, store=True)

    @api.constrains("hour_salary", "number_hours")
    def checking(self):
        if self.hour_salary < 0 or self.number_hours < 0:
            raise ValidationError("enter valid hour salary")

    @api.depends('hour_salary', 'number_hours')
    def total_money(self):
        for rec in self:
            rec.total_salary = rec.hour_salary * rec.number_hours

    _sql_constraints = [
        ('name_unique',
         'UNIQUE(name)',
         "this worker name already exists")
    ]
