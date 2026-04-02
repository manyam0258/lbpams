# Copyright (c) 2026, surendhranath and contributors
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
