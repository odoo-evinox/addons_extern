# Copyright (C) 2020 NextERP Romania
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, SUPERUSER_ID

def post_init_hook(cr, registry):
    """Loaded after installing the module."""

    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        # Update portal ir.rules to allow access right to portal users
        # on all project types.
        # project.project_task_rule_portal
        # project.project_project_rule_portal
        new_task_domain = """[
        '|',
                ('project_id.message_partner_ids', 'child_of', [user.partner_id.commercial_partner_id.id]),
                ('message_partner_ids', 'child_of', [user.partner_id.commercial_partner_id.id]),
        ]"""
        task_rule = env.ref("project.project_task_rule_portal")
        task_rule.domain_force = new_task_domain

        new_project_domain = """[
                ('message_partner_ids', 'child_of', [user.partner_id.commercial_partner_id.id]),
        ]"""
        project_rule = env.ref("project.project_project_rule_portal")
        project_rule.domain_force = new_project_domain


def uninstall_hook(cr, registry):
    """Loaded before uninstalling the module."""
    # Update portal ir.rules to initial domain
    # project.project_task_rule_portal
    # project.project_project_rule_portal
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        old_task_domain = """[
                ('project_id.privacy_visibility', '=', 'portal'),
                ('allowed_user_ids', 'in', user.ids),
            ]"""
        task_rule = env.ref("project.project_task_rule_portal")
        task_rule.domain_force = old_task_domain
        old_project_domain = """[
                ('privacy_visibility', '=', 'portal'),
                ('allowed_portal_user_ids', 'in', user.ids),
            ]"""
        project_rule = env.ref("project.project_project_rule_portal")
        project_rule.domain_force = old_project_domain