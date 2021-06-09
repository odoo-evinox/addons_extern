import logging

from odoo import _, api, fields, models
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)


class stock_picking(models.Model):
    _inherit = ["stock.picking", "comment.template"]
    _name = "stock.picking"

    purchase_id = fields.Many2one(
        "purchase.order", readonly=1, string="Created by this purchase"
    )

    delegate_id = fields.Many2one("res.partner", string="Delegate")
    mean_transp = fields.Char(string="Mean transport")

    installed_stock_picking_report_valued = fields.Boolean(
        compute="_compute_installed_stock_picking_report_valued", compute_sudo=True
    )

    show_shop_price = fields.Boolean(
        compute="_compute_installed_stock_picking_report_valued", compute_sudo=True
    )

    def _compute_installed_stock_picking_report_valued(self):
        stock_piging_report_valued = self.env["ir.module.module"].search(
            [("name", "=", "stock_picking_report_valued")]
        )
        if stock_piging_report_valued.filtered(lambda r: r.state == "installed"):
            self.installed_stock_picking_report_valued = True
            for record in self:
                if (
                    record.purchase_id
                    and record.location_dest_id.merchandise_type == "shop"
                ):
                    record.show_shop_price = True
                else:
                    record.show_shop_price = False
        else:
            self.installed_stock_picking_report_valued = False
            self.show_shop_price = False

    @api.onchange("delegate_id")
    def on_change_delegate_id(self):
        if self.delegate_id:
            self.mean_transp = self.delegate_id.mean_transp

    def write(self, vals):
        "if modified the mean_transp will write into delegate"
        mean_transp = vals.get("mean_transp", False)
        delegate_id = vals.get("delegate_id", False)
        if mean_transp and delegate_id:
            if (
                mean_transp
                != self.env["res.partner"].sudo().browse(delegate_id).mean_transp
            ):
                self.env["res.partner"].sudo().browse(delegate_id).write(
                    {"mean_transp": mean_transp}
                )
        return super().write(vals)

    # this function if from base_comment_template original made by nexterp but was removed, and also position is now selection
    def get_comment_template(
        self, position="before_lines", company_id=False, partner_id=False
    ):
        """Method that is called from report xml and is returning the
        position template as a html if exists
        """
        self.ensure_one()
        if not company_id:
            company_id = self.env.company.id
        present_model_id = self.env["ir.model"].search([("model", "=", self._name)])
        default_dom = [
            ("model_ids", "in", present_model_id.id),
            ("position", "=", position),
        ]
        lang = False
        if partner_id and "partner_id" in self._fields:
            default_dom += [
                "|",
                ("partner_ids", "=", False),
                ("partner_ids", "in", partner_id),
            ]
            lang = self.env["res.partner"].browse(partner_id).lang
        if company_id and "company_id" in self._fields:
            if partner_id and "partner_id" in self._fields:
                default_dom.insert(-3, "&")
            default_dom += [
                "|",
                ("company_id", "=", company_id),
                ("company_id", "=", False),
            ]
        templates = self.env["base.comment.template"].search(
            default_dom,  # order="priority"  this was taken out in oca commit but can be usefull
        )
        if lang:
            templates = templates.with_context({"lang": lang})
        template = False
        if templates:
            for templ in templates:
                if self.filtered_domain(safe_eval(templ.domain or "[]")):
                    template = templ
                    break
        if not template:
            return ""
        ret = self.env["mail.template"]._render_template(
            template.text, self._name, [self.id], post_process=True
        )
        if ret[self.id] == "" and template.text:
            _logger.error(
                f"some error in rendering jinja template_id={template.id} rendered object={self}. View template syntax and if exist those parameters"
            )
        return ret[self.id]
