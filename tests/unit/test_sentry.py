import logging
from unittest import mock

from config.config import get_secret_variable_names
from config.sentry import DEFAULT_TRACES_SAMPLE_RATE, UNCONFIGURED_ENVIRONMENT, initialise_sentry

BASE_CONFIG = {
    "SENTRY_DSN": "https://examplekey@o0.ingest.sentry.io/1",
    "SENTRY_ENVIRONMENT": "dev",
    "SENTRY_TRACES_SAMPLE_RATE": "0.25",
    "BULK_DATA_SERVICE_VERSION": "1.2.3",
}


def initialise_with(config_overrides: dict) -> dict:
    """Initialises Sentry with the base config plus the given overrides, and
    returns the keyword arguments which would have been passed to the SDK."""

    with mock.patch("config.sentry.sentry_sdk") as sentry_sdk:
        initialise_sentry(BASE_CONFIG | config_overrides, "checker", logging.getLogger("test"))

        if not sentry_sdk.init.called:
            return {}

        return sentry_sdk.init.call_args.kwargs


def test_sentry_not_initialised_when_no_dsn_configured():

    assert initialise_with({"SENTRY_DSN": ""}) == {}


def test_sentry_initialised_with_dsn_environment_and_release():

    init_args = initialise_with({})

    assert init_args["dsn"] == BASE_CONFIG["SENTRY_DSN"]
    assert init_args["environment"] == "dev"
    assert init_args["release"] == "bulk-data-service@1.2.3"


def test_sentry_environment_not_reported_as_production_when_unconfigured():

    assert initialise_with({"SENTRY_ENVIRONMENT": ""})["environment"] == UNCONFIGURED_ENVIRONMENT


def test_sentry_does_not_send_personally_identifying_information():

    assert initialise_with({})["send_default_pii"] is False


def test_sentry_ignores_interrupts():

    assert KeyboardInterrupt in initialise_with({})["ignore_errors"]


def test_sentry_tags_events_with_the_operation():

    with mock.patch("config.sentry.sentry_sdk") as sentry_sdk:
        initialise_sentry(BASE_CONFIG, "zipper", logging.getLogger("test"))

        sentry_sdk.set_tag.assert_called_once_with("bds.operation", "zipper")


def test_sentry_uses_configured_traces_sample_rate():

    assert initialise_with({})["traces_sample_rate"] == 0.25


def test_sentry_falls_back_to_default_traces_sample_rate_when_unset():

    assert initialise_with({"SENTRY_TRACES_SAMPLE_RATE": ""})["traces_sample_rate"] == DEFAULT_TRACES_SAMPLE_RATE


def test_sentry_falls_back_to_default_traces_sample_rate_when_not_a_number():

    assert initialise_with({"SENTRY_TRACES_SAMPLE_RATE": "lots"})["traces_sample_rate"] == DEFAULT_TRACES_SAMPLE_RATE


def test_sentry_falls_back_to_default_traces_sample_rate_when_out_of_range():

    assert initialise_with({"SENTRY_TRACES_SAMPLE_RATE": "50"})["traces_sample_rate"] == DEFAULT_TRACES_SAMPLE_RATE


def test_sentry_scrubs_every_secret_configuration_variable():
    """Sentry attaches stack-frame local variables to events, and the config
    dict is a local variable throughout the app, so every variable which
    config.py marks as secret has to be scrubbed by name."""

    scrubber = initialise_with({})["event_scrubber"]

    for name in get_secret_variable_names():
        assert name.lower() in scrubber.denylist, f"{name} is a secret, but Sentry would not scrub it"


def test_sentry_scrubs_secrets_nested_inside_local_variables():
    """The secret values sit inside the config dict rather than being local
    variables in their own right, so scrubbing has to be recursive."""

    assert initialise_with({})["event_scrubber"].recursive is True
