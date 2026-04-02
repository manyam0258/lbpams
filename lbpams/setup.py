"""
Populate Telangana Districts, Mandals, and Authority Mappings.
Run via: bench --site <site> execute lbpams.setup.populate_telangana_data
"""

import frappe


TELANGANA_DATA = {
    "Adilabad": {
        "mandals": [
            "Adilabad", "Bazarhathnoor", "Bela", "Boath", "Gudihatnoor",
            "Ichoda", "Jainath", "Jainad", "Mavala", "Neradigonda",
            "Sirikonda", "Talamadugu", "Tamsi", "Utnoor"
        ],
        "authority": "DTCP"
    },
    "Bhadradri Kothagudem": {
        "mandals": [
            "Aswapuram", "Bhadrachalam", "Chandrugonda", "Charla",
            "Dammapet", "Dummugudem", "Gundala", "Julurpad",
            "Karakagudem", "Kothagudem", "Laxmidevipalli", "Manuguru",
            "Mulakalapalli", "Paloncha", "Pinapaka", "Sujathanagar",
            "Tekulapalli", "Yellandu"
        ],
        "authority": "DTCP"
    },
    "Hanumakonda": {
        "mandals": [
            "Damera", "Elkathurthy", "Geesugonda", "Hanumakonda",
            "Hasanparthy", "Inavolu", "Narsampet", "Parkal",
            "Wardhannapet"
        ],
        "authority": "DTCP"
    },
    "Hyderabad": {
        "mandals": [
            "Amberpet", "Ameerpet", "Asifnagar", "Bandlaguda",
            "Bahadurpura", "Charminar", "Dabeerpura", "Golconda",
            "Himayatnagar", "Khairatabad", "Marredpally", "Musheerabad",
            "Nampally", "Secunderabad", "Serilingampally", "Shaikpet",
            "Tirumalagiri"
        ],
        "authority": "GHMC"
    },
    "Jagtial": {
        "mandals": [
            "Beerpur", "Dharmapuri", "Gollapalli", "Jagtial",
            "Kodimial", "Korutla", "Mallial", "Medipalli",
            "Metpalli", "Mohanraopet", "Pegadapalli", "Raikal",
            "Sarangapur", "Velgatoor"
        ],
        "authority": "DTCP"
    },
    "Jangaon": {
        "mandals": [
            "Bachannapeta", "Chilpur", "Devaruppula", "Ghanpur Station",
            "Jangaon", "Kodakandla", "Lingalaghanpur", "Narmetta",
            "Palakurthy", "Raghunathpalli", "Zaffergadh"
        ],
        "authority": "DTCP"
    },
    "Jayashankar Bhupalpally": {
        "mandals": [
            "Bhupalpally", "Chennur", "Chityal", "Ghanpur Mulug",
            "Kataram", "Mahadevpur", "Mogullapalli", "Morthad",
            "Palimela", "Regonda", "Tekumatla"
        ],
        "authority": "DTCP"
    },
    "Jogulamba Gadwal": {
        "mandals": [
            "Aija", "Alampur", "Dharur", "Gadwal",
            "Ghattu", "Ieeja", "Itikyal", "Maldakal",
            "Rajoli", "Undavelli", "Waddepalli"
        ],
        "authority": "DTCP"
    },
    "Kamareddy": {
        "mandals": [
            "Banswada", "Bichkunda", "Domakonda", "Gandhari",
            "Jukkal", "Kamareddy", "Lingampet", "Machareddy",
            "Madnur", "Nasrullabad", "Nizamsagar", "Pitlam",
            "Rajampet", "Ramareddy", "Sadasivanagar", "Tadwai",
            "Yellareddy"
        ],
        "authority": "DTCP"
    },
    "Karimnagar": {
        "mandals": [
            "Bommakal", "Chigurumamidi", "Choppadandi", "Ganneruvaram",
            "Huzurabad", "Karimnagar", "Kothapalli", "Manakondur",
            "Ramadugu", "Shankarapatnam", "Thimmapur", "Veenavanka"
        ],
        "authority": "DTCP"
    },
    "Khammam": {
        "mandals": [
            "Bonakal", "Chintakani", "Enkoor", "Kallur",
            "Khammam Rural", "Khammam Urban", "Konijerla", "Kusumanchi",
            "Madhira", "Mudigonda", "Nelakondapalli", "Penuballi",
            "Raghunadhapalem", "Sathupalli", "Singareni", "Tallada",
            "Thallada", "Thirumalayapalem", "Vemsoor", "Wyra",
            "Yerrupalem"
        ],
        "authority": "DTCP"
    },
    "Kumuram Bheem Asifabad": {
        "mandals": [
            "Asifabad", "Dahegaon", "Jainoor", "Kagaznagar",
            "Kerameri", "Koutala", "Lingapur", "Penchikalpet",
            "Rebbena", "Sirpur T", "Tiryani", "Wankdi"
        ],
        "authority": "DTCP"
    },
    "Mahabubabad": {
        "mandals": [
            "Bayyaram", "Chinna Gudur", "Dornakal", "Garla",
            "Gudur", "Kesamudram", "Kothaguda", "Kuravi",
            "Mahabubabad", "Maripeda", "Nellikuduru", "Peddavangara",
            "Thorrur"
        ],
        "authority": "DTCP"
    },
    "Mahbubnagar": {
        "mandals": [
            "Addakal", "Balanagar", "Bhootpur", "Bhoothpur",
            "Chinnachintakunta", "Devarkadra", "Dhanwada",
            "Gandeed", "Hanwada", "Jadcherla", "Koilkonda",
            "Mahbubnagar", "Midjil", "Moosapet", "Navabpet",
            "Rajapur"
        ],
        "authority": "DTCP"
    },
    "Mancherial": {
        "mandals": [
            "Bellampalli", "Bheemini", "Chennur", "Dandepalli",
            "Hajipur", "Jaipur", "Kannepalli", "Kasipet",
            "Kotapalli", "Luxettipet", "Mancherial", "Mandamarri",
            "Naspur", "Tandur", "Vemanpalli"
        ],
        "authority": "DTCP"
    },
    "Medak": {
        "mandals": [
            "Alladurg", "Chegunta", "Chilpur", "Havelighanpur",
            "Kowdipalli", "Kulcharam", "Medak", "Manoharabad",
            "Narsingi", "Narsapur", "Papannapet", "Ramayampet",
            "Shankarampet A", "Shankarampet B", "Shivampet",
            "Tekmal", "Toopran"
        ],
        "authority": "DTCP"
    },
    "Medchal-Malkajgiri": {
        "mandals": [
            "Alwal", "Boduppal", "Dammaiguda", "Ghatkesar",
            "Kapra", "Keesara", "Kompally", "Kukatpalli",
            "Medchal", "Malkajgiri", "Miyapur",
            "Quthbullapur", "Shamirpet", "Uppal"
        ],
        "authority": "HMDA"
    },
    "Mulugu": {
        "mandals": [
            "Eturunagaram", "Govindaraopet", "Kannaigudem",
            "Mangapet", "Mulugu", "Tadvai", "Venkatapuram",
            "Wazeed"
        ],
        "authority": "DTCP"
    },
    "Nagarkurnool": {
        "mandals": [
            "Achampet", "Amrabad", "Balmoor", "Bijinapally",
            "Charakonda", "Kalwakurthy", "Kollapur", "Lingal",
            "Nagarkurnool", "Padara", "Peddakothapally",
            "Tadoor", "Telkapalli", "Uppununthala",
            "Veldanda"
        ],
        "authority": "DTCP"
    },
    "Nalgonda": {
        "mandals": [
            "Chityal", "Chandur", "Devarakonda", "Haliya",
            "Kangal", "Kattangur", "Marriguda", "Miryalaguda",
            "Munugode", "Nakrekal", "Nalgonda", "Nampally",
            "Narketpalli", "Pedda Adisherlapalli", "Shaligouraram",
            "Thipparthi", "Tripuraram"
        ],
        "authority": "DTCP"
    },
    "Narayanpet": {
        "mandals": [
            "Damargidda", "Kosgi", "Maddur", "Makthal",
            "Marikal", "Narayanpet", "Narva", "Utkoor"
        ],
        "authority": "DTCP"
    },
    "Nirmal": {
        "mandals": [
            "Basar", "Bhainsa", "Dilawarpur", "Kaddam",
            "Kaddampeddur", "Khanapur", "Kubeer", "Laxmanchanda",
            "Lokeswaram", "Mamda", "Mudhole", "Nirmal",
            "Sarangapur", "Soan"
        ],
        "authority": "DTCP"
    },
    "Nizamabad": {
        "mandals": [
            "Armoor", "Balkonda", "Bheemgal", "Bodhan",
            "Dichpalli", "Dharpalli", "Indalwai", "Jakranpalli",
            "Kotagiri", "Makloor", "Mortad", "Mugpal",
            "Navipet", "Nizamabad North", "Nizamabad South",
            "Nandipet", "Renjal", "Rudrur", "Sirkonda",
            "Velpur", "Yedapalli"
        ],
        "authority": "DTCP"
    },
    "Peddapalli": {
        "mandals": [
            "Dharmaram", "Eligaid", "Julapalli", "Kalvasrirampur",
            "Manthani", "Oddicheruvu", "Peddapalli", "Ramagundam",
            "Sultanabad"
        ],
        "authority": "DTCP"
    },
    "Rajanna Sircilla": {
        "mandals": [
            "Boinpalli", "Chandurthi", "Ellanthakunta",
            "Gambhiraopet", "Konaraopet", "Mustabad",
            "Sircilla", "Thangallapalli", "Veernapalli",
            "Vemulawada", "Yellareddipet"
        ],
        "authority": "DTCP"
    },
    "Rangareddy": {
        "mandals": [
            "Amangal", "Balapur", "Chevella", "Gandipet",
            "Hayathnagar", "Ibrahimpatnam", "Kadthal", "Kandukur",
            "Keshampet", "Maheshwaram", "Manchal", "Moinabad",
            "Nandigama", "Rajendranagar", "Saroornagar",
            "Shamshabad", "Shankarpalli", "Tandur",
            "Yacharam"
        ],
        "authority": "HMDA"
    },
    "Sangareddy": {
        "mandals": [
            "Ameenpur", "Andole", "Bollaram", "Hathnoora",
            "Jharasangam", "Kangti", "Kandi", "Kohir",
            "Kondapur", "Manoor", "Mogudampalli", "Narayankhed",
            "Nyalkal", "Patancheru", "Pulkal", "RC Puram",
            "Raikode", "Sadasivpet", "Sangareddy",
            "Zaheerabad"
        ],
        "authority": "HMDA"
    },
    "Siddipet": {
        "mandals": [
            "Acchamapet", "Cheriyal", "Doultabad", "Dubbak",
            "Gajwel", "Husnabad", "Koheda", "Kondapak",
            "Markook", "Mirdoddi", "Mutharam", "Nangunoor",
            "Raipole", "Siddipet", "Thoguta", "Wargal"
        ],
        "authority": "DTCP"
    },
    "Suryapet": {
        "mandals": [
            "Athmakur", "Chivvemla", "Chilkur", "Garidepalli",
            "Huzurnagar", "Jaji Reddi Gudem", "Kodad",
            "Mattampalli", "Mellacheruvu", "Motigattu",
            "Munagala", "Nadigudem", "Neredcherla",
            "Palakeedu", "Penpahad", "Suryapet",
            "Thungathurthi", "Tirumalgiri"
        ],
        "authority": "DTCP"
    },
    "Vikarabad": {
        "mandals": [
            "Basheerabad", "Bomraspet", "Dharoor", "Doma",
            "Doulatabad", "Kodangal", "Kulkacherla",
            "Mominpet", "Nawabpet", "Pargi", "Pudoor",
            "Tandur", "Vikarabad"
        ],
        "authority": "DTCP"
    },
    "Wanaparthy": {
        "mandals": [
            "Amarchinta", "Atmakur", "Gopalpet",
            "Kothakota", "Madanapur", "Pangal",
            "Pebbair", "Srirangapur", "Wanaparthy"
        ],
        "authority": "DTCP"
    },
    "Warangal": {
        "mandals": [
            "Atmakur", "Bhupalpalli", "Dharmasagar",
            "Duggondi", "Khanapur", "Nallabelli",
            "Nekkonda", "Pakhala", "Sangem",
            "Torredu", "Warangal"
        ],
        "authority": "DTCP"
    },
    "Yadadri Bhuvanagiri": {
        "mandals": [
            "Alair", "Atmakur", "Bhongir", "Bhuvanagiri",
            "Bibinagar", "Choutuppal", "Halia",
            "Mothkur", "Pochampalli", "Rajapet",
            "Ramannapeta", "Turkapalli", "Valigonda",
            "Yadagirigutta"
        ],
        "authority": "HMDA"
    },
}


def populate_telangana_data():
    """Create all Telangana districts, mandals, and authority mappings."""
    print("=" * 60)
    print("Populating Telangana Master Data")
    print("=" * 60)

    total_districts = 0
    total_mandals = 0
    total_mappings = 0

    for district_name, data in TELANGANA_DATA.items():
        # Create District
        if not frappe.db.exists("District Master", district_name):
            doc = frappe.new_doc("District Master")
            doc.district_name = district_name
            doc.state = "Telangana"
            doc.is_active = 1
            doc.insert(ignore_permissions=True)
            total_districts += 1
            print(f"  Created District: {district_name}")
        else:
            print(f"  Exists District: {district_name}")

        # Create Mandals
        for mandal_name in data["mandals"]:
            if not frappe.db.exists("Mandal Master", mandal_name):
                doc = frappe.new_doc("Mandal Master")
                doc.mandal_name = mandal_name
                doc.district = district_name
                doc.is_active = 1
                try:
                    doc.insert(ignore_permissions=True)
                    total_mandals += 1
                    print(f"    Created Mandal: {mandal_name}")
                except frappe.exceptions.DuplicateEntryError:
                    # Mandal name exists in another district — rename
                    doc.mandal_name = f"{mandal_name} ({district_name})"
                    if not frappe.db.exists("Mandal Master", doc.mandal_name):
                        doc.insert(ignore_permissions=True)
                        total_mandals += 1
                        print(f"    Created Mandal: {doc.mandal_name} (renamed)")
                    else:
                        print(f"    Exists Mandal: {doc.mandal_name}")
            else:
                print(f"    Exists Mandal: {mandal_name}")

            # Create Authority Mapping
            mandal_key = mandal_name
            if frappe.db.exists("Mandal Master", f"{mandal_name} ({district_name})"):
                mandal_key = f"{mandal_name} ({district_name})"

            if frappe.db.exists("Mandal Master", mandal_key) and not frappe.db.exists("Authority Mapping", mandal_key):
                try:
                    mapping = frappe.new_doc("Authority Mapping")
                    mapping.mandal = mandal_key
                    mapping.authority = data["authority"]
                    mapping.insert(ignore_permissions=True)
                    total_mappings += 1
                except Exception as e:
                    print(f"    Warning: Could not create mapping for {mandal_key}: {e}")

    frappe.db.commit()

    print(f"\n{'=' * 60}")
    print(f"Summary:")
    print(f"  Districts created: {total_districts}")
    print(f"  Mandals created: {total_mandals}")
    print(f"  Authority Mappings created: {total_mappings}")
    print(f"{'=' * 60}")


def create_custom_roles():
    """Create the 6 custom roles for LB-PAMS."""
    roles = [
        {"role_name": "Land Manager", "desk_access": 1,
         "description": "Manages land parcel data entry and document collection"},
        {"role_name": "Legal Team", "desk_access": 1,
         "description": "Performs title verification, ownership chain review, litigation tracking"},
        {"role_name": "Survey Team", "desk_access": 1,
         "description": "Handles survey detail entry and physical verification"},
        {"role_name": "Project Manager", "desk_access": 1,
         "description": "Owns project execution from approval through OC"},
        {"role_name": "Approval Liaison Officer", "desk_access": 1,
         "description": "Follows up with GHMC/HMDA/DTCP; manages NOCs and fee letters"},
        {"role_name": "Management", "desk_access": 1,
         "description": "Final approvals, escalation review, and strategic decisions"},
    ]

    for role_data in roles:
        if not frappe.db.exists("Role", role_data["role_name"]):
            role = frappe.new_doc("Role")
            role.role_name = role_data["role_name"]
            role.desk_access = role_data.get("desk_access", 1)
            role.insert(ignore_permissions=True)
            print(f"  Created Role: {role_data['role_name']}")
        else:
            print(f"  Exists Role: {role_data['role_name']}")

    frappe.db.commit()
    print("Custom roles setup complete.")


def setup_all():
    """Run full setup: roles, then data."""
    create_custom_roles()
    populate_telangana_data()
