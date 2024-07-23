from bulk_data_service.checker import checker_run
from bulk_data_service.zipper import zipper_run
from helpers.helpers import get_and_clear_up_context  # noqa: F401
from helpers.helpers import get_number_xml_files_in_working_dir


def test_zip_creation_when_download_always_failed(get_and_clear_up_context):  # noqa: F811

    context = get_and_clear_up_context

    context["DATA_REGISTRY_BASE_URL"] = "http://localhost:3000/registration/datasets-03"
    datasets_in_bds = {}
    checker_run(context, datasets_in_bds)

    datasets_in_zip = {}
    zipper_run(context, datasets_in_zip, datasets_in_bds)

    assert len(datasets_in_zip) == 0

    assert get_number_xml_files_in_working_dir(context) == 0


def test_zip_creation_when_download_recently_failed(get_and_clear_up_context):  # noqa: F811

    context = get_and_clear_up_context

    context["DATA_REGISTRY_BASE_URL"] = "http://localhost:3000/registration/datasets-01"
    datasets_in_bds = {}
    checker_run(context, datasets_in_bds)

    # this is same dataset as above, only with a 404 URL
    context["DATA_REGISTRY_BASE_URL"] = "http://localhost:3000/registration/datasets-03"
    checker_run(context, datasets_in_bds)

    datasets_in_zip = {}
    zipper_run(context, datasets_in_zip, datasets_in_bds)

    assert len(datasets_in_zip) == 1

    assert get_number_xml_files_in_working_dir(context) == 1
