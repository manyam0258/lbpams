// Copyright (c) 2026, surendhranath and contributors
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
                '<span class="indicator-pill red">⚠ Risk Flag Active — Missing critical documents or under litigation</span>'
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
