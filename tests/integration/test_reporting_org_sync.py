import uuid

from bulk_data_service.checker import checker_run
from helpers.helpers import get_and_clear_up_context  # noqa: F401
from utilities.db import get_datasets_in_bds, get_reporting_orgs_in_bds


def test_add_all_reporting_orgs_from_url_to_db(get_and_clear_up_context):  # noqa: F811

    context = get_and_clear_up_context

    checker_run(context, {})

    reporting_orgs_in_db = get_reporting_orgs_in_bds(context)

    assert len(reporting_orgs_in_db) == 4


def test_add_reporting_org_to_db(get_and_clear_up_context):  # noqa: F811

    context = get_and_clear_up_context

    checker_run(context, {})

    reporting_orgs_in_db = get_reporting_orgs_in_bds(context)

    assert uuid.UUID("ea055d99-f7e9-456f-9f99-963e95493c1b") in reporting_orgs_in_db

    reporting_org = reporting_orgs_in_db[uuid.UUID("ea055d99-f7e9-456f-9f99-963e95493c1b")]

    assert reporting_org["short_name"] == "test_foundation_a"
    assert reporting_org["iati_identifier"] == "TEST_FOUNDATION_A"
    assert reporting_org["human_readable_name"] == "Test Foundation A"


def test_update_reporting_org_in_db(get_and_clear_up_context):  # noqa: F811

    context = get_and_clear_up_context

    context["DATA_REGISTRY_PUBLISHER_METADATA_URL"] = (
        "http://localhost:3000/ckan-registration/reporting-orgs-01-four-orgs"
    )
    checker_run(context, {})

    reporting_orgs_in_db = get_reporting_orgs_in_bds(context)

    # original values
    assert uuid.UUID("ea055d99-f7e9-456f-9f99-963e95493c1b") in reporting_orgs_in_db
    reporting_org = reporting_orgs_in_db[uuid.UUID("ea055d99-f7e9-456f-9f99-963e95493c1b")]
    assert reporting_org["short_name"] == "test_foundation_a"
    assert reporting_org["iati_identifier"] == "TEST-A-JHG-0123456"
    assert reporting_org["human_readable_name"] == "Test Foundation A"

    # re-run with updated values
    context["DATA_REGISTRY_PUBLISHER_METADATA_URL"] = (
        "http://localhost:3000/ckan-registration/reporting-orgs-02-four-orgs-all-modified"
    )
    checker_run(context, {})

    reporting_orgs_in_db = get_reporting_orgs_in_bds(context)

    # updated values
    assert uuid.UUID("ea055d99-f7e9-456f-9f99-963e95493c1b") in reporting_orgs_in_db
    reporting_org = reporting_orgs_in_db[uuid.UUID("ea055d99-f7e9-456f-9f99-963e95493c1b")]
    assert reporting_org["short_name"] == "test_foundation_a_mod"
    assert reporting_org["iati_identifier"] == "TEST-A-JHG-0123456-MOD"
    assert reporting_org["human_readable_name"] == "Test Foundation A Mod"


def test_delete_reporting_org_from_db_01_no_datasets(get_and_clear_up_context):  # noqa: F811

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

    context = get_and_clear_up_context

    # contains a two datasets, one on reporting org ea055d99-f7e9-456f-9f99-963e95493c1b and the other
    # on 373cd7dc-114b-4a91-a63f-cb2e25cd1249, which is the reporting org we attempt to delete
    context["DATA_REGISTRY_BASE_URL"] = "http://localhost:3000/ckan-registration/datasets-02-2-datasets"
    context["DATA_REGISTRY_PUBLISHER_METADATA_URL"] = (
        "http://localhost:3000/ckan-registration/reporting-orgs-01-four-orgs"
    )
    checker_run(context, {})

    reporting_orgs_in_db = get_reporting_orgs_in_bds(context)

    # this is test_organisation_a in the reporting-orgs-01-four-orgs.json artifact, but doesn't exist in
    # reporting-orgs-03-three-orgs.json
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

    # this is test_organisation_a in the reporting-orgs-01-four-orgs.json artifact, but doesn't exist in
    # reporting-orgs-03-three-orgs.json
    assert uuid.UUID("373cd7dc-114b-4a91-a63f-cb2e25cd1249") in reporting_orgs_in_db

    # re-run with updated values, but without changing the dataset source, so the BDS will get an orphaned dataset in the
    # list of datasets, which it should then ignore
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
