# © 2013-2014 Nicolas Bessi (Camptocamp SA)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Base Comments Templates",
    "summary": "Add conditional mako template to any report "
    "",
    "description":"""Add conditional mako template
With this module, you can make reports or part of reports like a email template ( using mako sintax).
To do this, a report must inherit comment.template
 The reports can be conditional based on user, compnay.. and any value put with a domain
 
  """,
  
    
    "version": "14.0.1.0.0",
    "category": "Reporting",
    "website": "https://github.com/OCA/reporting-engine",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "installable": True,
    "depends": ["base", "mail"],
    "data": [
        "security/ir.model.access.csv",
        "security/security.xml",
        "views/base_comment_template_view.xml",
        "views/res_partner_view.xml",
    ],
}
