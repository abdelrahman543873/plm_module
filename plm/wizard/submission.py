from odoo import models, fields


class Submission(models.Model):
    _name = "submission"

    actual_parts = fields.One2many("process.parts", "forum_parts")
    current_workers = fields.One2many("submission.intermediate", "current_workers")

    def submit(self):
        workers = ":".join([worker.name.name for worker in self.current_workers])
        self.env['factory.product'].browse(self._context.get('active_id')).worker = workers
        self.env['factory.product'].browse(self._context.get('active_id')).actual_parts = self.actual_parts


class SubmissionIntermediate(models.Model):
    _name = "submission.intermediate"

    name = fields.Many2one("workers")
    current_workers = fields.Many2one("submission", "current_workers")