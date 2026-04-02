#!/usr/bin/env python3
"""
Generate LB-PAMS DocType files for Stages 1-3.
Run this script from the app root: python setup_doctypes.py
"""
import json
import os
from datetime import datetime

BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lbpams", "lbpams", "doctype")
NOW = "2026-04-02 10:00:00.000000"
MODULE = "LBPAMS"


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def write_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=1, sort_keys=False)
    print(f"  Created: {path}")


def write_py(path, content):
    with open(path, "w") as f:
        f.write(content)
    print(f"  Created: {path}")


def write_init(dirpath):
    init_path = os.path.join(dirpath, "__init__.py")
    with open(init_path, "w") as f:
        f.write("")
    print(f"  Created: {init_path}")


def base_doctype(name, **kwargs):
    """Return base DocType dict with defaults."""
    doc = {
        "actions": [],
        "allow_rename": kwargs.get("allow_rename", 1),
        "creation": NOW,
        "doctype": "DocType",
        "engine": "InnoDB",
        "field_order": [],
        "fields": [],
        "index_web_pages_for_search": 1,
        "links": [],
        "modified": NOW,
        "modified_by": "Administrator",
        "module": MODULE,
        "name": name,
        "naming_rule": kwargs.get("naming_rule", "By fieldname"),
        "owner": "Administrator",
        "permissions": [],
        "sort_field": kwargs.get("sort_field", "creation"),
        "sort_order": kwargs.get("sort_order", "DESC"),
    }
    if kwargs.get("autoname"):
        doc["autoname"] = kwargs["autoname"]
    if kwargs.get("is_submittable"):
        doc["is_submittable"] = 1
    if kwargs.get("istable"):
        doc["istable"] = 1
        doc["editable_grid"] = 1
    if kwargs.get("track_changes"):
        doc["track_changes"] = 1
    if kwargs.get("description"):
        doc["description"] = kwargs["description"]
    return doc


def field(fieldname, fieldtype, label=None, **kwargs):
    """Create a field definition."""
    f = {
        "fieldname": fieldname,
        "fieldtype": fieldtype,
    }
    if label:
        f["label"] = label
    for k, v in kwargs.items():
        f[k] = v
    return f


def section_break(fieldname="", label="", **kwargs):
    f = {"fieldname": fieldname or f"sb_{label.lower().replace(' ', '_')}", "fieldtype": "Section Break"}
    if label:
        f["label"] = label
    f.update(kwargs)
    return f


def column_break(fieldname=""):
    return {"fieldname": fieldname or "column_break", "fieldtype": "Column Break"}


def tab_break(fieldname, label):
    return {"fieldname": fieldname, "fieldtype": "Tab Break", "label": label}


def perm(role, **kwargs):
    p = {"role": role, "read": 1}
    for k, v in kwargs.items():
        p[k] = v
    return p


def create_doctype(name, doc, controller_code=None, js_code=None):
    """Create the full DocType file structure."""
    folder_name = name.lower().replace(" ", "_")
    dirpath = os.path.join(BASE_DIR, folder_name)
    ensure_dir(dirpath)

    # Set field_order from fields
    doc["field_order"] = [f["fieldname"] for f in doc.get("fields", []) if f.get("fieldname")]

    # Write JSON
    write_json(os.path.join(dirpath, f"{folder_name}.json"), doc)

    # Write __init__.py
    write_init(dirpath)

    # Write Python controller
    if controller_code is None:
        controller_code = f"""# Copyright (c) 2026, surendhranath and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class {name.replace(' ', '')}(Document):
\tpass
"""
    write_py(os.path.join(dirpath, f"{folder_name}.py"), controller_code)

    # Write JS client script
    if js_code:
        write_py(os.path.join(dirpath, f"{folder_name}.js"), js_code)


# =====================================================================
# STAGE 1: Foundation Masters
# =====================================================================

def create_district_master():
    print("\n[Stage 1] Creating District Master...")
    doc = base_doctype(
        "District Master",
        autoname="field:district_name",
        naming_rule="By fieldname",
        track_changes=1,
        description="Master list of all districts in a state"
    )
    doc["fields"] = [
        field("district_name", "Data", "District Name", reqd=1, unique=1, in_list_view=1, in_standard_filter=1),
        field("state", "Data", "State", default="Telangana", reqd=1, in_list_view=1),
        field("is_active", "Check", "Is Active", default=1),
    ]
    doc["permissions"] = [
        perm("System Manager", create=1, write=1, delete=1, email=1, export=1, print_=1, report=1, share=1),
        perm("Land Manager", create=1, write=1),
        perm("Management", write=1),
    ]
    doc["search_fields"] = "district_name, state"
    doc["title_field"] = "district_name"
    create_doctype("District Master", doc)


def create_mandal_master():
    print("\n[Stage 1] Creating Mandal Master...")
    doc = base_doctype(
        "Mandal Master",
        autoname="field:mandal_name",
        naming_rule="By fieldname",
        track_changes=1,
        description="Master list of all mandals linked to their district"
    )
    doc["fields"] = [
        field("mandal_name", "Data", "Mandal Name", reqd=1, unique=1, in_list_view=1, in_standard_filter=1),
        field("district", "Link", "District", reqd=1, options="District Master", in_list_view=1, in_standard_filter=1),
        field("is_active", "Check", "Is Active", default=1),
    ]
    doc["permissions"] = [
        perm("System Manager", create=1, write=1, delete=1, email=1, export=1, print_=1, report=1, share=1),
        perm("Land Manager", create=1, write=1),
        perm("Management", write=1),
    ]
    doc["search_fields"] = "mandal_name, district"
    doc["title_field"] = "mandal_name"
    create_doctype("Mandal Master", doc)


def create_authority_mapping():
    print("\n[Stage 1] Creating Authority Mapping...")
    doc = base_doctype(
        "Authority Mapping",
        autoname="field:mandal",
        naming_rule="By fieldname",
        track_changes=1,
        description="Maps each mandal to its governing approval authority (GHMC/HMDA/DTCP)"
    )
    doc["fields"] = [
        field("mandal", "Link", "Mandal", reqd=1, unique=1, options="Mandal Master", in_list_view=1, in_standard_filter=1),
        field("district", "Link", "District", options="District Master", read_only=1,
              fetch_from="mandal.district", in_list_view=1),
        field("authority", "Select", "Approval Authority", reqd=1,
              options="\nGHMC\nHMDA\nDTCP", in_list_view=1, in_standard_filter=1),
        field("remarks", "Small Text", "Remarks"),
    ]
    doc["permissions"] = [
        perm("System Manager", create=1, write=1, delete=1, email=1, export=1, print_=1, report=1, share=1),
        perm("Management", create=1, write=1),
    ]
    doc["search_fields"] = "mandal, authority"
    create_doctype("Authority Mapping", doc)


# =====================================================================
# STAGE 2: Land Master Core
# =====================================================================

def create_survey_detail():
    print("\n[Stage 2] Creating Survey Detail (Child Table)...")
    doc = base_doctype(
        "Survey Detail",
        istable=1,
        description="Individual survey number details for a land parcel"
    )
    doc["fields"] = [
        field("survey_number", "Data", "Survey Number", reqd=1, in_list_view=1, columns=2),
        field("subdivision_number", "Data", "Subdivision Number", in_list_view=1, columns=1),
        field("extent_acres", "Float", "Extent (Acres)", in_list_view=1, columns=1, precision=4),
        field("extent_guntas", "Float", "Extent (Guntas)", in_list_view=1, columns=1, precision=2),
        field("classification", "Select", "Classification",
              options="\nAgricultural\nNon-Agricultural\nWaste Land",
              in_list_view=1, columns=1),
        field("patta_number", "Data", "Patta Number"),
        field("revenue_sketch_available", "Check", "Revenue Sketch Available", in_list_view=1, columns=1),
    ]
    create_doctype("Survey Detail", doc)


def create_land_master():
    print("\n[Stage 2] Creating Land Master (Submittable)...")
    doc = base_doctype(
        "Land Master",
        autoname="naming_series:",
        naming_rule="By \"Naming Series\" field",
        is_submittable=1,
        track_changes=1,
        allow_rename=0,
        description="Single source of truth for every land parcel in the organization's bank"
    )

    fields = []

    # --- Tab: Details ---
    fields.append(tab_break("details_tab", "Details"))

    # Section: Basic Identity
    fields.append(section_break("sb_basic_identity", "Basic Identity"))
    fields.append(field("naming_series", "Select", "Naming Series",
                        options="LAND-.YYYY.-.####", reqd=1, default="LAND-.YYYY.-.####",
                        set_only_once=1, no_copy=1))
    fields.append(field("land_name", "Data", "Land Name", reqd=1, in_list_view=1, in_standard_filter=1))
    fields.append(field("total_extent_acres", "Float", "Total Extent (Acres)", reqd=1, precision=4, in_list_view=1))
    fields.append(field("total_extent_guntas", "Float", "Total Extent (Guntas)", precision=2))
    fields.append(field("total_extent_display", "Data", "Total Extent", read_only=1,
                        description="Combined display of acres and guntas"))
    fields.append(column_break("cb_basic_1"))
    fields.append(field("facing", "Select", "Facing",
                        options="\nNorth\nEast\nWest\nSouth\nNorth-East\nNorth-West\nSouth-East\nSouth-West"))
    fields.append(field("land_nature", "Select", "Land Nature", reqd=1, in_standard_filter=1,
                        options="\nPatta\nAssigned Land\nGovernment Land\nCeiling Land\nInam Land\nForest Land\nWakf Land"))
    fields.append(field("current_status", "Select", "Current Status", reqd=1, in_list_view=1, in_standard_filter=1,
                        default="Available",
                        options="Available\nUnder Litigation\nAcquired\nUnder Approval\nApproved for Development"))
    fields.append(field("risk_flag", "Check", "Risk Flag", read_only=1, in_list_view=1,
                        description="Auto-set when litigation or missing critical documents are detected"))

    # Section: Location
    fields.append(section_break("sb_location", "Location"))
    fields.append(field("village", "Data", "Village"))
    fields.append(field("mandal", "Link", "Mandal", reqd=1, options="Mandal Master",
                        in_list_view=1, in_standard_filter=1))
    fields.append(field("district", "Link", "District", options="District Master",
                        read_only=1, fetch_from="mandal.district", in_standard_filter=1))
    fields.append(field("state", "Data", "State", default="Telangana", read_only=1))
    fields.append(column_break("cb_location_1"))
    fields.append(field("pin_code", "Data", "Pin Code"))
    fields.append(field("latitude", "Float", "Latitude", precision=8))
    fields.append(field("longitude", "Float", "Longitude", precision=8))
    fields.append(field("google_map_link", "Data", "Map Link", read_only=1,
                        description="Auto-generated from coordinates"))

    # Section: Map Preview (using Frappe Geolocation)
    fields.append(section_break("sb_map", "Map Preview", collapsible=1))
    fields.append(field("location", "Geolocation", "Location on Map",
                        description="Use Frappe's built-in Geolocation field for map display"))

    # --- Tab: Survey Details ---
    fields.append(tab_break("survey_tab", "Survey Details"))
    fields.append(field("survey_details", "Table", "Survey Details", options="Survey Detail"))

    # --- Tab: Compliance ---
    fields.append(tab_break("compliance_tab", "Compliance"))
    fields.append(field("land_compliance", "Table", "Land Compliance", options="Land Compliance"))

    # --- Tab: Documents ---
    fields.append(tab_break("documents_tab", "Documents"))
    fields.append(field("encumbrance_documents", "Table", "Encumbrance & Documents",
                        options="Encumbrance Document"))

    # --- Tab: Notes ---
    fields.append(tab_break("notes_tab", "Notes"))
    fields.append(field("internal_notes", "Text Editor", "Internal Notes",
                        description="Legal team remarks, notes, and communication history"))

    # Amended From (required for submittable doctypes)
    fields.append(section_break("sb_amended"))
    fields.append(field("amended_from", "Link", "Amended From",
                        options="Land Master", read_only=1, no_copy=1, print_hide=1))

    doc["fields"] = fields
    doc["permissions"] = [
        perm("System Manager", create=1, write=1, delete=1, submit=1, cancel=1, amend=1,
             email=1, export=1, print_=1, report=1, share=1),
        perm("Land Manager", create=1, write=1),
        perm("Legal Team", write=1, submit=1),
        perm("Survey Team", write=1),
        perm("Project Manager"),
        perm("Approval Liaison Officer"),
        perm("Management", write=1, submit=1, cancel=1, amend=1),
    ]
    doc["search_fields"] = "land_name, village, mandal, district, current_status"
    doc["title_field"] = "land_name"
    doc["show_title_field_in_link"] = 1
    doc["image_field"] = ""
    doc["timeline_field"] = ""

    # Controller
    controller = '''# Copyright (c) 2026, surendhranath and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
import math


class LandMaster(Document):
    def validate(self):
        self.validate_extent()
        self.validate_survey_extents()
        self.compute_total_extent_display()
        self.compute_development_eligibility()
        self.check_document_completeness()
        self.update_google_map_link()
        self.update_geolocation()

    def validate_extent(self):
        """Extent cannot be zero."""
        if not self.total_extent_acres or self.total_extent_acres <= 0:
            frappe.throw(_("Total Extent (Acres) must be greater than zero."))

    def validate_survey_extents(self):
        """Warn if sum of survey extents exceeds total extent."""
        if not self.survey_details:
            return
        total_survey_acres = sum(
            (row.extent_acres or 0) for row in self.survey_details
        )
        if total_survey_acres > (self.total_extent_acres or 0):
            frappe.msgprint(
                _("Warning: Sum of survey extents ({0} acres) exceeds "
                  "total declared extent ({1} acres).").format(
                    total_survey_acres, self.total_extent_acres
                ),
                indicator="orange",
                title=_("Survey Extent Mismatch")
            )

    def compute_total_extent_display(self):
        """Compute combined acres + guntas display."""
        acres = self.total_extent_acres or 0
        guntas = self.total_extent_guntas or 0
        if guntas:
            self.total_extent_display = f"{acres} Acres {guntas} Guntas"
        else:
            self.total_extent_display = f"{acres} Acres"

    def compute_development_eligibility(self):
        """Auto-compute development eligibility from compliance data."""
        if not self.land_compliance:
            return

        for row in self.land_compliance:
            ineligible_reasons = []
            conditional_reasons = []

            # Absolute blocks
            if row.go_111_area:
                ineligible_reasons.append("Land falls under GO 111 catchment area")
            if row.defense_zone:
                ineligible_reasons.append("Land is in a Defense Zone (no-construction zone)")
            if self.land_nature == "Forest Land":
                ineligible_reasons.append("Forest Land cannot be developed")
            if row.airport_funnel_zone and (row.airport_distance_km or 0) < 20:
                ineligible_reasons.append(
                    f"Airport funnel zone — distance {row.airport_distance_km} km (< 20 km)")

            # Conditional blocks
            if row.water_body_nearby:
                conditional_reasons.append("Water body nearby — buffer review required")
            if row.lake_buffer_zone_ftl:
                conditional_reasons.append("Lake Buffer Zone (FTL) — setback applies")
            if row.ht_line_buffer and (row.ht_line_distance_metres or 0) < 15:
                conditional_reasons.append(
                    f"HT Line within {row.ht_line_distance_metres}m (< 15m)")
            if row.master_plan_road_affected:
                conditional_reasons.append("Master Plan road widening setback applies")

            if ineligible_reasons:
                row.development_eligible = "No"
                row.eligibility_remarks = "; ".join(ineligible_reasons)
            elif conditional_reasons:
                row.development_eligible = "Conditional"
                row.eligibility_remarks = "; ".join(conditional_reasons)
            else:
                row.development_eligible = "Yes"
                row.eligibility_remarks = "All compliance checks passed"

    def check_document_completeness(self):
        """Auto-set risk flag if critical documents are missing."""
        if not self.encumbrance_documents:
            self.risk_flag = 1
            return

        doc_types_present = set()
        for row in self.encumbrance_documents:
            if row.document_type:
                doc_types_present.add(row.document_type)

        required_types = {"EC", "Sale Deed", "Pahani", "FMB Sketch"}
        missing = required_types - doc_types_present

        if missing:
            self.risk_flag = 1
        elif self.current_status == "Under Litigation":
            self.risk_flag = 1
        else:
            self.risk_flag = 0

    def update_google_map_link(self):
        """Generate Google Maps link from coordinates."""
        if self.latitude and self.longitude:
            self.google_map_link = (
                f"https://www.google.com/maps?q={self.latitude},{self.longitude}"
            )
        else:
            self.google_map_link = ""

    def update_geolocation(self):
        """Update the Frappe Geolocation field from lat/lng."""
        if self.latitude and self.longitude and not self.location:
            import json
            self.location = json.dumps({
                "type": "FeatureCollection",
                "features": [{
                    "type": "Feature",
                    "properties": {"point_type": "circle", "radius": 100},
                    "geometry": {
                        "type": "Point",
                        "coordinates": [self.longitude, self.latitude]
                    }
                }]
            })
'''

    # Client Script
    js_code = '''// Copyright (c) 2026, surendhranath and contributors
// For license information, please see license.txt

frappe.ui.form.on("Land Master", {
    refresh(frm) {
        // Add custom buttons
        if (!frm.is_new() && frm.doc.docstatus === 0) {
            frm.add_custom_button(__("View on Map"), function() {
                if (frm.doc.google_map_link) {
                    window.open(frm.doc.google_map_link, "_blank");
                } else {
                    frappe.msgprint(__("Please enter Latitude and Longitude first."));
                }
            }, __("Actions"));
        }

        // Show risk flag indicator
        if (frm.doc.risk_flag) {
            frm.dashboard.set_headline(
                \'<span class="indicator-pill red">⚠ Risk Flag Active — Missing critical documents or under litigation</span>\'
            );
        }
    },

    latitude(frm) {
        update_map_link(frm);
    },

    longitude(frm) {
        update_map_link(frm);
    },

    total_extent_acres(frm) {
        compute_extent_display(frm);
    },

    total_extent_guntas(frm) {
        compute_extent_display(frm);
    },

    mandal(frm) {
        // District is auto-fetched via fetch_from, but we trigger refresh
        if (frm.doc.mandal) {
            frm.trigger("district");
        }
    }
});

function update_map_link(frm) {
    if (frm.doc.latitude && frm.doc.longitude) {
        var link = "https://www.google.com/maps?q=" + frm.doc.latitude + "," + frm.doc.longitude;
        frm.set_value("google_map_link", link);

        // Update Geolocation field
        var geojson = {
            type: "FeatureCollection",
            features: [{
                type: "Feature",
                properties: { point_type: "circle", radius: 100 },
                geometry: {
                    type: "Point",
                    coordinates: [frm.doc.longitude, frm.doc.latitude]
                }
            }]
        };
        frm.set_value("location", JSON.stringify(geojson));
    }
}

function compute_extent_display(frm) {
    var acres = frm.doc.total_extent_acres || 0;
    var guntas = frm.doc.total_extent_guntas || 0;
    if (guntas) {
        frm.set_value("total_extent_display", acres + " Acres " + guntas + " Guntas");
    } else {
        frm.set_value("total_extent_display", acres + " Acres");
    }
}
'''

    create_doctype("Land Master", doc, controller, js_code)


# =====================================================================
# STAGE 3: Land Compliance & Documents
# =====================================================================

def create_land_compliance():
    print("\n[Stage 3] Creating Land Compliance (Child Table)...")
    doc = base_doctype(
        "Land Compliance",
        istable=1,
        description="Regulatory and physical compliance constraints for a land parcel"
    )

    fields = []

    # Regulatory Zoning
    fields.append(section_break("sb_regulatory", "Regulatory Zoning"))
    fields.append(field("zoning_type", "Select", "Zoning Type",
                        options="\nResidential\nCommercial\nMixed Use\nIndustrial\nGreen Zone\nNo Development Zone\nSpecial Development Zone",
                        in_list_view=1, columns=2))
    fields.append(field("master_plan_road_affected", "Check", "Master Plan Road Affected"))
    fields.append(field("road_width_metres", "Float", "Road Width (Metres)", precision=2))
    fields.append(column_break("cb_reg_1"))
    fields.append(field("permissible_far", "Float", "Permissible FAR", precision=2))
    fields.append(field("permissible_ground_coverage", "Float", "Permissible Ground Coverage (%)", precision=2))

    # Physical & Buffer Zone Constraints
    fields.append(section_break("sb_buffer", "Physical & Buffer Zone Constraints"))
    fields.append(field("water_body_nearby", "Check", "Water Body Nearby"))
    fields.append(field("water_body_distance_metres", "Float", "Water Body Distance (Metres)",
                        depends_on="water_body_nearby", precision=2))
    fields.append(field("lake_buffer_zone_ftl", "Check", "Lake Buffer Zone (FTL)",
                        description="Full Tank Level buffer — no construction within FTL boundary"))
    fields.append(field("fsl_level", "Float", "FSL Level",
                        description="Full Supply Level — relevant for HMDA GO 111 areas", precision=2))
    fields.append(field("nala_nearby", "Check", "Nala Nearby",
                        description="Stormwater drain — setback rules apply"))
    fields.append(field("nala_width_classification", "Select", "Nala Width Classification",
                        options="\nMinor\nMajor\nMaster Nala",
                        depends_on="nala_nearby"))
    fields.append(column_break("cb_buffer_1"))
    fields.append(field("railway_buffer", "Check", "Railway Buffer"))
    fields.append(field("railway_distance_metres", "Float", "Railway Distance (Metres)",
                        depends_on="railway_buffer", precision=2))
    fields.append(field("ht_line_buffer", "Check", "High Tension Line Buffer"))
    fields.append(field("ht_line_distance_metres", "Float", "HT Line Distance (Metres)",
                        depends_on="ht_line_buffer", precision=2,
                        description="CEA rules: 3m–15m clearance depending on voltage"))
    fields.append(field("gas_pipeline_buffer", "Check", "Gas Pipeline Buffer",
                        description="PNGRB regulations apply"))
    fields.append(field("defense_zone", "Check", "Defense Zone",
                        description="Ministry of Defence no-construction zone"))
    fields.append(field("airport_funnel_zone", "Check", "Airport Funnel Zone",
                        description="DGCA / AAI height restrictions"))
    fields.append(field("airport_distance_km", "Float", "Airport Distance (Km)",
                        depends_on="airport_funnel_zone", precision=2))

    # Hyderabad-Specific Restrictions
    fields.append(section_break("sb_hyderabad", "Hyderabad-Specific Restrictions"))
    fields.append(field("go_111_area", "Check", "GO 111 Area",
                        description="Catchment areas of Osman Sagar & Himayat Sagar; development strictly prohibited"))
    fields.append(field("hmda_green_zone", "Check", "HMDA Green Zone",
                        description="No construction; only afforestation permitted"))
    fields.append(column_break("cb_hyd_1"))
    fields.append(field("ghmc_limits", "Check", "GHMC Limits",
                        description="Determines which approval authority governs the project"))
    fields.append(field("hmda_jurisdiction", "Check", "HMDA Jurisdiction",
                        description="Outside GHMC but within HMDA metropolitan development area"))

    # Development Eligibility (Auto-Computed)
    fields.append(section_break("sb_eligibility", "Development Eligibility"))
    fields.append(field("development_eligible", "Select", "Development Eligible",
                        options="\nYes\nNo\nConditional",
                        read_only=1, in_list_view=1, columns=2,
                        description="Auto-computed based on compliance parameters"))
    fields.append(column_break("cb_elig_1"))
    fields.append(field("eligibility_remarks", "Small Text", "Eligibility Remarks",
                        read_only=1,
                        description="Auto-populated with reason for Conditional or No status"))

    doc["fields"] = fields
    create_doctype("Land Compliance", doc)


def create_encumbrance_document():
    print("\n[Stage 3] Creating Encumbrance Document (Child Table)...")
    doc = base_doctype(
        "Encumbrance Document",
        istable=1,
        description="Document records for land parcels including EC, Sale Deed, Pahani etc."
    )

    fields = []
    fields.append(field("document_type", "Select", "Document Type", reqd=1, in_list_view=1, columns=2,
                        options="\nEC\nSale Deed\nLink Document\nGift Deed\nPartition Deed\nPahani\nAdangal\n1-B Register\nFMB Sketch\nTippan\nRevenue Sketch\nCourt Order\nPower of Attorney\nOther"))
    fields.append(field("document_number", "Data", "Document Number", in_list_view=1, columns=1))
    fields.append(field("document_date", "Date", "Document Date", in_list_view=1, columns=1))
    fields.append(field("period_from", "Date", "Period From",
                        description="For EC: start of encumbrance period"))
    fields.append(field("period_to", "Date", "Period To",
                        description="For EC: end of encumbrance period"))
    fields.append(field("issued_by", "Data", "Issued By",
                        description="Authority that issued the document"))
    fields.append(field("file_attachment", "Attach", "File Attachment",
                        description="Upload the scanned document"))
    fields.append(section_break("sb_ocr", "OCR Processing"))
    fields.append(field("ocr_status", "Select", "OCR Status",
                        options="\nNot Processed\nProcessing\nExtracted\nVerified",
                        default="Not Processed", in_list_view=1, columns=1,
                        description="Set to Verified after manual review"))
    fields.append(field("ocr_extracted_data", "Text", "OCR Extracted Data",
                        read_only=1,
                        description="JSON data extracted by OCR engine"))
    fields.append(column_break("cb_ocr_1"))
    fields.append(field("verified_by", "Link", "Verified By", options="User",
                        description="Set by legal team after review"))
    fields.append(field("verification_date", "Date", "Verification Date",
                        read_only=1,
                        description="Auto-set when Verified By is saved"))

    doc["fields"] = fields
    create_doctype("Encumbrance Document", doc)


# =====================================================================
# MAIN
# =====================================================================

def main():
    print("=" * 60)
    print("LB-PAMS DocType Generator — Stages 1-3")
    print("=" * 60)

    # Ensure base doctype directory exists
    ensure_dir(BASE_DIR)

    # Stage 1
    create_district_master()
    create_mandal_master()
    create_authority_mapping()

    # Stage 2
    create_survey_detail()
    create_land_master()

    # Stage 3
    create_land_compliance()
    create_encumbrance_document()

    print("\n" + "=" * 60)
    print("All DocType files created successfully!")
    print("Next steps:")
    print("  1. Update hooks.py")
    print("  2. Run: bench --site <sitename> migrate")
    print("=" * 60)


if __name__ == "__main__":
    main()
