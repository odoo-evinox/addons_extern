# Copyright (C) 2022 NextERP Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import sys


def install(package):
    try:
        __import__(package)
    except Exception:
        import subprocess

        subprocess.call([sys.executable, "-m", "pip", "install", package])


install("openupgradelib")

try:
    from openupgradelib import openupgrade
except ImportError:
    openupgrade = None


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    openupgrade.rename_tables(
        env.cr,
        [
            ("stock_accounting_check", "l10n_ro_stock_accounting_check"),
            ("stock_accounting_check_line", "l10n_ro_stock_accounting_check_line"),
        ],
    )
    openupgrade.rename_models(
        env.cr,
        [
            ("stock.accounting.check", "l10n.ro.stock.accounting.check"),
            ("stock.accounting.check.line", "l10n.ro.stock.accounting.check.line"),
        ],
    )
