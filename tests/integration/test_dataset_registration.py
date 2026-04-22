import json
import uuid
from unittest import mock

import pytest
from libsuitecrm import SuiteCRM

from bulk_data_service.checker import checker_run
from dataset_registration.iati_registry_ckan import get_publisher_metadata_as_str
from dataset_registration.registration_proxy import fetch_datasets_metadata, fetch_reporting_orgs_metadata
from helpers.helpers import get_and_clear_up_context  # noqa: F401
from utilities.misc import get_timestamp


@pytest.mark.parametrize("http_status_code", ["400", "404", "500"])
def test_ckan_registry_url_400(get_and_clear_up_context, http_status_code):  # noqa: F811

    context = get_and_clear_up_context
    context["DATA_REGISTRY_BASE_URL"] = "http://localhost:3000/error-response/" + http_status_code

    with pytest.raises(RuntimeError):
        datasets_in_bds = {}
        checker_run(context, datasets_in_bds)

    assert len(datasets_in_bds) == 0


def test_ckan_registry_get_metadata_known_publisher(get_and_clear_up_context):  # noqa: F811

    expected = json.dumps(
        {
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
            "users": [{"capacity": "admin", "name": "3-f_international"}],
            "tags": [],
            "groups": [],
        }
    )

    context = get_and_clear_up_context

    context["DATA_REGISTRY_PUBLISHER_METADATA_URL"] = "http://localhost:3000/registration/ckan-publishers"

    reporting_orgs = fetch_reporting_orgs_metadata(context, get_timestamp())

    publisher_metadata_str = get_publisher_metadata_as_str(reporting_orgs, "1a3e3f42-6704-4adf-897a-9bdf5b854a00")

    assert publisher_metadata_str == expected


def test_ckan_registry_get_metadata_unknown_publisher(get_and_clear_up_context):  # noqa: F811

    context = get_and_clear_up_context

    context["DATA_REGISTRY_PUBLISHER_METADATA_URL"] = "http://localhost:3000/registration/ckan-publishers"

    reporting_orgs = fetch_reporting_orgs_metadata(context, get_timestamp())

    # this is an unknown organisation id
    publisher_metadata_str = get_publisher_metadata_as_str(reporting_orgs, "12345678-9000-4adf-897a-9bdf5b854a00")

    assert publisher_metadata_str == "{}"


def test_suitecrm_registry_returns_correct_reporting_orgs(get_and_clear_up_context):  # noqa: F811
    context = get_and_clear_up_context

    context["DATA_REGISTRATION"] = "suitecrm-registry"

    mock_crm = mock.Mock(spec=SuiteCRM)

    mock_crm.get_all_records.return_value = json.load(
        open("tests/artifacts/libsuitecrm-responses/reporting-orgs-01-four-orgs.json")
    )

    context.service_factory.get_suitecrm_client.return_value = mock_crm

    reporting_orgs = fetch_reporting_orgs_metadata(context, get_timestamp())

    assert len(reporting_orgs) == 4

    assert uuid.UUID("3544dcef-96a4-b63e-7eb6-6900a833d003") in reporting_orgs
    assert uuid.UUID("419427db-b2cc-5781-eba9-68ecc7d84982") in reporting_orgs
    assert uuid.UUID("48a2c5ee-356e-e838-30ac-6901fa9d1fb3") in reporting_orgs
    assert uuid.UUID("552376ae-2aa7-98ab-d800-68daa9bfeb4a") in reporting_orgs


def test_suitecrm_registry_conversion_of_registry_reporting_orgs(get_and_clear_up_context):  # noqa: F811
    context = get_and_clear_up_context

    context["DATA_REGISTRATION"] = "suitecrm-registry"

    mock_crm = mock.Mock(spec=SuiteCRM)

    mock_crm.get_all_records.return_value = json.load(
        open("tests/artifacts/libsuitecrm-responses/reporting-orgs-01-four-orgs.json")
    )

    context.service_factory.get_suitecrm_client.return_value = mock_crm

    reporting_orgs = fetch_reporting_orgs_metadata(context, get_timestamp())

    ro_1 = reporting_orgs[uuid.UUID("3544dcef-96a4-b63e-7eb6-6900a833d003")]

    assert ro_1["data_portal_url"] == "https://www.example.org/data-portal"
    assert ro_1["default_licence_id"] == "gpl-3.0"
    assert ro_1["description"] == "Eaque eaque nostrum quia illum ipsum."
    assert ro_1["exclusions_policy_url"] == "https://www.example.org/exclusions-policy"
    assert ro_1["first_publication_date"] is None
    assert ro_1["hq_country"] == "GB"
    assert ro_1["human_readable_name"] == "Gov Agency 1234"
    assert ro_1["organisation_identifier"] == "GOV-AGENCY-AID-1234"
    assert ro_1["organisation_type"] == "10"
    assert ro_1["region"] == "89"
    assert ro_1["reporting_source_type"] == "primary_source"
    assert ro_1["short_name"] == "gov-agency-aid-1234"
    assert ro_1["website"] == "https://www.example.org/"


def test_suitecrm_registry_returns_correct_datasets(get_and_clear_up_context):  # noqa: F811
    context = get_and_clear_up_context

    context["DATA_REGISTRATION"] = "suitecrm-registry"

    mock_crm = mock.Mock(spec=SuiteCRM)

    mock_crm.get_all_records.return_value = json.load(
        open("tests/artifacts/libsuitecrm-responses/reporting-orgs-01-four-orgs.json")
    )

    context.service_factory.get_suitecrm_client.return_value = mock_crm

    reporting_orgs = fetch_reporting_orgs_metadata(context, get_timestamp())

    mock_crm.get_all_records.return_value = json.load(
        open("tests/artifacts/libsuitecrm-responses/datasets-01-five-sample-datasets.json")
    )

    context.service_factory.get_suitecrm_client.return_value = mock_crm

    datasets = fetch_datasets_metadata(context, reporting_orgs, get_timestamp())

    assert len(datasets) == 5

    assert uuid.UUID("4ad2b196-aa31-983e-93d9-68ecf476a2c6") in datasets
    assert uuid.UUID("6f0616d2-1a3a-0545-a495-68ecf41bb123") in datasets
    assert uuid.UUID("74fc8ebd-3bb0-65fa-aac7-68ecc75b91af") in datasets
    assert uuid.UUID("7ba70b0e-0f22-3a7d-89aa-68ff9a882f74") in datasets
    assert uuid.UUID("eb6c0407-4d72-c9e7-52c6-6900b0a32eae") in datasets


def test_suitecrm_registry_conversion_of_registry_dataset(get_and_clear_up_context):  # noqa: F811
    context = get_and_clear_up_context

    context["DATA_REGISTRATION"] = "suitecrm-registry"

    mock_crm = mock.Mock(spec=SuiteCRM)

    mock_crm.get_all_records.return_value = json.load(
        open("tests/artifacts/libsuitecrm-responses/reporting-orgs-01-four-orgs.json")
    )

    context.service_factory.get_suitecrm_client.return_value = mock_crm

    reporting_orgs = fetch_reporting_orgs_metadata(context, get_timestamp())

    mock_crm.get_all_records.return_value = json.load(
        open("tests/artifacts/libsuitecrm-responses/datasets-01-five-sample-datasets.json")
    )

    context.service_factory.get_suitecrm_client.return_value = mock_crm

    datasets = fetch_datasets_metadata(context, reporting_orgs, get_timestamp())

    dataset_1 = datasets[uuid.UUID("4ad2b196-aa31-983e-93d9-68ecf476a2c6")]

    assert dataset_1["licence_id"] == ""
    assert dataset_1["reporting_org_id"] == uuid.UUID("3544dcef-96a4-b63e-7eb6-6900a833d003")
    assert dataset_1["reporting_org_short_name"] == "gov-agency-aid-1234"
    assert dataset_1["short_name"] == "aid-agency-02-europe"
    assert dataset_1["source_url"] == "https://example.com/europe-dataset.xml"
