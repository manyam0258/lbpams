// Copyright (c) 2026, surendhranath and contributors
// For license information, please see license.txt

frappe.ui.form.on("Land Master", {
    setup(frm) {
        // ──── Cascading Filters: State → District → Mandal ────
        frm.set_query("district", function() {
            if (frm.doc.state) {
                return { filters: { state: frm.doc.state } };
            }
        });

        frm.set_query("mandal", function() {
            if (frm.doc.district) {
                return { filters: { district: frm.doc.district } };
            }
        });
    },

    refresh(frm) {
        // ──── Custom Buttons ────
        if (!frm.is_new() && frm.doc.docstatus === 0) {
            frm.add_custom_button(__("View on Map"), function() {
                if (frm.doc.google_map_link) {
                    window.open(frm.doc.google_map_link, "_blank");
                } else {
                    frappe.msgprint(__("Please enter Latitude and Longitude first."));
                }
            }, __("Actions"));
        }

        // ──── Risk Flag Indicator ────
        if (frm.doc.risk_flag) {
            frm.dashboard.set_headline(
                '<span class="indicator-pill red">⚠ Risk Flag Active — Missing critical documents, litigation, or ownership chain issues</span>'
            );
        }

        // ──── Title Status Indicator ────
        if (frm.doc.title_status && frm.doc.title_status !== "Not Assessed") {
            var status_colors = {
                "Clear Title": "green",
                "Gap in Chain": "orange",
                "Overlapping Ownership": "red",
                "Disputed": "red",
                "Under Verification": "blue"
            };
            var color = status_colors[frm.doc.title_status] || "grey";
            frm.dashboard.add_comment(
                __("Title Status: {0}", ['<span class="indicator-pill ' + color + '">' + frm.doc.title_status + '</span>']),
                "blue", true
            );
        }

        // ──── Color-code Ownership Chain Rows ────
        render_ownership_chain_indicators(frm);
    },

    // ──── Location Hierarchy: State → District → Mandal ────
    state(frm) {
        if (frm.doc.district) {
            frappe.db.get_value("District Master", frm.doc.district, "state", function(r) {
                if (r && r.state !== frm.doc.state) {
                    frm.set_value("district", "");
                    frm.set_value("mandal", "");
                }
            });
        }
    },

    district(frm) {
        if (frm.doc.mandal && frm.doc.district) {
            frappe.db.get_value("Mandal Master", frm.doc.mandal, "district", function(r) {
                if (r && r.district !== frm.doc.district) {
                    frm.set_value("mandal", "");
                }
            });
        } else if (!frm.doc.district) {
            frm.set_value("mandal", "");
        }
    },

    mandal(frm) {
        if (frm.doc.mandal) {
            frappe.db.get_value("Mandal Master", frm.doc.mandal, "district", function(r) {
                if (r && r.district) {
                    frm.set_value("district", r.district);
                    frappe.db.get_value("District Master", r.district, "state", function(s) {
                        if (s && s.state) {
                            frm.set_value("state", s.state);
                        }
                    });
                }
            });
        }
    },

    // ──── Map & Extent ────
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
    }
});

// ──── Encumbrance Document (Land Document) Events ────
frappe.ui.form.on("Encumbrance Document", {
    document_category(frm, cdt, cdn) {
        // Filter document_type options based on selected category
        var row = locals[cdt][cdn];
        var category_types = {
            "Title Document": [
                "Sale Deed", "Gift Deed", "Partition Deed", "Release Deed",
                "Will / Succession Certificate", "Court Decree",
                "Government Allotment Order", "Power of Attorney", "Agreement of Sale"
            ],
            "Revenue Record": [
                "Pahani (ROR)", "Adangal", "1-B Register", "FMB Sketch",
                "Tippan", "Revenue Sketch", "Pattadar Passbook", "Village Map"
            ],
            "Encumbrance Record": [
                "EC", "Non-Encumbrance Certificate"
            ],
            "Compliance Document": [
                "Land Conversion Order", "NOC", "Survey / Demarcation Report",
                "Advocate Title Certificate"
            ],
            "Legal Opinion": [
                "Advocate Title Certificate"
            ],
            "Other": [
                "Link Document", "Other"
            ]
        };

        if (row.document_category && category_types[row.document_category]) {
            // Clear the current document_type if it doesn't belong to the new category
            var valid_types = category_types[row.document_category];
            if (row.document_type && valid_types.indexOf(row.document_type) === -1) {
                frappe.model.set_value(cdt, cdn, "document_type", "");
            }
        }
    },

    verified_by(frm, cdt, cdn) {
        // Auto-set verification date and status when verifier is assigned
        var row = locals[cdt][cdn];
        if (row.verified_by) {
            frappe.model.set_value(cdt, cdn, "verification_date", frappe.datetime.get_today());
            if (!row.verification_status || row.verification_status === "Unverified") {
                frappe.model.set_value(cdt, cdn, "verification_status", "Verified");
            }
        }
    }
});

// ──── Ownership Record Events ────
frappe.ui.form.on("Ownership Record", {
    from_date(frm, cdt, cdn) {
        check_ownership_overlap(frm, cdt, cdn);
    },

    to_date(frm, cdt, cdn) {
        check_ownership_overlap(frm, cdt, cdn);
    },

    ownership_records_remove(frm) {
        // Re-validate chain when a row is removed
        render_ownership_chain_indicators(frm);
    }
});

// ═══════════════════════════════════════════════════════
// Helper Functions
// ═══════════════════════════════════════════════════════

function update_map_link(frm) {
    if (frm.doc.latitude && frm.doc.longitude) {
        var link = "https://www.google.com/maps?q=" + frm.doc.latitude + "," + frm.doc.longitude;
        frm.set_value("google_map_link", link);

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

function check_ownership_overlap(frm, cdt, cdn) {
    /**
     * Client-side date overlap detection for ownership records.
     * Shows inline warnings for gaps (>6 months) and overlaps.
     */
    var current_row = locals[cdt][cdn];
    if (!current_row.from_date) return;

    var rows = frm.doc.ownership_records || [];
    var warnings = [];

    for (var i = 0; i < rows.length; i++) {
        var row = rows[i];
        if (row.name === current_row.name) continue;

        // Check overlap: current row starts before a previous row ends
        if (row.to_date && current_row.from_date) {
            var row_end = frappe.datetime.str_to_obj(row.to_date);
            var curr_start = frappe.datetime.str_to_obj(current_row.from_date);

            if (row.from_date) {
                var row_start = frappe.datetime.str_to_obj(row.from_date);

                // Overlap: current starts before previous ends AND current starts after previous starts
                if (curr_start < row_end && curr_start >= row_start) {
                    warnings.push(
                        __("⚠ Overlap detected with {0} (owner from {1} to {2})",
                            [row.owner_name || "Row " + row.idx, row.from_date, row.to_date])
                    );
                }
            }
        }

        // Check gap: current row starts more than 6 months after previous row ended
        if (row.to_date && current_row.from_date && !row.name === current_row.name) {
            var gap_days = frappe.datetime.get_diff(current_row.from_date, row.to_date);
            if (gap_days > 180) {
                warnings.push(
                    __("⚠ Gap of {0} days detected after {1} (ended {2})",
                        [gap_days, row.owner_name || "Row " + row.idx, row.to_date])
                );
            }
        }
    }

    if (warnings.length > 0) {
        frappe.msgprint({
            title: __("Ownership Chain Warning"),
            message: warnings.join("<br>"),
            indicator: "orange"
        });
    }
}

function render_ownership_chain_indicators(frm) {
    /**
     * Color-code ownership chain rows based on chain_status.
     * 🟢 Clear — continuous chain
     * 🟡 Gap Before — gap < 6 months or under review
     * 🔴 Overlap / Disputed — needs attention
     */
    if (!frm.doc.ownership_records || !frm.fields_dict.ownership_records) return;

    setTimeout(function() {
        var grid = frm.fields_dict.ownership_records.grid;
        if (!grid || !grid.grid_rows) return;

        grid.grid_rows.forEach(function(grid_row) {
            if (!grid_row.doc) return;

            var status = grid_row.doc.chain_status;
            var $row = $(grid_row.row);

            // Remove previous styling
            $row.css("border-left", "");

            if (status === "Clear") {
                $row.css("border-left", "4px solid var(--green-500, #28a745)");
            } else if (status === "Gap Before") {
                $row.css("border-left", "4px solid var(--orange-500, #ffc107)");
            } else if (status === "Overlap" || status === "Disputed") {
                $row.css("border-left", "4px solid var(--red-500, #dc3545)");
            }
        });
    }, 300);
}
