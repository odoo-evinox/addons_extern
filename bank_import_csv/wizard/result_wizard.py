
from odoo import _, api, fields, models

class ResultWizard(models.TransientModel):
    _name = "result.wizard"
    _description = "A model just to show results"

    text1 = fields.Text(readonly=1)
    text2 = fields.Text(readonly=1)
    text3 = fields.Text(readonly=1)
