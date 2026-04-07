"""
LB-PAMS Workflow & Notification Setup Script.

Creates the Land Master Approval Workflow and related notifications.
Run via: bench --site <site> execute lbpams.setup_workflow.setup_land_workflow
"""

import frappe
from frappe import _


def setup_land_workflow():
    """Create or update the Land Master Approval Workflow."""
    print("=" * 60)
    print("Setting up Land Master Approval Workflow")
    print("=" * 60)

    # Ensure all required Workflow State and Action documents exist
    _ensure_workflow_prerequisites()

    workflow_name = "Land Master Approval"

    # Delete existing workflow if present (for clean re-creation)
    if frappe.db.exists("Workflow", workflow_name):
        frappe.delete_doc("Workflow", workflow_name, force=True)
        print(f"  Deleted existing workflow: {workflow_name}")

    # ──── Create Workflow ────
    workflow = frappe.new_doc("Workflow")
    workflow.workflow_name = workflow_name
    workflow.document_type = "Land Master"
    workflow.is_active = 1
    workflow.override_status = 0
    workflow.send_email_alert = 1

    # ──── Workflow States ────
    states = [
        {
            "state": "Draft",
            "doc_status": "0",
            "is_optional_state": 0,
            "allow_edit": "Land Manager",
            "style": ""
        },
        {
            "state": "Under Verification",
            "doc_status": "0",
            "is_optional_state": 0,
            "allow_edit": "Legal Team",
            "style": "Warning"
        },
        {
            "state": "Legally Verified",
            "doc_status": "0",
            "is_optional_state": 0,
            "allow_edit": "Legal Team",
            "style": "Primary"
        },
        {
            "state": "Approved for Development",
            "doc_status": "1",
            "is_optional_state": 0,
            "allow_edit": "Management",
            "style": "Success"
        },
        {
            "state": "Under Litigation",
            "doc_status": "0",
            "is_optional_state": 0,
            "allow_edit": "Legal Team",
            "style": "Danger"
        },
        {
            "state": "On Hold",
            "doc_status": "0",
            "is_optional_state": 0,
            "allow_edit": "Management",
            "style": ""
        },
        {
            "state": "Rejected",
            "doc_status": "1",
            "is_optional_state": 0,
            "allow_edit": "Management",
            "style": "Inverse"
        },
    ]

    for state_data in states:
        workflow.append("states", state_data)

    # ──── Workflow Transitions ────
    transitions = [
        # Normal forward flow
        {
            "state": "Draft",
            "action": "Submit for Verification",
            "next_state": "Under Verification",
            "allowed": "Land Manager",
            "allow_self_approval": 1,
            "condition": "doc.survey_details"
        },
        # Legal team verifies
        {
            "state": "Under Verification",
            "action": "Mark as Legally Verified",
            "next_state": "Legally Verified",
            "allowed": "Legal Team",
            "allow_self_approval": 1,
        },
        # Legal team flags litigation
        {
            "state": "Under Verification",
            "action": "Flag as Under Litigation",
            "next_state": "Under Litigation",
            "allowed": "Legal Team",
            "allow_self_approval": 1,
        },
        # Legal team returns to draft
        {
            "state": "Under Verification",
            "action": "Return to Draft",
            "next_state": "Draft",
            "allowed": "Legal Team",
            "allow_self_approval": 1,
        },
        # Management approves for development
        {
            "state": "Legally Verified",
            "action": "Approve for Development",
            "next_state": "Approved for Development",
            "allowed": "Management",
            "allow_self_approval": 1,
            "condition": "doc.land_compliance and doc.land_compliance[0].development_eligible != 'No'"
        },
        # Management puts on hold
        {
            "state": "Legally Verified",
            "action": "Put On Hold",
            "next_state": "On Hold",
            "allowed": "Management",
            "allow_self_approval": 1,
        },
        # Management rejects
        {
            "state": "Legally Verified",
            "action": "Reject",
            "next_state": "Rejected",
            "allowed": "Management",
            "allow_self_approval": 1,
        },
        # Litigation resolved — back to verification
        {
            "state": "Under Litigation",
            "action": "Litigation Resolved",
            "next_state": "Under Verification",
            "allowed": "Legal Team",
            "allow_self_approval": 1,
        },
        # Resume from hold
        {
            "state": "On Hold",
            "action": "Resume",
            "next_state": "Legally Verified",
            "allowed": "Management",
            "allow_self_approval": 1,
        },
    ]

    for transition_data in transitions:
        workflow.append("transitions", transition_data)

    workflow.insert(ignore_permissions=True)
    print(f"  Created workflow: {workflow_name}")
    print(f"  States: {len(states)}")
    print(f"  Transitions: {len(transitions)}")

    frappe.db.commit()

    # ──── Create Notifications ────
    setup_notifications()

    print("=" * 60)
    print("Workflow setup complete!")
    print("=" * 60)


def setup_notifications():
    """Create notification configurations for Land Master."""

    # ──── Notification 1: Land Litigation Flag ────
    notif_name = "Land Litigation Flag Alert"
    if frappe.db.exists("Notification", notif_name):
        frappe.delete_doc("Notification", notif_name, force=True)

    notif = frappe.new_doc("Notification")
    notif.name = notif_name
    notif.subject = "[URGENT] Litigation flagged: {{ doc.land_name }} ({{ doc.name }})"
    notif.document_type = "Land Master"
    notif.event = "Value Change"
    notif.value_changed = "workflow_state"
    notif.enabled = 1
    notif.channel = "Email"
    notif.condition = 'doc.workflow_state == "Under Litigation"'

    notif.message = """
<h3>⚠ Land Litigation Alert</h3>
<table style="border-collapse: collapse; width: 100%;">
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Land ID</strong></td>
        <td style="padding: 8px; border: 1px solid #ddd;">{{ doc.name }}</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Land Name</strong></td>
        <td style="padding: 8px; border: 1px solid #ddd;">{{ doc.land_name }}</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Location</strong></td>
        <td style="padding: 8px; border: 1px solid #ddd;">{{ doc.village or '' }}, {{ doc.mandal }}, {{ doc.district }}</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Extent</strong></td>
        <td style="padding: 8px; border: 1px solid #ddd;">{{ doc.total_extent_display }}</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Flagged By</strong></td>
        <td style="padding: 8px; border: 1px solid #ddd;">{{ frappe.session.user }}</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Flagged On</strong></td>
        <td style="padding: 8px; border: 1px solid #ddd;">{{ frappe.utils.now_datetime() }}</td></tr>
</table>
<p>This land parcel has been flagged as <strong>Under Litigation</strong>. Immediate legal review is required.</p>
<p><a href="{{ frappe.utils.get_url_to_form('Land Master', doc.name) }}">View Land Record →</a></p>
"""

    # Send to Legal Team and Management roles
    notif.append("recipients", {
        "receiver_by_role": "Legal Team"
    })
    notif.append("recipients", {
        "receiver_by_role": "Management"
    })

    notif.insert(ignore_permissions=True)
    print(f"  Created notification: {notif_name}")

    # ──── Notification 2: Workflow State Change ────
    notif_name_2 = "Land Workflow State Change"
    if frappe.db.exists("Notification", notif_name_2):
        frappe.delete_doc("Notification", notif_name_2, force=True)

    notif2 = frappe.new_doc("Notification")
    notif2.name = notif_name_2
    notif2.subject = "Land {{ doc.name }}: Status changed to {{ doc.workflow_state }}"
    notif2.document_type = "Land Master"
    notif2.event = "Value Change"
    notif2.value_changed = "workflow_state"
    notif2.enabled = 1
    notif2.channel = "Email"
    notif2.condition = 'doc.workflow_state != "Under Litigation"'  # Litigation has its own alert

    notif2.message = """
<h3>Land Status Update</h3>
<table style="border-collapse: collapse; width: 100%;">
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Land ID</strong></td>
        <td style="padding: 8px; border: 1px solid #ddd;">{{ doc.name }}</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Land Name</strong></td>
        <td style="padding: 8px; border: 1px solid #ddd;">{{ doc.land_name }}</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>New Status</strong></td>
        <td style="padding: 8px; border: 1px solid #ddd;"><strong>{{ doc.workflow_state }}</strong></td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Location</strong></td>
        <td style="padding: 8px; border: 1px solid #ddd;">{{ doc.village or '' }}, {{ doc.mandal }}, {{ doc.district }}</td></tr>
</table>
<p><a href="{{ frappe.utils.get_url_to_form('Land Master', doc.name) }}">View Land Record →</a></p>
"""

    # Send to document owner
    notif2.append("recipients", {
        "receiver_by_document_field": "owner"
    })

    notif2.insert(ignore_permissions=True)
    print(f"  Created notification: {notif_name_2}")

    frappe.db.commit()


def _ensure_workflow_prerequisites():
    """Create Workflow State and Workflow Action Master documents if they don't exist."""
    # States
    state_defs = [
        {"name": "Draft", "style": ""},
        {"name": "Under Verification", "style": "Warning"},
        {"name": "Legally Verified", "style": "Primary"},
        {"name": "Approved for Development", "style": "Success"},
        {"name": "Under Litigation", "style": "Danger"},
        {"name": "On Hold", "style": ""},
        {"name": "Rejected", "style": "Inverse"},
    ]
    for s in state_defs:
        if not frappe.db.exists("Workflow State", s["name"]):
            doc = frappe.new_doc("Workflow State")
            doc.workflow_state_name = s["name"]
            doc.style = s["style"]
            doc.insert(ignore_permissions=True)
            print(f"  Created Workflow State: {s['name']}")

    # Actions
    action_names = [
        "Submit for Verification",
        "Mark as Legally Verified",
        "Flag as Under Litigation",
        "Return to Draft",
        "Approve for Development",
        "Put On Hold",
        "Reject",
        "Litigation Resolved",
        "Resume",
    ]
    for action_name in action_names:
        if not frappe.db.exists("Workflow Action Master", action_name):
            doc = frappe.new_doc("Workflow Action Master")
            doc.workflow_action_name = action_name
            doc.insert(ignore_permissions=True)
            print(f"  Created Workflow Action: {action_name}")

    frappe.db.commit()


def setup_all():
    """Run complete workflow and notification setup."""
    setup_land_workflow()
