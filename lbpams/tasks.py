"""
LB-PAMS Scheduled Tasks.

Contains scheduled jobs for periodic checks and notifications.
Registered in hooks.py under scheduler_events.
"""

import frappe
from frappe import _
from frappe.utils import today, getdate, add_days


def weekly_missing_documents_report():
    """
    Weekly job: Email summary of Land Master records with missing critical documents.
    Runs every Monday via Frappe scheduler.

    Queries all Land Master records where risk_flag = 1,
    identifies which critical documents are missing for each,
    and sends a summary email to the Land Manager role.
    """
    # Get all land records with risk flag active (draft or submitted)
    land_records = frappe.get_all(
        "Land Master",
        filters={"risk_flag": 1, "docstatus": ["<", 2]},
        fields=["name", "land_name", "mandal", "district", "total_extent_display",
                "current_status", "title_status", "owner"],
        order_by="district, mandal"
    )

    if not land_records:
        return  # No flagged records — nothing to report

    # Required document types
    required_types = {"EC", "Sale Deed", "Pahani (ROR)", "FMB Sketch"}

    # Build the report data
    report_rows = []

    for land in land_records:
        # Get document types present for this land
        doc_types = frappe.get_all(
            "Encumbrance Document",
            filters={"parent": land.name, "parenttype": "Land Master"},
            fields=["document_type"],
            pluck="document_type"
        )

        doc_types_set = set(doc_types)
        # Backward compat: treat "Pahani" as "Pahani (ROR)"
        if "Pahani" in doc_types_set:
            doc_types_set.add("Pahani (ROR)")

        missing = required_types - doc_types_set

        if missing or land.title_status in ("Gap in Chain", "Overlapping Ownership", "Disputed"):
            issues = []
            if missing:
                issues.append(f"Missing: {', '.join(sorted(missing))}")
            if land.title_status and land.title_status not in ("Not Assessed", "Clear Title"):
                issues.append(f"Title: {land.title_status}")
            if land.current_status == "Under Litigation":
                issues.append("Under Litigation")

            report_rows.append({
                "land_id": land.name,
                "land_name": land.land_name,
                "location": f"{land.mandal}, {land.district}",
                "extent": land.total_extent_display or "",
                "issues": "; ".join(issues),
                "owner": land.owner
            })

    if not report_rows:
        return

    # Build HTML table
    table_rows = ""
    for row in report_rows:
        link = frappe.utils.get_url_to_form("Land Master", row["land_id"])
        table_rows += f"""
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;">
                <a href="{link}">{row['land_id']}</a>
            </td>
            <td style="padding: 8px; border: 1px solid #ddd;">{row['land_name']}</td>
            <td style="padding: 8px; border: 1px solid #ddd;">{row['location']}</td>
            <td style="padding: 8px; border: 1px solid #ddd;">{row['extent']}</td>
            <td style="padding: 8px; border: 1px solid #ddd; color: #dc3545;">
                {row['issues']}
            </td>
        </tr>
        """

    message = f"""
    <h2>📋 Weekly Missing Documents Report — LB-PAMS</h2>
    <p>The following <strong>{len(report_rows)}</strong> land parcels have pending document
    or title chain issues that need attention:</p>

    <table style="border-collapse: collapse; width: 100%; margin-top: 16px;">
        <thead>
            <tr style="background-color: #f8f9fa;">
                <th style="padding: 10px; border: 1px solid #ddd; text-align: left;">Land ID</th>
                <th style="padding: 10px; border: 1px solid #ddd; text-align: left;">Name</th>
                <th style="padding: 10px; border: 1px solid #ddd; text-align: left;">Location</th>
                <th style="padding: 10px; border: 1px solid #ddd; text-align: left;">Extent</th>
                <th style="padding: 10px; border: 1px solid #ddd; text-align: left;">Issues</th>
            </tr>
        </thead>
        <tbody>
            {table_rows}
        </tbody>
    </table>

    <p style="margin-top: 16px; color: #6c757d;">
        Report generated on {today()} by LB-PAMS Weekly Document Check.
        <br>
        <a href="{frappe.utils.get_url()}/app/land-master?risk_flag=1">
            View all flagged land records →
        </a>
    </p>
    """

    # Get all users with Land Manager role
    land_managers = frappe.get_all(
        "Has Role",
        filters={"role": "Land Manager", "parenttype": "User"},
        fields=["parent"],
        pluck="parent"
    )

    if not land_managers:
        # Fallback to System Manager
        land_managers = [frappe.session.user or "Administrator"]

    # Send email
    frappe.sendmail(
        recipients=land_managers,
        subject=f"[LB-PAMS] Weekly Missing Documents Report — {len(report_rows)} parcels need attention",
        message=message,
        now=True
    )

    frappe.log_error(
        title="Weekly Missing Documents Report Sent",
        message=f"Report sent to {len(land_managers)} users covering {len(report_rows)} flagged parcels."
    )
