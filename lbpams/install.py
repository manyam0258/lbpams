"""
LB-PAMS Installation Hooks.

Runs after app installation to set up workflows, notifications, and master data.
"""

import frappe


def after_install():
    """Called after lbpams app is installed on a site."""
    print("Running LB-PAMS post-install setup...")

    # Create custom roles
    from lbpams.setup import create_custom_roles
    create_custom_roles()

    # Populate Telangana master data
    from lbpams.setup import populate_telangana_data
    populate_telangana_data()

    # Set up workflow and notifications
    from lbpams.setup_workflow import setup_land_workflow
    setup_land_workflow()

    print("LB-PAMS post-install setup complete!")
