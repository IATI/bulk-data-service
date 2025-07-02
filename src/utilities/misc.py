import datetime
import glob
import hashlib
import io
import re
import uuid
import zipfile
from typing import Any

import requests

START_OF_IATI_XML_REGEX = re.compile(
    r"^(<\?xml[^>]*>)?\s*(<!--[^>]*-->)?\s*<iati-(activities|organisations)", re.IGNORECASE
)


def content_has_iati_opening_element(content: str) -> bool:
    return START_OF_IATI_XML_REGEX.search(content) is not None


def get_initial_chars_if_text(download_response: requests.Response, encoding: str | None) -> str | None:
    if encoding is None:
        return None

    download_response.encoding = encoding

    return download_response.text[:6000].replace("\n", "").replace("\r", "")


def get_initial_iati_content(initial_chars: str | None) -> str | None:

    if initial_chars is None:
        return None

    initial_chars_wo_newlines = initial_chars.replace("\n", "").replace("\r", "")

    return initial_chars_wo_newlines[:150] if content_has_iati_opening_element(initial_chars_wo_newlines) else None


def dataset_has_iati_xml_download(dataset: dict) -> bool:
    return dataset["last_known_good_dataset_downloaded"] is not None


def get_hash_of_bytes(content: bytes) -> str:
    hasher = hashlib.sha1()
    hasher.update(content)
    return hasher.hexdigest()


def get_hash(content: str, encoding: str) -> str:
    hasher = hashlib.sha1()
    hasher.update(content.encode(encoding))
    return hasher.hexdigest()


def get_hash_excluding_generated_timestamp(content: str, encoding: str) -> str:
    content_to_hash = re.sub(r'generated-datetime="[^"]+"', "", content)
    hasher = hashlib.sha1()
    hasher.update(content_to_hash.encode(encoding))
    return hasher.hexdigest()


def is_str_valid_uuid(uuid_str_to_check: str) -> bool:
    try:
        uuid_object = uuid.UUID(uuid_str_to_check)
    except ValueError:
        return False
    return str(uuid_object) == uuid_str_to_check


def get_timestamp(isodate: str = "") -> datetime.datetime:
    if isodate != "":
        return datetime.datetime.fromisoformat(isodate).astimezone()
    else:
        return datetime.datetime.now(tz=datetime.timezone.utc)


def get_timestamp_as_str(isodate: str = "") -> str:
    if isodate != "":
        return datetime.datetime.fromisoformat(isodate).astimezone().isoformat()
    else:
        return datetime.datetime.now(tz=datetime.timezone.utc).isoformat()


def get_timestamp_as_str_z(isodate: str = "") -> str:
    dt = (
        datetime.datetime.fromisoformat(isodate).astimezone()
        if isodate != ""
        else datetime.datetime.now(tz=datetime.timezone.utc)
    )
    dt = dt.replace(microsecond=0)
    return dt.isoformat().replace("+00:00", "Z")


def set_timestamp_tz_utc(date: datetime.datetime) -> datetime.datetime:
    return date.replace(tzinfo=datetime.timezone.utc)


def zip_data_as_single_file(filename: str, data: bytes) -> bytes:

    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w") as xml_zipped:
        xml_zipped.writestr(filename, data)

    return zip_buffer.getvalue()


def get_number_xml_files_in_dir(dir_name):
    return len(glob.glob("**/*.xml", root_dir=dir_name, recursive=True))


def filter_dict_by_structure(source: dict, structure_to_retain: dict) -> dict:
    filtered_dict = {}

    for key, value in structure_to_retain.items():
        if key not in source:
            continue

        if structure_to_retain[key] is None:
            filtered_dict[key] = source[key]

        elif isinstance(structure_to_retain[key], dict) and not isinstance(source[key], dict):
            filtered_dict[key] = source[key]

        elif isinstance(structure_to_retain[key], dict) and isinstance(source[key], dict):
            filtered_dict[key] = filter_dict_by_structure(source[key], structure_to_retain[key])

        elif isinstance(structure_to_retain[key], list) and not isinstance(source[key], list):
            filtered_dict[key] = source[key]

        elif isinstance(structure_to_retain[key], list) and isinstance(source[key], list):
            filtered_dict[key] = [
                filter_dict_by_structure(
                    item, structure_to_retain[key][0] if len(structure_to_retain[key]) == 1 else {}
                )
                for item in source[key]
            ]

    return filtered_dict


def find_object_by_key(objects: list, key: str, value_to_find: Any):
    return next(filter(lambda x: x[key] == value_to_find, objects), None)


def lookup_licence_title_from_id(licence_id: str) -> str:
    LICENCE_TITLE_LOOKUP = {
        "notspecified": "Licence Not Specified",
        "odc-pddl": "Open Data Commons Public Domain Dedication and Licence (PDDL)",
        "odc-odbl": "Open Data Commons Open Database License (ODbL)",
        "odc-by": "Open Data Commons Attribution Licence",
        "cc-zero": "Creative Commons CCZero",
        "cc-by": "Creative Commons Attribution",
        "cc-by-sa": "Creative Commons Attribution Share-Alike",
        "gfdl": "GNU Free Documentation License",
        "ukclickusepsi": "UK Click Use PSI",
        "other-open": "Other (Open)",
        "other-pd": "Other (Public Domain)",
        "other-at": "Other (Attribution)",
        "ukcrown-withrights": "UK Crown Copyright with data.gov.uk rights",
        "hesa-withrights": "Higher Education Statistics Agency Copyright with data.gov.uk rights",
        "localauth-withrights": "Local Authority Copyright with data.gov.uk rights",
        "uk-ogl": "UK Open Government Licence (OGL)",
        "met-office-cp": "Non-Met Office UK Climate Projections Licence Agreement",
        "cc-nc": "Non-Creative Commons Non-Commercial (Any)",
        "ukcrown": "Non-UK Crown Copyright",
        "other-nc": "Non-Other (Non-Commercial)",
        "other-closed": "Non-Other (Not Open)",
        "bsd-license": "New and Simplified BSD licenses",
        "gpl-2.0": "GNU General Public License (GPL)",
        "gpl-3.0": "GNU General Public License version 3.0 (GPLv3)",
        "lgpl-2.1": 'GNU Library or "Lesser" General Public License (LGPL)',
        "mit-license": "MIT license",
        "afl-3.0": "Academic Free License 3.0 (AFL 3.0)",
        "apl1.0": "Adaptive Public License",
        "apache": "Apache Software License",
        "apache2.0": "Apache License, 2.0",
        "apsl-2.0": "Apple Public Source License",
        "artistic-license-2.0": "Artistic license 2.0",
        "attribution": "Attribution Assurance Licenses",
        "ca-tosl1.1": "Computer Associates Trusted Open Source License 1.1",
        "cddl1": "Common Development and Distribution License",
        "cpal_1.0": "Common Public Attribution License 1.0 (CPAL)",
        "cuaoffice": "CUA Office Public License Version 1.0",
        "eudatagrid": "EU DataGrid Software License",
        "eclipse-1.0": "Eclipse Public License",
        "ecl2": "Educational Community License, Version 2.0",
        "eiffel": "Eiffel Forum License",
        "ver2_eiffel": "Eiffel Forum License V2.0",
        "entessa": "Entessa Public License",
        "fair": "Fair License",
        "frameworx": "Frameworx License",
        "ibmpl": "IBM Public License",
        "intel-osl": "Intel Open Source License",
        "jabber-osl": "Jabber Open Source License",
        "lucent-plan9": "Lucent Public License (Plan9)",
        "lucent1.02": "Lucent Public License Version 1.02",
        "mitre": "MITRE Collaborative Virtual Workspace License (CVW License)",
        "motosoto": "Motosoto License",
        "mozilla": "Mozilla Public License 1.0 (MPL)",
        "mozilla1.1": "Mozilla Public License 1.1 (MPL)",
        "nasa1.3": "NASA Open Source Agreement 1.3",
        "naumen": "Naumen Public License",
        "nethack": "Nethack General Public License",
        "nokia": "Nokia Open Source License",
        "oclc2": "OCLC Research Public License 2.0",
        "opengroup": "Open Group Test Suite License",
        "osl-3.0": "Open Software License 3.0 (OSL 3.0)",
        "php": "PHP License",
        "pythonpl": "Python license",
        "PythonSoftFoundation": "Python Software Foundation License",
        "qtpl": "Qt Public License (QPL)",
        "real": "RealNetworks Public Source License V1.0",
        "rpl1.5": "Reciprocal Public License 1.5 (RPL1.5)",
        "ricohpl": "Ricoh Source Code Public License",
        "sleepycat": "Sleepycat License",
        "sun-issl": "Sun Industry Standards Source License (SISSL)",
        "sunpublic": "Sun Public License",
        "sybase": "Sybase Open Watcom Public License 1.0",
        "UoI-NCSA": "University of Illinois/NCSA Open Source License",
        "vovidapl": "Vovida Software License v. 1.0",
        "W3C": "W3C License",
        "wxwindows": "wxWindows Library License",
        "xnet": "X.Net License",
        "zpl": "Zope Public License",
        "zlib-license": "zlib/libpng license",
    }
    return LICENCE_TITLE_LOOKUP[licence_id] if licence_id in LICENCE_TITLE_LOOKUP else "Unknown License"
