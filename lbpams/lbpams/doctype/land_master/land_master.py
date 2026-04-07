# Copyright (c) 2026, surendhranath and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, today, date_diff
import math


class LandMaster(Document):
    def validate(self):
        self.auto_fetch_location_hierarchy()
        self.validate_extent()
        self.validate_survey_extents()
        self.compute_total_extent_display()
        self.compute_development_eligibility()
        self.check_document_completeness()
        self.validate_ownership_chain()
        self.update_verification_dates()
        self.validate_document_validity()
        self.update_google_map_link()
        self.update_geolocation()

    # ──── Location Hierarchy ────

    def auto_fetch_location_hierarchy(self):
        """Ensure State→District→Mandal hierarchy is correct."""
        if self.mandal:
            mandal_district = frappe.db.get_value("Mandal Master", self.mandal, "district")
            if mandal_district:
                self.district = mandal_district
                district_state = frappe.db.get_value("District Master", mandal_district, "state")
                if district_state:
                    self.state = district_state

    # ──── Extent Validations ────

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

    # ──── Compliance ────

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

    # ──── Document Completeness ────

    def check_document_completeness(self):
        """Auto-set risk flag if critical documents are missing."""
        if not self.encumbrance_documents:
            self.risk_flag = 1
            return

        doc_types_present = set()
        for row in self.encumbrance_documents:
            if row.document_type:
                doc_types_present.add(row.document_type)

        # Critical documents that must be present for a clear title
        required_types = {"EC", "Sale Deed", "Pahani (ROR)", "FMB Sketch"}
        # Also accept the old "Pahani" value for backward compatibility
        if "Pahani" in doc_types_present:
            doc_types_present.add("Pahani (ROR)")

        missing = required_types - doc_types_present

        if missing:
            self.risk_flag = 1
        elif self.current_status == "Under Litigation":
            self.risk_flag = 1
        else:
            # Don't clear if ownership chain has issues (handled in validate_ownership_chain)
            if not getattr(self, '_ownership_risk', False):
                self.risk_flag = 0

    # ──── Ownership Chain Validation ────

    def validate_ownership_chain(self):
        """
        Validate the ownership chain for completeness and continuity.
        Sets title_status and chain_status on each row.

        A clear chain means:
        - Each owner's from_date is close to (within 6 months of) the previous owner's to_date
        - No overlapping ownership periods
        - No gaps > 6 months without explanation
        """
        if not self.ownership_records:
            self.title_status = "Not Assessed"
            return

        # Sort ownership records by from_date
        sorted_records = sorted(
            self.ownership_records,
            key=lambda r: getdate(r.from_date) if r.from_date else getdate("1900-01-01")
        )

        has_gaps = False
        has_overlaps = False
        has_disputed = False

        for i, row in enumerate(sorted_records):
            if not row.from_date:
                row.chain_status = "Gap Before"
                has_gaps = True
                continue

            if i == 0:
                # First owner — no previous record to check against
                row.chain_status = "Clear"
                continue

            prev_row = sorted_records[i - 1]

            if not prev_row.to_date:
                # Previous owner has no end date but there's a next owner — flag
                if prev_row.from_date and row.from_date:
                    # Previous owner should have ended before this one started
                    row.chain_status = "Overlap"
                    has_overlaps = True
                    continue

            if prev_row.to_date and row.from_date:
                prev_end = getdate(prev_row.to_date)
                curr_start = getdate(row.from_date)
                gap_days = date_diff(curr_start, prev_end)

                if gap_days < 0:
                    # Overlap: current owner started before previous owner ended
                    row.chain_status = "Overlap"
                    has_overlaps = True
                elif gap_days > 180:
                    # Gap > 6 months
                    row.chain_status = "Gap Before"
                    has_gaps = True
                else:
                    row.chain_status = "Clear"
            else:
                row.chain_status = "Clear"

        # Check for any rows marked as Disputed
        for row in self.ownership_records:
            if row.chain_status == "Disputed":
                has_disputed = True

        # Set overall title status
        if has_disputed:
            self.title_status = "Disputed"
            self._ownership_risk = True
            self.risk_flag = 1
        elif has_overlaps:
            self.title_status = "Overlapping Ownership"
            self._ownership_risk = True
            self.risk_flag = 1
        elif has_gaps:
            self.title_status = "Gap in Chain"
            self._ownership_risk = True
            self.risk_flag = 1
            frappe.msgprint(
                _("Ownership chain has gaps exceeding 6 months. "
                  "Legal team should verify and update remarks."),
                indicator="orange",
                title=_("Ownership Chain Gap")
            )
        else:
            self.title_status = "Clear Title"
            self._ownership_risk = False

    # ──── Document Verification Helpers ────

    def update_verification_dates(self):
        """Auto-set verification_date when verified_by is set on document rows."""
        if not self.encumbrance_documents:
            return

        for row in self.encumbrance_documents:
            if row.verified_by and not row.verification_date:
                row.verification_date = today()
                if not row.verification_status or row.verification_status == "Unverified":
                    row.verification_status = "Verified"

    def validate_document_validity(self):
        """Warn if critical documents (EC, Pahani) have expired."""
        if not self.encumbrance_documents:
            return

        today_date = getdate(today())
        expired_docs = []

        for row in self.encumbrance_documents:
            if row.validity_date and row.document_type in ("EC", "Pahani (ROR)", "Pahani"):
                if getdate(row.validity_date) < today_date:
                    expired_docs.append(f"{row.document_type} (expired {row.validity_date})")

        if expired_docs:
            frappe.msgprint(
                _("The following documents have expired and should be renewed: {0}").format(
                    ", ".join(expired_docs)
                ),
                indicator="orange",
                title=_("Expired Documents")
            )

    # ──── Map & Geolocation ────

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
