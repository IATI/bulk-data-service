import datetime
from typing import Any, Optional
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit

import chardet
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from config.bds_context import BDSContext


def add_qs_params_to_url(url: str, qs_params: dict) -> str:
    scheme, netloc, path, qs, fragment = urlsplit(url)
    new_qs_as_dict = parse_qs(qs) | qs_params
    new_qs_as_str = urlencode(new_qs_as_dict, doseq=True)
    return urlunsplit([scheme, netloc, path, new_qs_as_str, fragment])


def determine_response_encoding(download_response: requests.Response) -> str | None:
    detection_result = chardet.detect(download_response.content)
    return detection_result["encoding"]


def get_last_modified_header_if_exists(download_response: requests.Response) -> Optional[datetime.datetime]:
    last_modified_header = None
    if download_response.headers.get("Last-Modified", None) is not None:
        last_modified_header = parse_last_modified_header(download_response.headers.get("Last-Modified", ""))
    return last_modified_header


def parse_last_modified_header(last_modified_header: str) -> Optional[datetime.datetime]:
    last_modified_header_parsed = None
    try:
        last_modified_header_parsed = datetime.datetime.strptime(
            last_modified_header, "%a, %d %b %Y %H:%M:%S %Z"
        ).replace(tzinfo=datetime.timezone.utc)
    except ValueError:
        pass
    return last_modified_header_parsed


def get_requests_session(context: BDSContext) -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": "IATI Bulk Data Service {}".format(context["BULK_DATA_SERVICE_VERSION"])})
    retries = Retry(total=2, backoff_factor=0.1)
    session.mount("http://", HTTPAdapter(max_retries=retries))
    session.mount("https://", HTTPAdapter(max_retries=retries))
    return session


def http_get_json(session: requests.Session, url: str, timeout: int = 30, exception_on_non_200: bool = True) -> Any:

    response = session.get(url=url, timeout=timeout)

    if exception_on_non_200 and response.status_code != 200:
        raise RuntimeError(
            "HTTP status code {} and reason {} when fetching {}".format(response.status_code, response.reason, url)
        )

    return response.json()


def http_head_dataset(session: requests.Session, url: str, timeout: int = 10, retries: int = 2) -> requests.Response:

    response = session.head(url=url, timeout=timeout, allow_redirects=True, verify=False)

    if response.status_code != 200:
        raise RuntimeError(
            {
                "summary_message": "HEAD request failed with non-200 status",
                "http_headers": dict(response.headers),
                "http_method": "HEAD",
                "http_reason": response.reason,
                "http_status": response.status_code,
                "url": response.url,
            }
        )

    return response


def http_download_dataset(
    session: requests.Session, url: str, timeout: int = 25, retries: int = 2
) -> requests.Response:

    response = session.get(url=url, timeout=timeout, allow_redirects=True, verify=False)

    if response.status_code != 200:
        raise RuntimeError(
            {
                "summary_message": "HTTP GET request failed with non-200 status",
                "http_headers": dict(response.headers),
                "http_method": "GET",
                "http_status": response.status_code,
                "http_reason": response.reason,
                "url": response.url,
            }
        )

    return response
