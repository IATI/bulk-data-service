import datetime
import glob
import hashlib
import io
import re
import zipfile


def get_hash(content: str) -> str:
    hasher = hashlib.sha1()
    hasher = hashlib.sha1()
    hasher.update(content.encode("utf-8"))
    return hasher.hexdigest()


def get_hash_excluding_generated_timestamp(content: str) -> str:
    hasher = hashlib.sha1()
    content_to_hash = re.sub(r'generated-datetime="[^"]+"', "", content)

    hasher = hashlib.sha1()
    hasher.update(content_to_hash.encode("utf-8"))
    return hasher.hexdigest()


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


def zip_data_as_single_file(filename: str, data: str) -> bytes:

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
