from odoo import models, fields,api


class Submission(models.Model):
    _name = "submission"
    _description = "the model of the submission form"

    forum = fields.One2many("process.parts", "forum_parts")
    current_workers = fields.One2many("submission.intermediate", "current_workers")
    standard_parts = fields.One2many("process.parts", "something", readonly=True,
                                     compute="test")

    @api.onchange('current_workers')
    def test(self):
        process_id = self.env['factory.product'].browse(self._context.get('active_id')).states
        self.standard_parts = process_id.process_parts

    def submit(self):
        workers = ":".join([worker.name.name for worker in self.current_workers])
        self.env['factory.product'].browse(self._context.get('active_id')).worker = workers
        self.env['factory.product'].browse(self._context.get('active_id')).actual_parts = self.forum


class SubmissionIntermediate(models.Model):
    _name = "submission.intermediate"
    _description = "a model to allow the selection of workers"

    name = fields.Many2one("workers")
    current_workers = fields.Many2one("submission", "current_workers")
