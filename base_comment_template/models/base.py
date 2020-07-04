# Copyright 2020 NextERP Romania SRL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models
from odoo.tools import safe_eval


class Base(models.AbstractModel):
    _inherit = "base"

    def get_comment_template(self, position=False, partner_id=False):
        self.ensure_one()
        template = False
        default_dom = [
            ("model", "=", self._name),
            ("position", "=", position),
            ("default", "=", True),
        ]
        templates = self.env["base.comment.template"].search(default_dom)
        if partner_id:
            partner_dom = [
                ("model", "=", self._name),
                ("position", "=", position),
                ("partner_id", "=", partner_id),
            ]
            part_templates = self.env["base.comment.template"].search(partner_dom)
            lang = self.env["res.partner"].browse(partner_id).lang
            if part_templates:
                templates = part_templates.with_context({"lang": lang})
        if templates:
            for templ in templates:
                if self in self.search(safe_eval(templ.domain or "[]")):
                    template = templ
                    break
        if not template:
            return False
        return template
