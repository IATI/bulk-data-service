import datetime
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


def set_timestamp_tz_utc(date: datetime.datetime) -> datetime.datetime:
    return date.replace(tzinfo=datetime.timezone.utc)


def zip_data_as_single_file(filename: str, data: str) -> bytes:

    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w") as xml_zipped:
        xml_zipped.writestr(filename, data)

    return zip_buffer.getvalue()
