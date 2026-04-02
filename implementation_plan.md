# LB-PAMS Implementation Plan

## Overview

Build the **Land Bank & Project Approval Management System** as a Frappe app (`lbpams`) layered on ERPNext. The app is currently a blank scaffold — no DocTypes exist yet. We will follow the 13-stage development sequence from the knowledge base.

## Current State

- App `lbpams` is scaffolded with module `LBPAMS` registered
- `hooks.py` is default boilerplate — no custom hooks configured
- No DocTypes, workflows, reports, dashboards, or print formats exist
- The app needs to be built from scratch per the knowledge base specification

## Proposed Changes — Staged Approach

We will implement **Stage 1 through Stage 9** (core functionality) first, then follow with Stages 10-13 (reports, dashboards, print formats, workspace). Each stage builds on the previous one.

---

### Stage 1 — Foundation Masters

> [!IMPORTANT]
> These must be created first as all other DocTypes link to them.

#### [NEW] District Master DocType
- Simple DocType (not submittable)
- Fields: `district_name` (Data, mandatory, unique)
- Naming: by `district_name`
- Pre-populate with all Telangana districts

#### [NEW] Mandal Master DocType
- Simple DocType
- Fields: `mandal_name` (Data, mandatory), `district` (Link → District Master, mandatory)
- Naming: by `mandal_name`

#### [NEW] Authority Mapping DocType
- Simple DocType
- Fields: `mandal` (Link → Mandal Master, mandatory), `authority` (Select: GHMC/HMDA/DTCP, mandatory)
- Used for auto-detecting approval authority from land location

---

### Stage 2 — Land Master Core

#### [NEW] Survey Detail (Child DocType)
- Fields: survey_number, subdivision_number, extent_acres, extent_guntas, classification (Select), patta_number, revenue_sketch_available (Check)
- Parent: Land Master

#### [NEW] Land Master (Submittable DocType)
- Naming Series: `LAND-.YYYY.-.####`
- **Basic Identity**: land_name, total_extent_acres, total_extent_guntas, facing (Select), land_nature (Select), current_status (Select), risk_flag (Check, read-only)
- **Location**: village, mandal (Link), district (Link, auto-fetched), state (Select, default Telangana), pin_code, latitude, longitude, google_map_link, map_preview (HTML)
- **Survey Details**: Table → Survey Detail
- **Internal Notes**: Text Editor
- Client Script: Google Maps preview from lat/lng

---

### Stage 3 — Land Compliance & Documents

#### [NEW] Land Compliance (Child DocType)
- Parent: Land Master
- Regulatory zoning fields, buffer zone fields, Hyderabad-specific restrictions, auto-computed development eligibility

#### [NEW] Encumbrance Document (Child DocType)
- Parent: Land Master
- Document tracking with OCR status fields, verification tracking

#### [MODIFY] Land Master Controller
- Add `validate` hook for:
  - Development eligibility auto-computation
  - Risk flag auto-setting based on missing documents
  - Survey extent validation

---

### Stage 4 — Ownership Chain

#### [NEW] Ownership Record (Child DocType)
- Parent: Land Master
- Full ownership chain tracking with dates, registration details, consideration amounts

#### Client Script for Land Master
- Date overlap warning for ownership records

---

### Stage 5 — Land Workflow & Notifications

#### [NEW] Land Master Approval Workflow
- 7 states: Draft → Under Verification → Legally Verified → Approved for Development (+ Under Litigation, On Hold, Rejected)
- Transition conditions for development eligibility check
- Role-based transitions

#### Notification Configurations
- Land Litigation Flag notification
- Weekly Missing Documents (scheduled job)

---

### Stage 6 — Project Master Core

#### [NEW] NOC Tracker (Child DocType)
- Parent: Project Master
- 10 NOC types with status tracking, validity dates, document attachments

#### [NEW] Approval Stage (Child DocType)
- Parent: Project Master (also used in OC Application)
- Stage tracking with assignment, dates, status, overdue indicators

#### [NEW] Construction Milestone (Child DocType)
- Parent: Project Master
- Milestone tracking with planned/actual dates, completion %, inspection tracking

#### [NEW] Project Master (Submittable DocType)
- Naming Series: `PROJ-.YYYY.-.####`
- Links to approved Land Master
- Authority auto-detection from land location
- Pre-approval checklist fields
- Child tables: NOC Tracker, Approval Stage, Construction Milestone

---

### Stage 7 — Fee Letter & Conditions

#### [NEW] Fee Condition (Child DocType)
- Parent: Fee Letter
- Condition tracking with amounts, payment status, receipts

#### [NEW] Fee Letter (Submittable DocType)
- Naming Series: `FL-.YYYY.-.####`
- Links to Project Master
- Auto-sum total amount, auto-update payment status
- Due date auto-calculation

---

### Stage 8 — RERA, Environmental & OC

#### [NEW] RERA Process (Regular DocType)
- Naming Series: `RERA-.YYYY.-.####`
- Application tracking, deficiency management, certificate handling

#### [NEW] Environmental Compliance (Regular DocType)
- CFE/CFO tracking, EIA management

#### [NEW] OC Application (Submittable DocType)
- Naming Series: `OCA-.YYYY.-.####`
- OC approval stages, required documents checklist, handover checklist
- Mortgage unit release trigger on OC issuance

---

### Stage 9 — Project Workflow

#### [NEW] Project Master Approval Workflow
- 10+ states covering the full project lifecycle
- Gate transitions for NOC completeness, fee payment, milestone completion

---

### Stage 10 — Reports & Dashboards (Follow-up)

6 reports (Script Reports and Query Reports) + 2 Dashboards

### Stage 11 — Print Formats (Follow-up)

4 Jinja2 Print Formats

### Stage 12 — Workspace & Roles (Follow-up)

Workspace configuration, 6 custom roles, DocPerm matrix

### Stage 13 — UAT & Data Migration (Follow-up)

---

## Summary of DocTypes to Create

| # | DocType | Type | Parent |
|---|---------|------|--------|
| 1 | District Master | Regular | — |
| 2 | Mandal Master | Regular | — |
| 3 | Authority Mapping | Regular | — |
| 4 | Survey Detail | Child | Land Master |
| 5 | Land Compliance | Child | Land Master |
| 6 | Encumbrance Document | Child | Land Master |
| 7 | Ownership Record | Child | Land Master |
| 8 | Land Master | Submittable | — |
| 9 | NOC Tracker | Child | Project Master |
| 10 | Approval Stage | Child | Project Master |
| 11 | Construction Milestone | Child | Project Master |
| 12 | Project Master | Submittable | — |
| 13 | Fee Condition | Child | Fee Letter |
| 14 | Fee Letter | Submittable | — |
| 15 | RERA Process | Regular | — |
| 16 | Environmental Compliance | Regular | — |
| 17 | OC Application | Submittable | — |

**Total: 17 DocTypes** (4 submittable, 6 regular, 7 child tables)

## Implementation Method

We will use **`bench new-doctype`** and direct JSON file creation for DocType definitions, with Python controllers for server-side logic and JS files for client scripts. All work will be done within the `lbpams/lbpams/doctype/` directory structure.

> [!WARNING]
> This is a large development effort. We'll create all Stage 1-9 DocTypes with their controllers, update `hooks.py`, and run `bench migrate` to create the database tables. Stages 10-13 will be follow-up work.

## Verification Plan

### Automated Tests
- `bench migrate` must complete without errors
- Each DocType must be createable via the Frappe desk
- Validation hooks must fire correctly (test with `bench console`)

### Manual Verification
- Create test Land Master records through the Frappe desk
- Test workflow transitions
- Verify link filters (Project Master should only link to approved Land Master records)
- Test parent-child relationships

## Open Questions

> [!IMPORTANT]
> 1. **Should we start with Stage 1-3 first** and verify before proceeding, or build all stages at once?
> 2. **Google Maps API key** — do you have one, or should we skip the map preview for now?
> 3. **OCR integration (Tesseract)** — should we implement the OCR module now or defer it?
> 4. **Telangana data** — do you have a list of all Telangana districts/mandals for pre-population, or should we research and create it?
> 5. **ERPNext dependency** — should we add `erpnext` to `required_apps` in hooks.py?
