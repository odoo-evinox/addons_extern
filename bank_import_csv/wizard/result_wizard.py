
from odoo import _, api, fields, models

class ResultWizard(models.TransientModel):
    _name = "result.wizard"
    _description = "A model just to show results"

    text1 = fields.Text()
    text2 = fields.Text()
    text3 = fields.Text()
