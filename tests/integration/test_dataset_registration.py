import pytest

from bulk_data_service.checker import checker_run
from helpers.helpers import get_and_clear_up_context  # noqa: F401


@pytest.mark.parametrize("http_status_code", ["400", "404", "500"])
def test_ckan_reg_url_400(get_and_clear_up_context, http_status_code):  # noqa: F811

    context = get_and_clear_up_context
    context["DATA_REGISTRY_BASE_URL"] = "http://localhost:3000/error-response/" + http_status_code

    datasets_in_bds = {}
    checker_run(context, datasets_in_bds)

    assert len(datasets_in_bds) == 0
