# Land Bank & Project Approval Management System (LB-PAMS)
## Complete Knowledge Base for Frappe / ERPNext Development

---

> **Purpose:** This document is the single reference for designing, building, and configuring the Land Bank & Project Approval Management System as a custom Frappe app layered on top of ERPNext. Every section maps directly to a Frappe or ERPNext concept. Developers should read this before writing a single line of code.

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Frappe App Architecture](#2-frappe-app-architecture)
3. [ERPNext Native Features to Leverage](#3-erpnext-native-features-to-leverage)
4. [Phase 1 — Land Bank Management](#4-phase-1--land-bank-management)
   - 4.1 Master Data Doctypes
   - 4.2 Land Compliance Intelligence
   - 4.3 Ownership & Title Chain
   - 4.4 Document Management & OCR
   - 4.5 Land Workflow
5. [Phase 2 — Project Approval & Execution](#5-phase-2--project-approval--execution)
   - 5.1 Project Master
   - 5.2 NOC Management
   - 5.3 Approval Workflow Chain
   - 5.4 Fee Letter & Conditions
6. [Phase 3 — RERA, Construction & OC](#6-phase-3--rera-construction--oc)
   - 6.1 RERA Process
   - 6.2 Environmental Compliance
   - 6.3 Construction Milestones
   - 6.4 OC Application & Handover
7. [Frappe Workflow Engine Design](#7-frappe-workflow-engine-design)
8. [Role & Permission Matrix](#8-role--permission-matrix)
9. [Notifications & Automation](#9-notifications--automation)
10. [Reports & Dashboards](#10-reports--dashboards)
11. [Print Formats](#11-print-formats)
12. [Workspace Configuration](#12-workspace-configuration)
13. [External Integrations](#13-external-integrations)
14. [Validations & Business Rules](#14-validations--business-rules)
15. [Development Sequence](#15-development-sequence)
16. [Edge Cases & Risk Flags](#16-edge-cases--risk-flags)

---

## 1. System Overview

### What This System Does

LB-PAMS is a **complete lifecycle management system** that takes a piece of land from initial identification all the way through legal verification, project planning, regulatory approvals, construction, and final handover to the project association.

The system answers the following questions at any point in time:

- What land parcels does the organization own or control, and what is the legal standing of each?
- Which lands are ready for development and which have compliance blockers?
- For each project, where exactly is it in the approval pipeline and who is responsible for the next action?
- What NOCs are pending, expiring, or missing?
- What conditions were imposed in the fee letter and have they been fulfilled?
- What is the RERA registration status and is it about to expire?
- Has the OC been received and have mortgage units been released?

### Two Phases, One Connected System

**Phase 1 — Land Bank** is about knowing what you own. It captures land parcels, their legal history, their compliance constraints, and their document trail. A land parcel in Phase 1 must be fully verified and approved before it can ever be used in Phase 2.

**Phase 2 — Project Approval** is about building on what you own. It takes an approved land parcel, attaches a project plan to it, tracks every regulatory approval required, manages the fee letter from the authority, monitors construction, handles RERA registration, and closes out with an Occupancy Certificate and handover.

### Design Philosophy

- **Use ERPNext native wherever possible.** The Workflow Engine, File Manager, ToDo, Notification system, Assignment module, Project module, Dashboard, and Report Builder all exist in ERPNext. Do not rebuild them.
- **Build custom Doctypes only for domain logic.** The custom app `land_project_mgmt` introduces Doctypes that ERPNext has no equivalent for — land parcels, survey details, approval stages, fee letters, and so on.
- **Every record has a traceable owner and a workflow state.** Nothing moves forward without an explicit transition. This creates an audit trail that management and legal teams can rely on.
- **Documents are first-class citizens.** Every Doctype that requires supporting documents exposes an attachment field and an explicit verification status. The OCR module assists but never replaces human verification.

---

## 2. Frappe App Architecture

### App Name and Module

The custom app is named `land_project_mgmt`. It is installed on the same Frappe bench as ERPNext and sits alongside it. The app defines its own module of the same name. All custom Doctypes, workflows, print formats, dashboards, reports, notifications, and workspace configurations live inside this app so that the system is fully portable between Frappe bench instances.

### Folder Structure Concepts

Inside the app, Frappe expects each Doctype to have its own folder containing a JSON definition file (the schema), a Python controller file (server-side logic), and a JavaScript client file (browser-side logic). The app also contains folders for workflows, print formats, dashboards, reports, notifications, and workspace definitions — all of which are JSON-based and version-controlled.

Child Doctypes are Doctypes that do not stand alone. They only exist as rows inside a parent Doctype's table field. They follow the same folder convention but are always linked to their parent via the `parent_doctype` field in their JSON definition.

### Relationship to ERPNext

The app references ERPNext Doctypes by linking to them where appropriate:

- **Project** (from ERPNext's Projects module) is linked to `Project Master` to enable task and milestone tracking.
- **User** is linked in assignment and role fields.
- **File** (Frappe's built-in file system) handles all document attachments.
- **Email Account** and **Notification** configurations in ERPNext power all alerts generated by this app.

---

## 3. ERPNext Native Features to Leverage

Understanding which ERPNext features to use — and how — is the most important architectural decision in this project. The following native features should be configured, not reimplemented.

### 3.1 Frappe Workflow Engine

**What it does:** Allows a Doctype to have named states (Draft, Under Review, Approved, etc.) and transitions between those states, each controlled by roles and optional conditions. When a document transitions, Frappe can automatically send a notification, create a ToDo, and log the change.

**How this system uses it:** Both `Land Master` and `Project Master` are submittable Doctypes with full workflow definitions. The workflow replaces any manual status management. States are defined in **Setup → Workflow**. The `workflow_state` field is automatically added to the Doctype by Frappe when a workflow is attached.

**Key design rule:** Never manage document states in Python code. Always use the Workflow Engine. This gives management a visual state machine they can modify without a developer.

### 3.2 Frappe Document Attachments

**What it does:** Every Doctype in Frappe natively supports file attachments via the `Attach` fieldtype or the standard attachment section at the bottom of every form. Files are stored in the Frappe file system (or S3 if configured) and linked to the parent document.

**How this system uses it:** Every document type — EC, Sale Deed, Pahani, NOC, Fee Letter scan, approved plan — is stored as an `Attach` field within the relevant child table row. This keeps documents physically tied to the record they belong to, with full version history via the document's timeline.

### 3.3 ToDo & Assignment Module

**What it does:** Frappe's `assign_to` utility creates a `ToDo` entry assigned to a specific user and links it to a document. The assigned user sees the task in their ToDo list and receives a notification. Assignments carry a due date and a description.

**How this system uses it:** Every time an approval stage is moved to "In Progress" and assigned to a user, the system creates a linked ToDo. This ensures no stage is silently pending — it always shows up in someone's task queue. Due dates come from the `due_date` field on the approval stage row.

### 3.4 Frappe Notifications

**What it does:** Setup → Notification allows you to define event-based or date-based email and in-app notifications. They can reference document fields using Jinja2 syntax and be sent to specific roles, document owners, or specific users.

**How this system uses it:** Six key notifications are configured for this system. NOC expiry alerts, fee letter deadline alerts, RERA renewal alerts, litigation flags, and OC issuance alerts. None of these require custom code — they are pure Frappe Notification configurations.

### 3.5 Frappe Dashboard & Dashboard Charts

**What it does:** The Frappe Dashboard module allows building visual dashboards from SQL queries or script-based data. Charts can be bar, donut, line, or number cards. Dashboards auto-refresh and can be linked to a Workspace.

**How this system uses it:** The Land Bank Summary dashboard and the RERA Status dashboard are built entirely using Frappe Dashboard Charts. No custom front-end code is required.

### 3.6 Frappe Report Builder

**What it does:** Frappe supports two types of reports — Query Reports (raw SQL with filters) and Script Reports (Python functions that return rows and columns with styling). Both types appear in the Frappe Desk and can be exported to Excel or PDF.

**How this system uses it:** All six reports in this system (Land Risk Analysis, Approval Status Tracker, NOC Pending Matrix, Fee Compliance Tracker, RERA Status, Land Bank Summary) are built using Query Reports or Script Reports. They reference custom Doctypes directly via SQL.

### 3.7 ERPNext Projects Module

**What it does:** ERPNext's native Project and Task Doctypes provide milestone tracking, Gantt charts, progress percentages, and resource assignment.

**How this system uses it:** When a project receives its Building Permit and moves to the "Under Construction" state, the system creates a linked ERPNext `Project` document. Each `Construction Milestone` row in the custom `Project Master` is mirrored as a `Task` under that ERPNext Project. This means construction progress is tracked using ERPNext's fully-featured project management tools without rebuilding them.

### 3.8 Frappe Role & Permission System

**What it does:** Frappe's DocPerm matrix controls Create, Read, Write, Delete, Submit, Cancel, Amend, and Print access per role per Doctype. User Permissions add a second layer that restricts which specific records a user can see within a Doctype.

**How this system uses it:** Six custom roles are defined. Each role has a specific permission profile per Doctype. User Permissions restrict Land Managers to only the land parcels assigned to them.

### 3.9 Frappe Print Format

**What it does:** Print Formats define how a document looks when printed or exported to PDF. They are Jinja2 HTML templates that can reference all fields and child tables of the document.

**How this system uses it:** Four custom Print Formats are defined: Land Information Sheet, Project Approval Status Report, Fee Letter Summary, and OC Application Checklist.

### 3.10 Frappe Workspace

**What it does:** The Frappe Workspace (formerly Desk) is the main landing page for each module. It supports shortcuts, charts, number cards, quick links, and recent document lists.

**How this system uses it:** A dedicated "Land & Project Management" Workspace is configured with shortcuts for common actions, live charts from the Land Bank dashboard, and number cards showing key KPIs.

---

## 4. Phase 1 — Land Bank Management

### 4.1 Master Data Doctypes

Before building the main `Land Master`, two simple reference Doctypes are created to ensure clean, linked data:

**Mandal Master**
A single-field Doctype (Mandal Name) that acts as a lookup for all mandal entries in Telangana. This is linked from `Land Master` so that mandal values are consistent across all land records. Add a `district` field here as well so that selecting a Mandal auto-fetches the District on the Land Master form.

**District Master**
A single-field Doctype linked from `Mandal Master` and `Land Master`. Pre-populated with all Telangana districts. Having this as a linked Doctype (rather than a Select field) allows future reporting by district without relying on text matching.

---

### Land Master Doctype

**Type:** Submittable Doctype (enables workflow and submission history)

**Naming Series:** `LAND-.YYYY.-.####` — This auto-increments and includes the year, giving IDs like `LAND-2025-0001`.

**Purpose:** The single source of truth for every land parcel in the organization's bank. No project can be created unless it links to a `Land Master` that has been approved through the full land workflow.

#### Section: Basic Identity

| Field Label | Field Type | Key Behaviour |
|---|---|---|
| Land ID | Data | Read-only; auto-set from naming series |
| Land Name | Data | Mandatory; descriptive name for the parcel |
| Total Extent (Acres) | Float | Mandatory |
| Total Extent (Guntas) | Float | 1 acre = 40 guntas; combined display shown in a read-only formula field |
| Facing | Select | North / East / West / South / North-East / North-West / South-East / South-West |
| Land Nature | Select | Patta / Assigned Land / Government Land / Ceiling Land / Inam Land / Forest Land / Wakf Land |
| Current Status | Select | Available / Under Litigation / Acquired / Under Approval / Approved for Development |
| Risk Flag | Check | Read-only; auto-set by server logic when litigation or missing critical documents are detected |

#### Section: Location

| Field Label | Field Type | Key Behaviour |
|---|---|---|
| Village | Data | |
| Mandal | Link → Mandal Master | Mandatory |
| District | Link → District Master | Auto-fetched from Mandal; read-only |
| State | Select | Defaulted to Telangana |
| Pin Code | Data | |
| Latitude | Float | Used for Google Maps embed |
| Longitude | Float | Used for Google Maps embed |
| Google Map Link | Data | Auto-generated from Latitude + Longitude via client script |
| Map Preview | HTML | Client script renders a Google Maps iframe using the coordinates |

**Client Script Behaviour for Map Preview:** When Latitude or Longitude changes, the client script builds a Google Maps embed URL using those values and injects it into the HTML field. This gives the user a live map preview without leaving the form. The Google Map Link field is also auto-populated for sharing.

#### Section: Survey Details (Child Table)

**Child Doctype Name:** `Survey Detail`

Each land parcel can span multiple survey numbers. This table captures one row per survey number.

| Field | Type | Notes |
|---|---|---|
| Survey Number | Data | Mandatory |
| Subdivision Number | Data | |
| Extent (Acres) | Float | |
| Extent (Guntas) | Float | |
| Classification | Select | Agricultural / Non-Agricultural / Waste Land |
| Patta Number | Data | |
| Revenue Sketch Available | Check | |

A validation rule ensures that the sum of extents across all survey rows does not exceed the Total Extent declared in the parent Land Master header.

#### Section: Ownership & Title Chain (Child Table)

Detailed in Section 4.3 below.

#### Section: Encumbrance & Documents (Child Table)

Detailed in Section 4.4 below.

#### Section: Compliance Parameters

This is a child table with typically one row per land parcel. Detailed in Section 4.2 below.

#### Section: Internal Notes

A Text Editor field for legal team remarks, internal notes about the parcel, and any communication history that does not fit elsewhere.

---

### 4.2 Land Compliance Intelligence

**Child Doctype Name:** `Land Compliance`

**Parent:** `Land Master`

This table captures all regulatory and physical constraints that determine whether a land parcel is eligible for development, conditionally eligible, or ineligible. It maps to HMDA, GHMC, and DTCP regulations as well as national-level restrictions.

#### Regulatory Zoning

| Field | Type | Notes |
|---|---|---|
| Zoning Type | Select | Residential / Commercial / Mixed Use / Industrial / Green Zone / No Development Zone / Special Development Zone |
| Master Plan Road Affected | Check | If Yes, road widening setback applies |
| Road Width (Metres) | Float | Required road width per master plan |
| Permissible FAR | Float | Floor Area Ratio as per zoning |
| Permissible Ground Coverage (%) | Float | |

#### Physical & Buffer Zone Constraints

| Field | Type | Notes |
|---|---|---|
| Water Body Nearby | Check | |
| Water Body Distance (Metres) | Float | HMDA mandates 30m setback from FTL |
| Lake Buffer Zone (FTL) | Check | Full Tank Level buffer — no construction permitted within FTL boundary |
| FSL Level | Float | Full Supply Level — relevant for HMDA GO 111 catchment areas |
| Nala Nearby | Check | Stormwater drain; setback rules apply |
| Nala Width Classification | Select | Minor / Major / Master Nala |
| Railway Buffer | Check | Indian Railways requires setback from track centre |
| Railway Distance (Metres) | Float | |
| High Tension Line Buffer | Check | |
| HT Line Distance (Metres) | Float | CEA rules: 3m–15m clearance depending on voltage |
| Gas Pipeline Buffer | Check | PNGRB regulations apply |
| Defense Zone | Check | Ministry of Defence no-construction zone |
| Airport Funnel Zone | Check | DGCA / AAI height restrictions apply |
| Airport Distance (Km) | Float | |

#### Hyderabad-Specific Restrictions

| Field | Type | Notes |
|---|---|---|
| GO 111 Area | Check | Catchment areas of Osman Sagar & Himayat Sagar; development strictly prohibited |
| HMDA Green Zone | Check | No construction; only afforestation permitted |
| GHMC Limits | Check | Determines which approval authority governs the project |
| HMDA Jurisdiction | Check | Outside GHMC but within HMDA metropolitan development area |

#### Development Eligibility (Auto-Computed)

| Field | Type | Notes |
|---|---|---|
| Development Eligible | Select | Yes / No / Conditional — computed by server-side validate hook |
| Eligibility Remarks | Small Text | Auto-populated with the reason for Conditional or No status |

**Auto-computation logic (configured as a server-side validate hook):**

The system sets `Development Eligible = No` if any of the following are true: GO 111 Area is checked, Defense Zone is checked, Forest Land nature is set on the parent, or Airport Funnel Zone is checked with distance under 20 km. It sets `Development Eligible = Conditional` if Water Body Nearby is checked (buffer review needed), Lake Buffer Zone is checked, HT Line Buffer is within 15 metres, or Master Plan Road affects the parcel (setback calculation needed). All other cases set it to `Yes`. The `Eligibility Remarks` field is populated with the reason automatically.

This logic is enforced by a `validate` hook in the `Land Master` Python controller, not in the child table controller, because it needs access to parent fields like `land_nature`.

---

### 4.3 Ownership & Title Chain

**Child Doctype Name:** `Ownership Record`

**Parent:** `Land Master`

This table builds the complete chain of title from the root deed to the current owner. For a land parcel to be legally clear, the ownership chain must be unbroken — every transfer must be documented and registered.

| Field | Type | Notes |
|---|---|---|
| Owner Name | Data | Mandatory |
| Owner Type | Select | Individual / Joint / HUF / Company / Trust / Government |
| Acquisition Mode | Select | Sale / Gift / Inheritance / Partition / Court Decree / Government Allotment / Power of Attorney |
| From Date | Date | Date of acquisition |
| To Date | Date | Left blank for the current owner |
| Registration Number | Data | Document registration number at SRO |
| Registration Office | Data | Sub-Registrar Office where registered |
| Consideration Amount | Currency | Sale value or declared value |
| Remarks | Small Text | Any notes about this transfer |

**Client-side validation:** When a new row is added, the client script checks whether the `From Date` of the new row overlaps with the `To Date` of any existing row. If there is a gap or overlap, it flags a warning (not an error, since some gaps may be legitimately explained in remarks). The legal team is responsible for resolving gaps before moving the land to the `Legally Verified` workflow state.

**Ownership Timeline View:** A separate Script Report called "Ownership Timeline" renders the ownership chain as a chronological list with visual indicators for duration and chain continuity. This report is accessible directly from the `Land Master` form via a custom button.

---

### 4.4 Document Management & OCR

**Child Doctype Name:** `Encumbrance Document`

**Parent:** `Land Master`

Every document related to a land parcel is uploaded here. The Doctype supports the full range of legal documents relevant to Indian land transactions.

| Field | Type | Notes |
|---|---|---|
| Document Type | Select | EC / Sale Deed / Link Document / Gift Deed / Partition Deed / Pahani / Adangal / 1-B Register / FMB Sketch / Tippan / Revenue Sketch / Court Order / Power of Attorney / Other |
| Document Number | Data | Reference number on the document |
| Document Date | Date | Date of issue or registration |
| Period From | Date | For EC: the start of the encumbrance period |
| Period To | Date | For EC: the end of the encumbrance period |
| Issued By | Data | Authority that issued the document |
| File Attachment | Attach | Mandatory before OCR can be triggered |
| OCR Status | Select | Not Processed / Processing / Extracted / Verified — Read-only except for Verified |
| OCR Extracted Data | Text | Read-only; populated by the OCR background job |
| Verified By | Link → User | Set by the legal team after manual verification |
| Verification Date | Date | Auto-set when Verified By is saved |

**Document Completeness Check:** A `validate` hook on `Land Master` counts the types of documents present and sets the `risk_flag = 1` if any of the following are missing: EC, at least one Sale Deed, Pahani, and FMB Sketch. This is a business rule that can be adjusted based on the legal team's minimum document requirements.

#### OCR Intelligence Module

The OCR module is a background job triggered by a custom button on the `Land Master` form. It is not automatic — a user must explicitly click "Process with OCR" for a specific document row. This design ensures that the legal team retains control over when processing happens and can review results before they are used.

**How it works conceptually:**
*Note: OCR integration - frappe assistant core is using the paddleocr or ollama (OCR configuration from the Assistant core Settings) if we can leverage the same for extracting data from the encumbrance documents, it would be great. Otherwise, we can implement the OCR integration for this module separately.
1. The user uploads a PDF or image scan to a document row in the `Encumbrance Document` child table.
2. The user selects one or more rows and clicks "Process with OCR".
3. The system enqueues a background job (using Frappe's built-in RQ job queue) for each selected row.
4. The background job reads the file, runs it through the OCR engine (Tesseract with both English and Telugu language packs), and extracts structured fields using pattern matching.
5. For documents written in Telugu (Pahani, Adangal, old Revenue Records), the Telugu language pack is required. Install `tesseract-ocr-tel` on the server.
6. Extracted data is written back to `OCR Extracted Data` in JSON format, and `OCR Status` is set to "Extracted".
7. The legal team reviews the extracted data and manually sets `OCR Status = "Verified"` and fills in `Verified By`.

**What is extracted per document type:**

- **Encumbrance Certificate:** Owner names for each transaction in the EC period, transaction types (sale, mortgage, gift), registration dates, document numbers. The system attempts to auto-populate `Ownership Record` rows from this data, which the legal team can then correct.
- **Sale Deed:** Vendor name, purchaser name, survey numbers, consideration amount, registration date, registration office.
- **Pahani:** Survey number, owner name, extent, classification, irrigation source, crop type.

**OCR accuracy note:** Scanned documents vary significantly in quality. The system treats OCR as a first-pass extraction tool that reduces manual data entry effort, not as a verified data source. The `OCR Status` field distinguishes between machine-extracted ("Extracted") and human-verified ("Verified") states, and the workflow prevents advancement until critical documents are "Verified".

---

### 4.5 Land Workflow

**Configured via:** Setup → Workflow in Frappe Desk

**Document Type:** Land Master

**Workflow Name:** Land Master Approval Workflow

#### States

| State Name | Style (Button Color) | Who Can Edit in This State |
|---|---|---|
| Draft | Gray (Secondary) | Land Manager, Management |
| Under Verification | Orange (Warning) | Legal Team, Survey Team |
| Legally Verified | Blue (Primary) | Legal Team |
| Approved for Development | Green (Success) | Management |
| Under Litigation | Red (Danger) | Legal Team |
| On Hold | Gray | Management |
| Rejected | Light | Management |

#### Transitions

| From State | Action Button Label | To State | Roles Allowed | Condition (if any) |
|---|---|---|---|---|
| Draft | Submit for Verification | Under Verification | Land Manager | All survey rows have data |
| Under Verification | Mark as Legally Verified | Legally Verified | Legal Team | |
| Under Verification | Flag as Under Litigation | Under Litigation | Legal Team | |
| Under Verification | Return to Draft | Draft | Legal Team | |
| Legally Verified | Approve for Development | Approved for Development | Management | Development Eligible is not "No" |
| Legally Verified | Put On Hold | On Hold | Management | |
| Legally Verified | Reject | Rejected | Management | |
| Under Litigation | Litigation Resolved | Under Verification | Legal Team | |
| On Hold | Resume | Legally Verified | Management | |

**Workflow condition for "Approve for Development":** The transition condition checks that `development_eligible != "No"` on the `Land Compliance` child table row. If it is "No", the workflow engine will block the transition and display the ineligibility reason.

**Email notification on transition:** Configure a Frappe Notification tied to each workflow transition so that the role responsible for the next action is notified by email and in-app alert when a document arrives in their queue.

---

## 5. Phase 2 — Project Approval & Execution

### 5.1 Project Master Doctype

**Type:** Submittable Doctype

**Naming Series:** `PROJ-.YYYY.-.####`

**Purpose:** Represents a real estate project built on an approved land parcel. Created only after the linked `Land Master` has reached "Approved for Development" state. The filter on the `land_master` Link field enforces this.

#### Section: Project Identity

| Field | Type | Notes |
|---|---|---|
| Project ID | Data | Auto from naming series; read-only |
| Project Name | Data | Mandatory |
| Linked Land | Link → Land Master | Filter: workflow_state = "Approved for Development" |
| Approval Authority | Select | GHMC / HMDA / DTCP — auto-detected from land location via server hook |
| Project Type | Select | Villas / Apartments / Plotted Layout / Commercial Complex / Mixed Use |
| Project Status | Select | Draft / Pre-Approval / Under Approval / Permit Issued / Under Construction / OC Applied / OC Received / Completed |

#### Section: Project Parameters

| Field | Type | Notes |
|---|---|---|
| Total Extent Used (Acres) | Float | Cannot exceed Land Master total extent — validated on save |
| Built-Up Area (Sq Mt) | Float | |
| Number of Units | Int | |
| Mortgage Units | Int | Auto = ceiling of (Number of Units × 10%); read-only; HMDA mandatory |
| Permissible FAR | Float | Fetched from Land Compliance via server script |
| Permissible Ground Coverage (%) | Float | Fetched from Land Compliance |

#### Section: Pre-Approval Checklist

These are check fields that the project manager must complete before the project can move past the "Pre-Approval" workflow state.

| Field | Notes |
|---|---|
| Approach Road Available | A motorable road must reach the project boundary |
| Road Width Adequate | Minimum as per approval authority norms |
| Land Conversion Required | Agri → Non-Agri conversion (1-B patta to non-agricultural conversion) |
| Land Conversion Status | Select: Not Required / Pending Application / Applied / Obtained |
| Revenue Sketch Available | Required by DTCP / HMDA for layout processing |
| Title Clear (Advocate Certificate) | Legal team confirmation |
| No Encumbrance Pending | Confirmed clean EC |

#### Child Tables on Project Master

- **NOC Tracker** — detailed in Section 5.2
- **Approval Stages** — detailed in Section 5.3
- **Construction Milestones** — detailed in Section 6.3

**Authority Auto-Detection Logic:** A `before_save` server hook reads the `mandal` and `district` from the linked `Land Master` and sets `approval_authority` based on a lookup table maintained in a simple `Authority Mapping` Doctype. This mapping table lists each mandal against its governing authority (GHMC, HMDA, or DTCP) and can be updated by management without code changes. This is preferable to hardcoding mandal lists in Python.
*Note: the Location should be like State to district, and district to mandal (parent child drilldown hierarchy) so if user selected the State then in the District will only give the districts of that state and similarly for mandal. and also the mandal should be linked to the district and district should be linked to the state. and also the mandal should be linked to the authority and authority should be linked to the district and district should be linked to the state. 

---

### 5.2 NOC Management

**Child Doctype Name:** `NOC Tracker`

**Parent:** `Project Master`

Every project requires a set of No Objection Certificates from different authorities before the main approval file can be submitted. This table tracks each NOC independently.

| Field | Type | Notes |
|---|---|---|
| NOC Type | Select | Airport Authority of India / Fire Department / Environmental Clearance / HMWSSB (Water) / TSSPDCL (Electricity) / Forest Department / Indian Railways / NHAI / TSPCB (Pollution) / Revenue (Tahsildar) |
| Applied Date | Date | |
| Expected Date | Date | |
| Received Date | Date | |
| NOC Number | Data | Reference number on the NOC letter |
| Valid Upto | Date | Expiry date of the NOC |
| Document | Attach | Scanned copy of the NOC |
| Status | Select | Not Applied / Applied / Pending / Received / Rejected / Expired |
| Follow-Up Remarks | Small Text | |

**Workflow Gate:** The `Project Master` workflow transition from "Under Approval" to "Fee Letter Received" is conditionally blocked unless all rows in the `NOC Tracker` table have `status = "Received"`. This condition is checked in the workflow transition definition in Frappe.

**Expiry Alert:** A Frappe Notification is configured to fire 30 days before `valid_upto` for any row where `status = "Received"`. It alerts the Approval Liaison Officer role by email and in-app notification, with the NOC type, project name, and expiry date in the message body.

---

### 5.3 Approval Workflow Chain

**Child Doctype Name:** `Approval Stage`

**Parent:** `Project Master`

This child table tracks each step in the approval chain inside the authority (GHMC / HMDA / DTCP). The stages vary slightly by authority but broadly follow the same pattern.

| Field | Type | Notes |
|---|---|---|
| Stage Name | Select | File Submission / APO Review / Tahsildar Title Verification / Planning Officer Approval / Director Approval / Commissioner Approval / Fee Letter Issued / Building Permit Order Issued |
| Assigned To | Link → User | Person responsible for following up on this stage |
| Submitted Date | Date | Date file was submitted to this officer |
| Due Date | Date | Expected turnaround date |
| Completed Date | Date | Actual completion date |
| Days Taken | Int | Auto-computed: Completed Date minus Submitted Date |
| Status | Select | Pending / In Progress / Completed / Returned for Resubmission / Rejected |
| Document Attached | Attach | Letter, acknowledgement, or order at this stage |
| Remarks | Small Text | |

**ToDo Integration:** When `Assigned To` is set and `Status` is changed to "In Progress", a server hook creates a Frappe Assignment (ToDo) linked to the `Project Master` for that user with the stage name and due date. The user sees this in their ToDo list and on their Frappe home page.

**Days Overdue Indicator:** A client script computes and displays a color indicator next to each row: green if within due date, amber if 1–14 days overdue, red if more than 14 days overdue. This is purely a visual indicator computed from `due_date` vs today's date.

---

### 5.4 Fee Letter & Conditions

**Doctype Name:** `Fee Letter`

**Type:** Submittable Doctype

**Naming Series:** `FL-.YYYY.-.####`

**Purpose:** When the approval authority issues the formal fee demand, it comes with conditions that must be met before the Building Permit Order is issued. This Doctype captures the fee letter and each condition independently.

| Field | Type | Notes |
|---|---|---|
| Fee Letter ID | Data | Auto from naming series |
| Project Master | Link | The project this fee letter belongs to |
| Issued Date | Date | |
| Due Date | Date | Auto = Issued Date + 30 days; editable |
| Issued By Authority | Select | GHMC / HMDA / DTCP |
| Letter Reference | Data | Reference number on the authority's letter |
| Scanned Letter | Attach | Uploaded copy of the official fee letter |
| Fee Conditions | Table | Child: Fee Condition |
| Total Amount | Currency | Auto-sum of all Fee Condition amounts |
| Payment Status | Select | Pending / Partial / Fully Paid |
| Building Permit Issued | Check | Set when BPO is received |
| Building Permit Order | Attach | Scanned BPO |
| Approved Plan Set | Attach | Approved architectural and structural drawings |

**Child Doctype: `Fee Condition`**

| Field | Type | Notes |
|---|---|---|
| Condition Type | Select | Mortgage Units / Road Widening Contribution / OSR (Open Space Reservation) / Betterment Charges / Development Charges / Impact Fee / Sewerage Connection / Water Connection / Other |
| Description | Small Text | Free text description of the condition |
| Amount | Currency | |
| Units (if applicable) | Int | For mortgage units condition |
| Status | Select | Pending / Paid / Transferred / Waived |
| Payment Date | Date | |
| Receipt Number | Data | Challan or receipt number |
| Receipt Attachment | Attach | |
| Remarks | Small Text | |

**Deadline Alert:** A Frappe Notification fires 7 days before `due_date` on `Fee Letter` if `payment_status != "Fully Paid"`. It emails and in-app-notifies the Project Manager and Management roles.

**Payment Status Auto-Update:** A `validate` hook on `Fee Letter` checks all `Fee Condition` rows. If all are "Paid" or "Waived", it sets `payment_status = "Fully Paid"`. If some are paid, it sets "Partial". This removes the need to manually update the header status.

**Gate for Building Permit:** The `Project Master` workflow transition to "Permit Issued" is conditionally blocked unless the linked `Fee Letter.payment_status = "Fully Paid"` and `building_permit_issued = 1`. The transition condition uses a `frappe.db.get_value` call in the condition expression.

---

## 6. Phase 3 — RERA, Construction & OC

### 6.1 RERA Process

**Doctype Name:** `RERA Process`

**Type:** Regular Doctype (not submittable; status tracked via a status field)

**Naming Series:** `RERA-.YYYY.-.####`

**Purpose:** Tracks RERA registration for the project as required under the Real Estate (Regulation and Development) Act, 2016, as adopted by Telangana (TSRERA).

| Field | Type | Notes |
|---|---|---|
| RERA ID | Data | Auto from naming series |
| Project Master | Link | |
| Application Date | Date | |
| Application Number | Data | TSRERA reference number |
| Promoter Name | Data | As per RERA registration |
| Escrow Account Number | Data | 70% collection escrow account — mandatory under RERA |
| Stage | Select | Documents Preparation / Application Submitted / Scrutiny / Deficiency Notice Received / Deficiency Resolved / Approved / Certificate Issued / Expired / Renewed |
| RERA Number | Data | Final registration number issued by TSRERA |
| Certificate Issue Date | Date | |
| Validity Date | Date | RERA registrations are typically valid for project duration |
| Renewal Required | Check | Auto-set 60 days before Validity Date via Notification |
| RERA Certificate | Attach | |

**Required Documents Table (child table within RERA Process):**

A sub-table listing all documents required for RERA submission. Each row has: Document Name, Mandatory (check), Uploaded (check), Attachment, Remarks. This serves as a checklist for the project manager.

Key documents include: Commencement Certificate, Sanctioned Plan, Title Deed of Land, Encumbrance Certificate, CA Certificate of project cost, Structural Engineer's certificate, Promoter's PAN and ITR, and the escrow bank account statement.

**Deficiency Management:** When `Stage = "Deficiency Notice Received"`, the system creates a ToDo assigned to the Project Manager with a 15-day due date and the subject "RERA Deficiency Notice — response required." The Stage can only be moved to "Deficiency Resolved" after uploading a response document.

---

### 6.2 Environmental Compliance

**Doctype Name:** `Environmental Compliance`

**Type:** Regular Doctype

**Purpose:** Tracks the two key environmental consents required from the Telangana State Pollution Control Board (TSPCB) — Consent for Establishment (CFE, pre-construction) and Consent for Operation (CFO, post-construction).

| Field | Type | Notes |
|---|---|---|
| Project Master | Link | |
| Project Category | Select | B1 / B2 — determines if EIA (Environmental Impact Assessment) is required |
| CFE Applied Date | Date | |
| CFE Reference Number | Data | |
| CFE Received Date | Date | |
| CFE Validity | Date | |
| CFE Attachment | Attach | |
| CFO Required | Check | Applicable after construction; required before OC |
| CFO Applied Date | Date | |
| CFO Received Date | Date | |
| CFO Validity | Date | |
| CFO Attachment | Attach | |
| EIA Required | Check | For projects above threshold size |
| EIA Report | Attach | |
| Status | Select | Not Started / CFE Applied / CFE Received / Construction Complete / CFO Applied / CFO Received / Fully Compliant |

**Alert:** A Frappe Notification fires 45 days before CFE Validity date if CFO has not yet been received, alerting the Project Manager.

---

### 6.3 Construction Milestones

**Child Doctype Name:** `Construction Milestone`

**Parent:** `Project Master`

| Field | Type | Notes |
|---|---|---|
| Milestone Name | Select | Foundation / Plinth Completion / Ground Floor Slab / First Floor Slab / [floors as applicable] / Terrace Slab / External Finishing / Internal Finishing / Plumbing & Electrical / Landscaping & Common Areas / Pre-OC Inspection Ready |
| Planned Date | Date | |
| Actual Date | Date | |
| Completion % | Percent | |
| Inspection Required | Check | |
| Inspection Done | Check | |
| Inspection Authority | Data | |
| Remarks | Small Text | |
| Photo | Attach | Progress photo |

**ERPNext Project Integration:** When `Project Master` workflow state moves to "Under Construction", a server hook creates a linked ERPNext `Project` document and maps all `Construction Milestone` rows as `Task` documents under that project. From that point, construction progress can be tracked using ERPNext's native Gantt chart and task completion features.

The `Project Master` record stores the `erpnext_project` Link field pointing to the created ERPNext Project. This allows navigation directly from the Land/Project management workspace to the construction project.

---

### 6.4 OC Application & Handover

**Doctype Name:** `OC Application`

**Type:** Submittable Doctype

**Naming Series:** `OCA-.YYYY.-.####`

**Purpose:** Manages the Occupancy Certificate application process, which mirrors the original approval workflow. Once OC is received, mortgage units are released, and the project transitions to "Completed."

| Field | Type | Notes |
|---|---|---|
| OC Application ID | Data | Auto from naming series |
| Project Master | Link | |
| Application Date | Date | |
| OC Approval Stages | Table | Child table using same `Approval Stage` structure — APO, Planning Officer, Director, Commissioner |
| Status | Select | Draft / Submitted / Under Review / Returned / OC Issued |
| OC Issued Date | Date | |
| OC Number | Data | |
| OC Attachment | Attach | |

**Required Documents for OC (child table):**

Same checklist approach as RERA. Key documents: Completion Certificate from architect, As-Built Drawings, Structural Stability Certificate, Fire NOC (final), Water Board NOC, Electrical Inspector's certificate, CFO from TSPCB.

**On OC Issuance — Mortgage Unit Release Trigger:**

When `status = "OC Issued"` is saved, a server hook:
1. Sets `Project Master.project_status = "Completed"`.
2. Creates a ToDo assigned to the Management role with the message: "OC issued for [project name]. Initiate release of [N] mortgage units with the Sub-Registrar Office."
3. Sends a Frappe Notification email to Management and Project Manager roles with the OC number, project name, and number of mortgage units to be released.
4. Logs a comment on the `Project Master` timeline: "OC Received — [date]. Mortgage units eligible for release: [N]."

**Handover Checklist (child table within OC Application):**

A final checklist before project handover to the residents' association or buyer group. Items include: OC received, RERA completion certificate filed, common area handover done, maintenance corpus collected, electricity meters transferred, water connection transferred, lift inspection certificate, fire safety handover.

---

## 7. Frappe Workflow Engine Design

### Core Design Principles

The Frappe Workflow Engine is the backbone of both the Land and Project lifecycles. All state management goes through the workflow engine — no custom state fields managed in Python.

**How the Workflow Engine Works in Frappe:**

When you attach a Workflow to a Doctype, Frappe adds a `workflow_state` field to that Doctype. The Workflow defines the complete set of valid states and the allowed transitions between them. Each transition has:
- A triggering action (a button label that appears on the form)
- A "From" state and a "To" state
- A list of roles that are allowed to perform this transition
- An optional condition (a Python expression evaluated at transition time)

The workflow also controls which roles can **edit** the document while it is in each state. This means that in the "Under Verification" state, only Legal Team and Survey Team can make changes, even though others might be able to read the document.

**Workflow Notifications:** For each transition in both workflows, configure a Frappe Notification to fire when the document enters the "To" state. Use the `document_type`, `event = "Workflow State Change"`, and `workflow_state_field_value = [target state]` settings. Reference the document's fields in the notification message to provide context.

### Land Master Workflow — Full Design

**Total States: 7** — Draft, Under Verification, Legally Verified, Approved for Development, Under Litigation, On Hold, Rejected

**Transition Matrix:**

The complete set of transitions covers normal progression (Draft → Under Verification → Legally Verified → Approved for Development), exception paths (Under Verification → Under Litigation; Legally Verified → On Hold; Legally Verified → Rejected), and recovery paths (Under Litigation → Under Verification; On Hold → Legally Verified; Rejected leads to amendment via standard Frappe amend functionality).

**Key condition on "Approve for Development" transition:**

The transition condition evaluates whether `development_eligible` on the associated `Land Compliance` record is not equal to "No". In the Workflow transition condition field, use a Frappe expression like:
```
doc.get("land_compliance") and [row.development_eligible for row in doc.land_compliance][0] != "No"
```
This ensures that no GO 111 land, defense land, or forest land can ever be accidentally approved.

### Project Master Workflow — Full Design

**Total States: 10** — Draft, Pre-Approval Check, NOC Collection, File Submitted, Under Authority Review, Fee Letter Received, Fee Paid, Building Permit Issued, Under Construction, OC Applied, OC Received, Completed

**Key gate transitions:**

- "Submit File to Authority" (NOC Collection → File Submitted): Condition checks that all NOC rows have `status = "Received"`.
- "Mark Fee as Paid" (Fee Letter Received → Fee Paid): Condition checks `Fee Letter.payment_status = "Fully Paid"` via `frappe.db.get_value`.
- "Issue Building Permit" (Fee Paid → Building Permit Issued): Condition checks `Fee Letter.building_permit_issued = 1`.
- "Apply for OC" (Under Construction → OC Applied): Condition checks that all `Construction Milestone` rows have `completion_percentage = 100`.

---

## 8. Role & Permission Matrix

### Custom Roles

Define the following six roles under **Setup → Role** in Frappe. These roles are in addition to the standard ERPNext roles (Administrator, System Manager, etc.).

| Role Name | Scope |
|---|---|
| Land Manager | Manages land parcel data entry and document collection |
| Legal Team | Performs title verification, ownership chain review, litigation tracking |
| Survey Team | Handles survey detail entry and physical verification |
| Project Manager | Owns project execution from approval through OC |
| Approval Liaison Officer | Follows up with GHMC/HMDA/DTCP; manages NOCs and fee letters |
| Management | Final approvals, escalation review, and strategic decisions |

### DocPerm Matrix

Configure via **Setup → DocType → [Doctype name] → Permissions** for each custom Doctype.

| Doctype | Land Manager | Legal Team | Survey Team | Project Manager | Approval Liaison | Management |
|---|---|---|---|---|---|---|
| Land Master | R, W, C | R, W, Sub | R, W | R | R | R, W, Sub, Can, Am |
| Survey Detail | R, W, C | R, W | R, W, C | R | R | R, W |
| Ownership Record | R | R, W, C | R | R | R | R, W |
| Encumbrance Document | R, W, C | R, W, C | R | R | R | R, W |
| Land Compliance | R, W | R, W | R, W | R | R | R, W |
| Project Master | R | R | — | R, W, C | R, W | R, W, Sub, Can, Am |
| NOC Tracker | — | R | — | R | R, W, C | R, W |
| Approval Stage | — | R | — | R | R, W, C | R, W |
| Fee Letter | — | R | — | R, W | R, W, C, Sub | R, W, Sub |
| RERA Process | — | R | — | R, W, C | R, W | R, W, Sub |
| Environmental Compliance | — | R | — | R, W, C | R | R, W |
| OC Application | — | R | — | R, W, C | R, W | R, W, Sub |

**Key:** R = Read, W = Write, C = Create, Sub = Submit, Can = Cancel, Am = Amend

### User Permissions

Use Frappe's User Permission feature to restrict Land Managers to records linked to specific mandalsor districts. This is configured under **Setup → User Permissions** by adding a User Permission record of DocType "Land Master" for each Land Manager user, restricting by the `mandal` field.

---

## 9. Notifications & Automation

All notifications are configured under **Setup → Notification** in Frappe. No custom email code is required.

### Notification Configurations

**1. Land Litigation Flag**
- Document Type: Land Master
- Event: Value Change
- Value Changed: current_status → Under Litigation
- Send To: Roles — Legal Team, Management
- Subject: `[URGENT] Litigation flagged on Land: {{ doc.land_name }}`
- Message: Includes land ID, location, and the name of the user who made the change

**2. NOC Expiry Warning**
- Document Type: NOC Tracker
- Event: Days Before
- Date Field: valid_upto
- Days Before: 30
- Condition: `doc.status == "Received"`
- Send To: Role — Approval Liaison Officer
- Subject: `NOC Expiry Alert: {{ doc.noc_type }} for {{ doc.parent }}`
- Message: Includes expiry date, project name, and a link to the Project Master

**3. Fee Letter Deadline**
- Document Type: Fee Letter
- Event: Days Before
- Date Field: due_date
- Days Before: 7
- Condition: `doc.payment_status != "Fully Paid"`
- Send To: Roles — Project Manager, Management
- Subject: `Fee Payment Due in 7 Days: {{ doc.project_master }}`

**4. RERA Expiry Warning**
- Document Type: RERA Process
- Event: Days Before
- Date Field: validity_date
- Days Before: 60
- Condition: `doc.stage == "Certificate Issued"`
- Send To: Roles — Project Manager, Management
- Subject: `RERA Renewal Required: {{ doc.project_master }}`

**5. OC Issued — Mortgage Release**
- Document Type: OC Application
- Event: Value Change
- Value Changed: status → OC Issued
- Send To: Roles — Management, Project Manager
- Subject: `OC Received — Mortgage Units Eligible for Release: {{ doc.project_master }}`
- Message: Fetches and includes mortgage unit count from the linked Project Master

**6. Weekly Missing Documents Summary**
- Document Type: Land Master
- Event: Days After (use a Script Report or Scheduled Job instead)
- This one requires a **Frappe Scheduled Job** (not a Notification) since it aggregates across multiple records. Configure it to run every Monday, query all Land Master records missing critical documents, and email the Land Manager role a summary table.

---

## 10. Reports & Dashboards

### Dashboard: Land Bank Summary

**Configure via:** Frappe Desk → Dashboard → New

This dashboard contains the following cards, all built using Frappe Dashboard Charts (no custom code):

**Number Cards:**
- Total Land in Bank (count of Land Master records)
- Total Extent (acres) — sum of `total_extent_acres`
- Available Land (count where `current_status = "Available"`)
- Under Litigation (count where `current_status = "Under Litigation"`)
- Approved for Development (count where `workflow_state = "Approved for Development"`)
- Risk Flagged (count where `risk_flag = 1`)

**Charts:**
- Land by Workflow State (Donut) — `SELECT workflow_state, COUNT(*) FROM tabLand Master GROUP BY workflow_state`
- Land by Nature (Bar) — `SELECT land_nature, COUNT(*) FROM tabLand Master GROUP BY land_nature`
- Land by District (Bar) — `SELECT district, SUM(total_extent_acres) FROM tabLand Master GROUP BY district`

### Dashboard: Project Approval Overview

**Number Cards:** Active Projects, Projects Under Approval, Building Permits Issued, OC Pending, Projects Completed

**Charts:**
- Projects by Status (Donut)
- Projects by Authority — GHMC vs HMDA vs DTCP (Bar)
- Monthly Permits Issued (Line, last 12 months)

### Report: Approval Status Tracker

**Type:** Script Report

**Filters:** Project Master, Approval Authority, Date Range, Current Stage

**Columns:** Project Name, Authority, Current Workflow State, Current Stage Name, Stage Owner, Days in Stage, NOC Pending Count, Fee Status, Target OC Date

**Indicator Logic:** Rows where `days_in_stage > 60` get a red indicator. Between 30 and 60 get amber. Under 30 get green. This uses Frappe's Script Report row formatting with the `indicator` column convention.

### Report: NOC Pending Matrix

**Type:** Query Report

**Purpose:** Shows all NOC rows across all projects where status is not "Received" or "Waived." Sorted by days overdue descending. Highlights expired NOCs in red.

**Columns:** Project Name, Authority, NOC Type, Applied Date, Expected Date, Days Overdue, Current Status

### Report: Fee Compliance Tracker

**Type:** Script Report

**Purpose:** All Fee Letters with their conditions, amounts, due dates, and payment status. Groups by project. Shows total amount, paid amount, and outstanding amount per project.

**Color Rules:** Overdue = red. Due within 7 days = amber. Fully paid = green.

### Report: Land Risk Analysis

**Type:** Script Report

**Purpose:** Provides a risk score for each land parcel across four dimensions: legal risk (from litigation and title gaps), compliance risk (from GO 111, defense, airport zones), document risk (missing critical documents), and approval risk (time in current workflow state).

Each dimension is scored 1 (low risk) to 5 (high risk). The composite score is the average. Export to PDF uses a custom Print Format styled as a risk matrix.

### Report: Ownership Timeline

**Type:** Script Report

**Filters:** Land Master (mandatory)

**Purpose:** Renders the complete ownership chain for a single land parcel as a chronological narrative. Shows each owner, the period of ownership, the acquisition mode, and any gaps in the chain. Flags gaps larger than 6 months with a warning.

### Report: RERA Status Dashboard

**Type:** Query Report

**Columns:** Project Name, RERA Number, Application Date, Certificate Date, Validity Date, Days to Expiry, Status

**Filters:** Status, Validity Within (days)

---

## 11. Print Formats

Configure all Print Formats under **Setup → Print Format** using Jinja2 HTML templates in Frappe.

### Land Information Sheet

**For Doctype:** Land Master

**Purpose:** Formal document summarizing a land parcel for legal review, management presentations, or due diligence packs.

**Sections:**
1. Header with organization logo and document title
2. Land identity block: Land ID, name, location, extent, land nature, current status
3. Survey Details table: survey numbers, subdivisions, extents, classification
4. Google Maps link (as QR code or clickable hyperlink in PDF)
5. Compliance Summary: zoning, buffer zone flags, development eligibility with reason
6. Ownership Chain table: all owners from root to present
7. Document Checklist: all uploaded documents with type, date, and verification status
8. Legal Remarks section
9. Footer with workflow state, last modified by, and date

### Project Approval Status Report

**For Doctype:** Project Master

**Sections:**
1. Project identity and linked land summary
2. Pre-approval checklist with tick/cross indicators
3. NOC Status table: all NOC types with status and expiry dates
4. Approval Stages table: all stages with assigned persons, dates, and status
5. Fee Letter summary: total amount, conditions, payment status
6. Current workflow state and next action required

### Fee Letter Summary

**For Doctype:** Fee Letter

**Sections:**
1. Authority details and fee letter reference
2. Project details
3. Conditions table with amounts and status
4. Total amount and payment due date (highlighted in red if overdue)
5. Payment receipt table (filled from Fee Condition rows where status = Paid)
6. Building Permit Order reference (if issued)

### OC Application Checklist

**For Doctype:** OC Application

**Sections:**
1. Project details
2. OC Approval Stages tracker (with dates and status)
3. Required Documents checklist with uploaded/pending indicators
4. Handover checklist
5. OC issuance details (once received)

---

## 12. Workspace Configuration

**Configure via:** Frappe Desk → Workspace → New

**Workspace Name:** Land & Project Management

**Icon:** Building / Home (use Frappe's built-in icon set)

**Roles Allowed:** All six custom roles defined in Section 8

### Workspace Layout

**Quick Shortcuts Row (top):**
- New Land Master
- New Project Master
- Land Bank Map View (custom page)
- Reports

**Number Cards Row:**
- Total Land (acres in bank)
- Available Parcels
- Active Projects
- Permits Issued This Year
- OC Pending

**Charts Row:**
- Land by Status (donut — from Land Bank Summary dashboard)
- Projects by Approval Stage (bar — from Project Approval Overview dashboard)

**Quick Lists:**
- Fee Letters Due This Week (query: `due_date <= adddays(today, 7) and payment_status != "Fully Paid"`)
- NOCs Expiring This Month
- Workflow Items Pending for Me (standard Frappe ToDo integration)

**Recent Documents:**
- Land Master (last 10, filtered by the logged-in user's role)
- Project Master (last 10)

---

## 13. External Integrations

### Google Maps Integration

**Implementation approach:** Client-side only. No server-side API calls required for the map preview.

When a user enters Latitude and Longitude on the `Land Master` form, a JavaScript client script generates a Google Maps embed URL and injects an `<iframe>` into the HTML field labelled "Map Preview". The Google Map Link field is also populated with a direct URL for sharing.

For the **Land Bank Map View** — a page showing all land parcels as markers on a single map — build a Frappe `Page` (a standalone web page within the Frappe desk). This page makes a `frappe.call` to fetch all `Land Master` records with their coordinates and renders them as markers on a Google Maps JavaScript API instance. Markers are color-coded by `current_status`. Clicking a marker opens a popup with the land name, extent, and a link to the full record.

**API key:** Store the Google Maps API key in Frappe **System Settings** or a **Single Doctype** called `LB-PAMS Settings` rather than hardcoding it. The client script fetches it via `frappe.call`.

### OCR Engine — Tesseract

**Installation:** Tesseract OCR is installed on the server at the OS level. The Python library `pytesseract` is installed in the Frappe virtual environment via `pip`. For Telugu-language documents, the `tesseract-ocr-tel` language pack must be installed on the server.

**Document processing library:** `PyMuPDF` (the `fitz` library) handles PDF-to-text extraction for text-based PDFs. `Pillow` handles image preprocessing for scanned documents.

**Job queue:** All OCR processing runs as Frappe background jobs using the built-in RQ (Redis Queue) integration. Do not run OCR synchronously in the request lifecycle — it will time out for large documents.

**Accuracy expectations:** Modern PDFs from government portals (Dharani, SRO) extract text cleanly via PyMuPDF. Scanned documents (hand-written, photocopied) require Tesseract and produce lower accuracy. For Telugu-script documents, accuracy is further limited by scan quality. The `OCR Status` field with a "Verified" state ensures legal team oversight before OCR-extracted data is treated as authoritative.

### Telangana Registration Portal (Dharani / SRO)

There is currently no public API available from the Telangana Registration Portal. The integration is therefore **manual-upload assisted**:

A `Document Fetch Tracker` child table within `RERA Process` and `Land Master` lists each document that must be obtained from the portal or SRO, with a `fetch_status` field (To Be Fetched / Fetched / Uploaded / Verified). The Approval Liaison Officer uses this checklist to track which documents have been collected from the government portals and uploaded.

**Future enhancement:** When the Dharani API or HMDA APIs become available, this checklist can be extended to include an "Auto-Fetch" button that calls the API directly.

### S3 Document Storage (Optional)

For large deployments with many scanned documents, configure Frappe to use Amazon S3 or compatible object storage (MinIO for on-premise). This is done in **Site Config** (the `site_config.json` file) and is transparent to all Doctypes — the `Attach` field stores S3 URLs instead of local paths. No application-level changes are required.

---

## 14. Validations & Business Rules

These are server-side rules enforced in Python `validate` hooks on the respective Doctypes. They prevent data integrity violations regardless of how the form is submitted (UI, API, or import).

### Land Master Validations

| Rule | Behaviour |
|---|---|
| Extent cannot be zero | Error on save if `total_extent_acres = 0` |
| Survey extents must not exceed total extent | Warning (not error) if sum of survey detail extents > total_extent_acres |
| GO 111 blocks development approval | Error on workflow transition to "Approved for Development" if `go111_area = 1` |
| Forest land blocks development | Error on workflow transition to "Approved for Development" if `land_nature = "Forest Land"` |
| Defense zone blocks development | Error on workflow transition if `defense_zone = 1` |
| Missing critical documents set risk flag | `risk_flag = 1` auto-set if EC, Sale Deed, or Pahani is not uploaded |
| Duplicate survey number warning | Warning (not error) if survey number exists in another Land Master |

### Project Master Validations

| Rule | Behaviour |
|---|---|
| Land must be approved | Link filter + validate hook: `Land Master.workflow_state must be "Approved for Development"` |
| Extent cannot exceed land total | Error if `total_extent_used > Land Master.total_extent_acres` |
| Mortgage units minimum | Error if `mortgage_units < ceil(no_of_units * 0.10)` |
| NOC completeness for file submission | Workflow condition: all NOC rows must be "Received" |
| Fee payment for permit | Workflow condition: Fee Letter payment must be "Fully Paid" |

### Fee Letter Validations

| Rule | Behaviour |
|---|---|
| Due date auto-set | `due_date = issued_date + 30 days` on save if not manually overridden |
| Total amount auto-sum | `total_amount` = sum of all Fee Condition amounts on each save |
| Payment status auto-update | Status auto-computed from condition rows on each save |

### OC Application Validations

| Rule | Behaviour |
|---|---|
| All milestones must be complete | Warning if any Construction Milestone has `completion_percentage < 100` when OC Application is submitted |
| CFO required before OC | Warning if Environmental Compliance record shows CFO not received |

---

## 15. Development Sequence

Build the system in the following order to avoid dependency errors and allow incremental testing at each stage.

### Stage 1 — Foundation Masters (Week 1)

Create `Mandal Master` and `District Master` as simple reference Doctypes. Pre-populate with all Telangana mandal and district data. Create the `Authority Mapping` Doctype linking mandals to their governing authority (GHMC/HMDA/DTCP). These must exist before `Land Master` can be built since it links to them.

### Stage 2 — Land Master Core (Weeks 2–3)

Build `Land Master` with the basic identity section, location section, and the `Survey Detail` child table. Configure naming series. Add the Google Maps client script for coordinate preview. Test data entry end-to-end before adding child tables.

### Stage 3 — Land Compliance & Documents (Week 4)

Add `Land Compliance` child table with all buffer zone fields and the development eligibility server-side logic. Add `Encumbrance Document` child table. Test the auto-flag of `risk_flag` and `development_eligible`.

### Stage 4 — Ownership Chain & OCR (Weeks 5–6)

Add `Ownership Record` child table. Build the OCR background job infrastructure: install Tesseract, PyMuPDF, and Pillow on the server. Build the OCR triggering button and background job. Test with sample EC and Sale Deed PDFs.

### Stage 5 — Land Workflow & Notifications (Week 7)

Configure the Land Master Workflow in the Frappe Workflow engine. Configure all Land-related Notifications. Test each workflow transition with the appropriate roles. Verify that conditions block invalid transitions correctly.

### Stage 6 — Project Master Core (Weeks 8–9)

Build `Project Master` with the identity section, parameters, and pre-approval checklist. Add `NOC Tracker` and `Approval Stage` child tables. Build the authority auto-detection server hook. Test link filtering to approved land only.

### Stage 7 — Fee Letter & Conditions (Week 10)

Build `Fee Letter` and `Fee Condition` Doctypes. Add the payment status auto-computation hook. Configure deadline notification. Test the workflow gate on Project Master that requires fee payment.

### Stage 8 — RERA, Environmental & OC (Weeks 11–12)

Build `RERA Process`, `Environmental Compliance`, and `OC Application` Doctypes. Build the ERPNext Project creation hook for construction milestones. Configure the OC issuance trigger for mortgage unit release ToDo.

### Stage 9 — Project Workflow (Week 13)

Configure the Project Master Workflow with all ten states and their transitions. Set up all transition conditions (NOC completeness, fee payment, milestone completion). Test the full project lifecycle from Draft to Completed using test data.

### Stage 10 — Reports & Dashboards (Weeks 14–15)

Build all six reports. Build the Land Bank Summary and Project Approval Overview dashboards. Configure all six Notifications from Section 9. Build the Land Bank Map View custom page.

### Stage 11 — Print Formats (Week 16)

Build all four Print Formats using Jinja2 HTML in Frappe. Test PDF export for each. Ensure all child tables render correctly in the print output.

### Stage 12 — Workspace & Roles (Week 17)

Configure the "Land & Project Management" Workspace. Set up all DocPerm configurations for the six custom roles. Configure User Permissions for Land Managers. Conduct role-based access testing with test users.

### Stage 13 — UAT & Data Migration (Weeks 18–20)

Conduct User Acceptance Testing with the client's land managers, legal team, and project managers. Use Frappe's built-in Data Import Tool to migrate existing land records from Excel or legacy systems via CSV. Clean and validate imported data against the validation rules.

---

## 16. Edge Cases & Risk Flags

### Multiple Ownership Conflicts

When the OCR module extracts multiple owner names from an EC and creates `Ownership Record` rows, it is possible to end up with overlapping ownership periods. The client-side date overlap warning handles detection, but resolution requires the legal team to manually reconcile the records against physical documents. The system does not auto-resolve conflicts.

### Missing EC History

Some older land parcels may have incomplete EC history due to records predating computerization. The `document_risk` dimension of the Land Risk Analysis Report flags these. The legal team should obtain a Long-Term EC from the SRO (covering the maximum available period) and upload it. The `Encumbrance Document` table supports an EC with `period_from` going back to the earliest available date.

### GO 111 Land in Bank

A land parcel can enter the system as "Available" even if it falls under GO 111, since the classification may only become apparent during the compliance review stage. The compliance validation blocks development approval for such land, but the parcel remains in the system as an "On Hold" record. Management can add a note explaining why it is retained (e.g., pending government dereservation or court proceedings).

### Buffer Zone Conditional Cases

Land flagged as "Conditional" for development eligibility (e.g., near a water body but beyond the mandatory buffer distance) requires a clearance from HMDA before development approval. The system captures this in `Eligibility Remarks` and requires the Legal Team to upload the HMDA clearance letter before moving the workflow to "Approved for Development."

### Delayed Approvals Beyond Deadline

When the approval authority (GHMC/HMDA/DTCP) exceeds its statutory processing time, the `Approval Stage` row with `days_overdue > 0` triggers the amber/red indicators in the Approval Status Tracker report. The Approval Liaison Officer should log communication details in the `Remarks` field of each stage row to maintain a dated interaction record for potential legal escalation.

### RERA Expiry During Construction

If construction is delayed and the RERA registration expires before the project is completed, the `renewal_required` field on `RERA Process` is auto-checked 60 days before expiry. The Notification fires. The Project Manager must apply for renewal with TSRERA before the expiry date. The system does not block construction activities on RERA expiry, but the OC Application cannot be submitted in "Fully Compliant" status without an active RERA registration.

### Mortgage Unit Release

Mortgage units cannot be released before OC is received. The system enforces this by only triggering the mortgage unit release ToDo when `OC Application.status = "OC Issued"`. The actual release requires a physical process at the Sub-Registrar Office — the system manages the trigger and tracking, not the legal execution.

### Amendment After Submission

Frappe's standard `Amend` functionality is enabled for both `Land Master` and `Project Master`. When a submitted document needs to be corrected (e.g., extent updated after resurvey, project scope changed), the user cancels the original and creates an amendment. The amendment carries an `amended_from` link to the original. All workflows restart from Draft for the amended document. All child records are carried over from the original.

---

## Appendix: Key Frappe Concepts Reference

| Concept | Where Configured | Purpose in This System |
|---|---|---|
| Naming Series | Doctype → Naming | Consistent IDs for Land Master, Project Master, Fee Letter, etc. |
| Workflow | Setup → Workflow | State machine for Land and Project lifecycles |
| DocPerm | Setup → Doctype → Permissions | Role-based access to each Doctype |
| User Permission | Setup → User Permissions | Restricts Land Managers to assigned land records |
| Notification | Setup → Notification | Date and event-based email and in-app alerts |
| Print Format | Setup → Print Format | PDF templates for official documents |
| Dashboard Chart | Frappe Desk → Dashboard | Live charts for management overview |
| Script Report | Frappe Desk → Report | Custom multi-column tabular reports with indicators |
| Query Report | Frappe Desk → Report | Direct SQL query based reports |
| Background Job (Frappe Enqueue) | Python controller | Runs OCR processing without blocking the user interface |
| Assignment / ToDo | frappe.utils.assign_to | Links tasks to users from workflow transitions |
| Custom Button | Client Script | Triggers server-side actions like OCR processing |
| Fetch from Linked Document | Doctype → Field Settings | Auto-fills fields from linked records (e.g., district from mandal) |
| Jinja2 in Print Format | Print Format Editor | Dynamic document rendering with field values and loops |
| ERPNext Project + Task | ERPNext Projects Module | Construction milestone tracking via native Gantt tools |

---

*Document Version: 1.0 — LB-PAMS Knowledge Base for Frappe / ERPNext Development*

*This document should be read alongside the official Frappe Framework documentation at frappeframework.com/docs and the ERPNext documentation at docs.erpnext.com. All Doctype, Workflow, and Notification configurations described here are achievable through the Frappe Desk UI without writing Python or JavaScript for the configuration itself — code is required only for validate hooks, client scripts, background jobs, and custom pages.*
