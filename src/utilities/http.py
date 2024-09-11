import datetime
from typing import Any, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry


def parse_last_modified_header(last_modified_header: str) -> Optional[datetime.datetime]:
    last_modified_header_parsed = None
    try:
        last_modified_header_parsed = datetime.datetime.strptime(
            last_modified_header, "%a, %d %b %Y %H:%M:%S %Z"
        ).replace(tzinfo=datetime.timezone.utc)
    except ValueError:
        pass
    return last_modified_header_parsed


def get_requests_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": "IATI Bulk Data Service 0.1"})
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
                "message": "HEAD request failed with non-200 status",
                "url": response.url,
                "http_method": "HEAD",
                "http_status_code": response.status_code,
                "http_reason": response.reason,
                "http_headers": dict(response.headers),
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
                "message": "HTTP GET request failed with non-200 status",
                "url": response.url,
                "http_method": "GET",
                "http_status_code": response.status_code,
                "http_reason": response.reason,
                "http_headers": dict(response.headers),
            }
        )

    return response
