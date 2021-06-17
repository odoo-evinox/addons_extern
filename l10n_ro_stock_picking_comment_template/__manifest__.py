# Copyright 2020 NextERP Romania SRL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Romania - Stock Picking Comment Template",
    "category": "Localization",
    "description": """
    This model is going to add a a header and a footer at picking report.
    a transfer of type incoming  will have header RECEPTION NOTE AND DIFFERENCES,  and as footer a table for reception and differencies
    internal to location   - has a signature for giving and receiving
    internal to consume - is a consume

    installed_stock_picking_report_valued field in stock_picking is telling ig the stock_picking_repot_valued is instaleed. If is intaled will show also values in picking
    we didn't put dependency stock_picking_repot_valued because that module is dependent on stock_account that is maybe not used

    """,
    "depends": [
        "sale_stock",
        "purchase_stock",
        "l10n_ro_stock",
        "base_comment_template",  # you can take it from here https://github.com/OCA/reporting-engine.git
    ],
    "data": [
        "data/l10n_ro_stock_picking_comment_template.xml",
        "views/stock_picking_view.xml",
        "views/base_comment_template_view.xml",
        "report/stock_picking_report_valued.xml",
        "report/report_picking.xml",
    ],
    "license": "AGPL-3",
    "version": "14.0.1.0.0",
    "author": "NextERP Romania," "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-romania",
    "installable": True,
    "development_status": "Mature",
    "maintainers": ["feketemihai"],
}
