import uuid

from bulk_data_service.checker import checker_run
from helpers.helpers import get_and_clear_up_context  # noqa: F401
from utilities.db import get_reporting_orgs_in_bds


def test_add_all_reporting_orgs_from_url_to_db(get_and_clear_up_context):  # noqa: F811

    context = get_and_clear_up_context

    checker_run(context, {})

    reporting_orgs_in_db = get_reporting_orgs_in_bds(context)

    assert len(reporting_orgs_in_db) == 4


def test_add_reporting_org_fields_to_db(get_and_clear_up_context):  # noqa: F811

    context = get_and_clear_up_context

    checker_run(context, {})

    reporting_orgs_in_db = get_reporting_orgs_in_bds(context)

    assert uuid.UUID("ea055d99-f7e9-456f-9f99-963e95493c1b") in reporting_orgs_in_db

    reporting_org = reporting_orgs_in_db[uuid.UUID("ea055d99-f7e9-456f-9f99-963e95493c1b")]

    assert reporting_org["short_name"] == "test_foundation_a"
    assert reporting_org["iati_identifier"] == "TEST_FOUNDATION_A"
    assert reporting_org["human_readable_name"] == "Test Foundation A"


def test_update_reporting_org_fields_in_db(get_and_clear_up_context):  # noqa: F811

    context = get_and_clear_up_context

    checker_run(context, {})

    reporting_orgs_in_db = get_reporting_orgs_in_bds(context)

    # original values
    assert uuid.UUID("ea055d99-f7e9-456f-9f99-963e95493c1b") in reporting_orgs_in_db
    reporting_org = reporting_orgs_in_db[uuid.UUID("ea055d99-f7e9-456f-9f99-963e95493c1b")]
    assert reporting_org["short_name"] == "test_foundation_a"
    assert reporting_org["iati_identifier"] == "TEST_FOUNDATION_A"
    assert reporting_org["human_readable_name"] == "Test Foundation A"

    # re-run with updated values
    context["DATA_REGISTRY_PUBLISHER_METADATA_URL"] = "http://localhost:3000/registration/ckan-publishers-02"
    checker_run(context, {})

    reporting_orgs_in_db = get_reporting_orgs_in_bds(context)

    # updated values
    assert uuid.UUID("ea055d99-f7e9-456f-9f99-963e95493c1b") in reporting_orgs_in_db
    reporting_org = reporting_orgs_in_db[uuid.UUID("ea055d99-f7e9-456f-9f99-963e95493c1b")]
    assert reporting_org["short_name"] == "test_foundation_a_updated"
    assert reporting_org["iati_identifier"] == "TEST_FOUNDATION_A_UPDATED"
    assert reporting_org["human_readable_name"] == "Test Foundation A Updated"


def test_delete_reporting_org_fields_from_db(get_and_clear_up_context):  # noqa: F811

    context = get_and_clear_up_context

    checker_run(context, {})

    reporting_orgs_in_db = get_reporting_orgs_in_bds(context)

    # original values
    assert uuid.UUID("ea055d99-f7e9-456f-9f99-963e95493c1b") in reporting_orgs_in_db

    # re-run with updated values
    context["DATA_REGISTRY_PUBLISHER_METADATA_URL"] = "http://localhost:3000/registration/ckan-publishers-03"
    checker_run(context, {})

    reporting_orgs_in_db = get_reporting_orgs_in_bds(context)

    assert len(reporting_orgs_in_db) == 3
    assert uuid.UUID("ea055d99-f7e9-456f-9f99-963e95493c1b") not in reporting_orgs_in_db
