import datetime
import uuid

from bulk_data_service.checker import checker_run
from helpers.data_helpers import check_registration_service_refreshed_datetime
from helpers.helpers import get_and_clear_up_context  # noqa: F401
from utilities.db import get_datasets_in_bds, get_reporting_orgs_in_bds


def test_add_all_reporting_orgs_from_url_to_db(get_and_clear_up_context):  # noqa: F811

    context = get_and_clear_up_context

    checker_run(context, {})

    reporting_orgs_in_db = get_reporting_orgs_in_bds(context)

    assert len(reporting_orgs_in_db) == 4


def test_add_reporting_org_to_db(get_and_clear_up_context):  # noqa: F811

    context = get_and_clear_up_context

    context["DATA_REGISTRY_PUBLISHER_METADATA_URL"] = (
        "http://localhost:3000/ckan-registration/reporting-orgs-01-four-orgs"
    )
    checker_run(context, {})

    reporting_orgs_in_db = get_reporting_orgs_in_bds(context)

    assert uuid.UUID("ea055d99-f7e9-456f-9f99-963e95493c1b") in reporting_orgs_in_db

    reporting_org = reporting_orgs_in_db[uuid.UUID("ea055d99-f7e9-456f-9f99-963e95493c1b")]

    assert reporting_org["created_date"] is None
    assert reporting_org["data_portal_url"] == "http://www.example.com/data_portal_test_a.html"
    assert reporting_org["default_licence_id"] == "gpl-3.0"
    assert reporting_org["description"] == "Eligendi qui ab voluptate enim."
    assert reporting_org["exclusions_policy_url"] is None
    assert reporting_org["first_publication_date"] == datetime.datetime.fromisoformat("2022-02-04T13:51:36+00:00")
    assert reporting_org["hq_country"] == "GB"
    assert reporting_org["human_readable_name"] == "Test Foundation A"
    assert reporting_org["organisation_identifier"] == "TEST-A-JHG-0123456"
    assert reporting_org["organisation_type"] == "23"
    assert reporting_org["region"] is None
    assert reporting_org["reporting_source_type"] == "primary-source"
    assert reporting_org["short_name"] == "test_foundation_a"
    assert reporting_org["website"] == "http://www.example.com/foundation_a"

    check_registration_service_refreshed_datetime(reporting_org)


def test_add_reporting_org_to_db_org_with_missing_fields(get_and_clear_up_context):  # noqa: F811
    """Tests creation of a reporting_org for CKAN Registry missing fields entry

    The CKAN Registry sometimes returns entries without the following keys (as
    opposed to an entry with the key and a null entry): data_portal_url,
    first_publication_date, reporting_source_type, website. This test checks
    those cases are handled correctly."""

    context = get_and_clear_up_context

    context["DATA_REGISTRY_PUBLISHER_METADATA_URL"] = (
        "http://localhost:3000/ckan-registration/reporting-orgs-02-four-orgs-all-modified"
    )
    checker_run(context, {})

    reporting_orgs_in_db = get_reporting_orgs_in_bds(context)

    assert uuid.UUID("1a3e3f42-6704-4adf-897a-9bdf5b854a00") in reporting_orgs_in_db

    reporting_org = reporting_orgs_in_db[uuid.UUID("1a3e3f42-6704-4adf-897a-9bdf5b854a00")]

    assert reporting_org["data_portal_url"] is None
    assert reporting_org["first_publication_date"] is None
    assert reporting_org["reporting_source_type"] is None
    assert reporting_org["website"] is None

    check_registration_service_refreshed_datetime(reporting_org)


def test_update_reporting_org_in_db(get_and_clear_up_context):  # noqa: F811

    context = get_and_clear_up_context

    context["DATA_REGISTRY_PUBLISHER_METADATA_URL"] = (
        "http://localhost:3000/ckan-registration/reporting-orgs-01-four-orgs"
    )
    checker_run(context, {})

    # re-run from CKAN Registry response containing updated values
    context["DATA_REGISTRY_PUBLISHER_METADATA_URL"] = (
        "http://localhost:3000/ckan-registration/reporting-orgs-02-four-orgs-all-modified"
    )
    checker_run(context, {})

    reporting_orgs_in_db = get_reporting_orgs_in_bds(context)

    # updated values
    assert uuid.UUID("ea055d99-f7e9-456f-9f99-963e95493c1b") in reporting_orgs_in_db
    reporting_org = reporting_orgs_in_db[uuid.UUID("ea055d99-f7e9-456f-9f99-963e95493c1b")]
    assert reporting_org["created_date"] is None
    assert reporting_org["data_portal_url"] == "http://www.example.com/data_portal_test_a_mod.html"
    assert reporting_org["default_licence_id"] == "cc-by"
    assert reporting_org["description"] == "Eligendi qui ab voluptate enim. Mod."
    assert reporting_org["first_publication_date"] == datetime.datetime.fromisoformat("2022-02-05T13:51:36+00:00")
    assert reporting_org["hq_country"] == "DE"
    assert reporting_org["human_readable_name"] == "Test Foundation A Mod"
    assert reporting_org["organisation_identifier"] == "TEST-A-JHG-0123456-MOD"
    assert reporting_org["organisation_type"] == "60"
    assert reporting_org["reporting_source_type"] == "secondary-source"
    assert reporting_org["short_name"] == "test_foundation_a_mod"
    assert reporting_org["website"] == "http://www.example.com/foundation_a/mod"


def test_delete_reporting_org_from_db_01_no_datasets(get_and_clear_up_context):  # noqa: F811
    """Test the deletion of a reporting org that has no datasets"""

    context = get_and_clear_up_context

    # contains a single dataset belonging to reporting org ea055d99-f7e9-456f-9f99-963e95493c1b
    context["DATA_REGISTRY_BASE_URL"] = "http://localhost:3000/ckan-registration/datasets-01-1-dataset"
    context["DATA_REGISTRY_PUBLISHER_METADATA_URL"] = (
        "http://localhost:3000/ckan-registration/reporting-orgs-01-four-orgs"
    )
    checker_run(context, {})

    reporting_orgs_in_db = get_reporting_orgs_in_bds(context)

    # this is test_organisation_d in the reporting-orgs-01-four-orgs.json artifact, but doesn't exist in
    # reporting-orgs-03-three-orgs.json
    assert uuid.UUID("373cd7dc-114b-4a91-a63f-cb2e25cd1249") in reporting_orgs_in_db

    # re-run with updated values
    context["DATA_REGISTRY_PUBLISHER_METADATA_URL"] = (
        "http://localhost:3000/ckan-registration/reporting-orgs-03-three-orgs"
    )
    checker_run(context, {})

    reporting_orgs_in_db = get_reporting_orgs_in_bds(context)

    assert len(reporting_orgs_in_db) == 3
    assert uuid.UUID("373cd7dc-114b-4a91-a63f-cb2e25cd1249") not in reporting_orgs_in_db


def test_delete_reporting_org_from_db_02_associated_datasets(get_and_clear_up_context):  # noqa: F811
    """Test the deletion of a reporting org that has datasets"""

    context = get_and_clear_up_context

    # contains a two datasets, one on reporting org ea055d99-f7e9-456f-9f99-963e95493c1b and the other
    # on 373cd7dc-114b-4a91-a63f-cb2e25cd1249, which is the reporting org we attempt to delete
    context["DATA_REGISTRY_BASE_URL"] = "http://localhost:3000/ckan-registration/datasets-02-2-datasets"
    context["DATA_REGISTRY_PUBLISHER_METADATA_URL"] = (
        "http://localhost:3000/ckan-registration/reporting-orgs-01-four-orgs"
    )
    checker_run(context, {})

    reporting_orgs_in_db = get_reporting_orgs_in_bds(context)

    # this is test_organisation_a in the reporting-orgs-01-four-orgs.json
    # artifact, but doesn't exist in reporting-orgs-03-three-orgs.json
    assert uuid.UUID("373cd7dc-114b-4a91-a63f-cb2e25cd1249") in reporting_orgs_in_db

    # re-run with updated values
    context["DATA_REGISTRY_BASE_URL"] = "http://localhost:3000/ckan-registration/datasets-01-1-dataset"
    context["DATA_REGISTRY_PUBLISHER_METADATA_URL"] = (
        "http://localhost:3000/ckan-registration/reporting-orgs-03-three-orgs"
    )
    checker_run(context, {})

    reporting_orgs_in_db = get_reporting_orgs_in_bds(context)

    datasets_in_db = get_datasets_in_bds(context)

    # check the reporting org has gone
    assert len(reporting_orgs_in_db) == 3
    assert uuid.UUID("373cd7dc-114b-4a91-a63f-cb2e25cd1249") not in reporting_orgs_in_db

    # now check that its associated dataset has gone
    datasets_in_db = get_datasets_in_bds(context)
    assert uuid.UUID("90f4282f-9ac5-4385-804d-1a377f5b57be") not in datasets_in_db


def test_delete_reporting_org_from_db_03_orphaned_datasets_in_registry(get_and_clear_up_context):  # noqa: F811

    context = get_and_clear_up_context

    # contains a two datasets, one on reporting org ea055d99-f7e9-456f-9f99-963e95493c1b and the other
    # on 373cd7dc-114b-4a91-a63f-cb2e25cd1249, which is the reporting org we attempt to delete
    context["DATA_REGISTRY_BASE_URL"] = "http://localhost:3000/ckan-registration/datasets-02-2-datasets"
    context["DATA_REGISTRY_PUBLISHER_METADATA_URL"] = (
        "http://localhost:3000/ckan-registration/reporting-orgs-01-four-orgs"
    )
    checker_run(context, {})

    reporting_orgs_in_db = get_reporting_orgs_in_bds(context)

    # this is test_organisation_a in the reporting-orgs-01-four-orgs.json
    # artifact, but doesn't exist in reporting-orgs-03-three-orgs.json
    assert uuid.UUID("373cd7dc-114b-4a91-a63f-cb2e25cd1249") in reporting_orgs_in_db

    # re-run with updated values, but without changing the dataset source, so
    # the BDS will get an orphaned dataset in the list of datasets, which it
    # should then ignore
    context["DATA_REGISTRY_PUBLISHER_METADATA_URL"] = (
        "http://localhost:3000/ckan-registration/reporting-orgs-03-three-orgs"
    )
    checker_run(context, {})

    reporting_orgs_in_db = get_reporting_orgs_in_bds(context)

    datasets_in_db = get_datasets_in_bds(context)

    # check the reporting org has gone
    assert len(reporting_orgs_in_db) == 3
    assert uuid.UUID("373cd7dc-114b-4a91-a63f-cb2e25cd1249") not in reporting_orgs_in_db

    # now check that its associated dataset has gone
    datasets_in_db = get_datasets_in_bds(context)
    assert uuid.UUID("90f4282f-9ac5-4385-804d-1a377f5b57be") not in datasets_in_db
