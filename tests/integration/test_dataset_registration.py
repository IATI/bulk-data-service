import json

import pytest

from bulk_data_service.checker import checker_run
from dataset_registration.iati_registry_ckan import get_publisher_metadata_as_str
from helpers.helpers import get_and_clear_up_context  # noqa: F401
from utilities.http import get_requests_session


@pytest.mark.parametrize("http_status_code", ["400", "404", "500"])
def test_ckan_registry_url_400(get_and_clear_up_context, http_status_code):  # noqa: F811

    context = get_and_clear_up_context
    context["DATA_REGISTRY_BASE_URL"] = "http://localhost:3000/error-response/" + http_status_code

    datasets_in_bds = {}
    checker_run(context, datasets_in_bds)

    assert len(datasets_in_bds) == 0


def test_ckan_registry_get_metadata_known_publisher(get_and_clear_up_context):  # noqa: F811

    expected = json.dumps({
      "description": "",
      "id": "1a3e3f42-6704-4adf-897a-9bdf5b854a00",
      "image_display_url": "",
      "image_url": "",
      "is_organization": True,
      "license_id": "notspecified",
      "name": "3fi",
      "num_followers": 0,
      "package_count": 1,
      "publisher_agencies": "",
      "publisher_constraints": "",
      "publisher_contact": "3F\r\nKampmannsgade 4\r\nDK-1790 Copenhagen V\r\nDenmark ",
      "publisher_contact_email": "jesper.nielsen@3f.dk",
      "publisher_country": "DK",
      "publisher_data_quality": "",
      "publisher_description": "",
      "publisher_field_exclusions": "",
      "publisher_first_publish_date": "",
      "publisher_frequency": "",
      "publisher_frequency_select": "not_specified",
      "publisher_iati_id": "DK-CVR-31378028",
      "publisher_implementation_schedule": "",
      "publisher_organization_type": "22",
      "publisher_record_exclusions": "",
      "publisher_refs": "",
      "publisher_segmentation": "",
      "publisher_source_type": "primary_source",
      "publisher_thresholds": "",
      "publisher_timeliness": "",
      "publisher_ui": "",
      "publisher_units": "",
      "publisher_url": "https://tema.3f.dk/international ",
      "state": "active",
      "title": "3F International",
      "type": "organization",
      "users": [
        {
          "capacity": "admin",
          "name": "3-f_international"
        }
      ],
      "tags": [

      ],
      "groups": [

      ]
    })

    context = get_and_clear_up_context

    context["DATA_REGISTRY_PUBLISHER_METADATA_URL"] = "http://localhost:3000/registration/ckan-publishers"

    session = get_requests_session()

    publisher_metadata_str = get_publisher_metadata_as_str(context, session, "3fi")

    assert publisher_metadata_str == expected


def test_ckan_registry_get_metadata_unknown_publisher(get_and_clear_up_context):  # noqa: F811

    context = get_and_clear_up_context

    context["DATA_REGISTRY_PUBLISHER_METADATA_URL"] = "http://localhost:3000/registration/ckan-publishers"

    session = get_requests_session()

    publisher_metadata_str = get_publisher_metadata_as_str(context, session, "unknown_publisher")

    assert publisher_metadata_str == "{}"
