import uuid

from bulk_data_service.checker import checker_run
from helpers.helpers import get_and_clear_up_context  # noqa: F401
from utilities.db import get_organisations_in_bds


def test_add_all_organisations_from_url_to_db(get_and_clear_up_context):  # noqa: F811

    context = get_and_clear_up_context

    checker_run(context, {})

    organisations_in_db = get_organisations_in_bds(context)

    assert len(organisations_in_db) == 4


def test_add_organisation_fields_to_db(get_and_clear_up_context):  # noqa: F811

    context = get_and_clear_up_context

    checker_run(context, {})

    organisations_in_db = get_organisations_in_bds(context)

    assert uuid.UUID("4f0f8498-20d2-4ca5-a20f-f441eedb1d4f") in organisations_in_db

    organisation = organisations_in_db[uuid.UUID("4f0f8498-20d2-4ca5-a20f-f441eedb1d4f")]

    assert organisation["short_id"] == "test_org_a"
    assert organisation["iati_identifier"] == "TEST_ORG_A"
    assert organisation["human_readable_name"] == "Test Organisation A"


def test_update_organisation_fields_in_db(get_and_clear_up_context):  # noqa: F811

    context = get_and_clear_up_context

    checker_run(context, {})

    organisations_in_db = get_organisations_in_bds(context)

    # original values
    assert uuid.UUID("4f0f8498-20d2-4ca5-a20f-f441eedb1d4f") in organisations_in_db
    organisation = organisations_in_db[uuid.UUID("4f0f8498-20d2-4ca5-a20f-f441eedb1d4f")]
    assert organisation["short_id"] == "test_org_a"
    assert organisation["iati_identifier"] == "TEST_ORG_A"
    assert organisation["human_readable_name"] == "Test Organisation A"

    # re-run with updated values
    context["DATA_REGISTRY_PUBLISHER_METADATA_URL"] = "http://localhost:3000/registration/ckan-publishers-02"
    checker_run(context, {})

    organisations_in_db = get_organisations_in_bds(context)

    # updated values
    assert uuid.UUID("4f0f8498-20d2-4ca5-a20f-f441eedb1d4f") in organisations_in_db
    organisation = organisations_in_db[uuid.UUID("4f0f8498-20d2-4ca5-a20f-f441eedb1d4f")]
    assert organisation["short_id"] == "test_org_a_updated"
    assert organisation["iati_identifier"] == "TEST_ORG_A_UPDATED"
    assert organisation["human_readable_name"] == "Test Organisation A Updated"


def test_delete_organisation_fields_from_db(get_and_clear_up_context):  # noqa: F811

    context = get_and_clear_up_context

    checker_run(context, {})

    organisations_in_db = get_organisations_in_bds(context)

    # original values
    assert uuid.UUID("4f0f8498-20d2-4ca5-a20f-f441eedb1d4f") in organisations_in_db

    # re-run with updated values
    context["DATA_REGISTRY_PUBLISHER_METADATA_URL"] = "http://localhost:3000/registration/ckan-publishers-03"
    checker_run(context, {})

    organisations_in_db = get_organisations_in_bds(context)

    assert len(organisations_in_db) == 3
    assert uuid.UUID("4f0f8498-20d2-4ca5-a20f-f441eedb1d4f") not in organisations_in_db
