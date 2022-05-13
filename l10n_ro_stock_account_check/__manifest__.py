# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Stock Accounting Check",
    "version": "14.0.1.0.0",
    "author": "NextERP Romania SRL",
    "website": "https://nexterp.ro",
    "category": "Stock",
    "depends": [
        "l10n_ro_stock_account",
        "purchase_stock",
        "sale_stock",
    ],
    "data": [
        "report/stock_check_report_view.xml",
        "security/ir.model.access.csv",
    ],
    "installable": True,
    "maintainers": ["feketemihai"],
}
