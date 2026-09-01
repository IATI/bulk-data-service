import logging
from typing import Any
from unittest import mock

import sentry_sdk
from sentry_sdk.transport import Transport

from config.config import get_basic_config, get_secret_variable_names
from config.sentry import (
    DEFAULT_TRACES_SAMPLE_RATE,
    UNCONFIGURED_ENVIRONMENT,
    WITHHELD,
    before_breadcrumb,
    before_send,
    before_send_transaction,
    initialise_sentry,
)
from utilities.db import get_db_connection

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


def test_sentry_does_not_send_stack_frame_variables():
    """The app's credentials reach the stack in forms the scrubber cannot match by
    name: psycopg assembles the database password into a single conninfo string,
    and the Azure SDK holds the storage account key in locals of its own. Sending
    no local variables is the only way to withhold all of them."""

    assert initialise_with({})["include_local_variables"] is False


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


def make_log_record(**attributes) -> logging.LogRecord:
    record = logging.LogRecord("bds", logging.ERROR, "some_module.py", 1, "a message", None, None)
    for name, value in attributes.items():
        setattr(record, name, value)
    return record


def test_sentry_is_given_the_grouping_hook():

    assert initialise_with({})["before_send"] is before_send


def test_events_marked_with_an_alert_group_are_grouped_by_it():
    """Without this, each occurrence would be a separate issue: these messages
    name the record they are about, and Sentry groups log events on their text."""

    event = before_send({}, {"log_record": make_log_record(bds_alert_group="suitecrm-orphan-dataset")})

    assert event is not None

    assert event.get("fingerprint") == ["suitecrm-orphan-dataset"]

    assert event.get("tags") == {"bds.alert_group": "suitecrm-orphan-dataset"}


def test_events_marked_with_an_alert_group_keep_their_own_message():
    """The message identifies the record, which is what makes an individual event
    useful once the alert has been raised, so grouping must not flatten it."""

    event = before_send(
        {"logentry": {"message": "dataset 320cf690 has no reporting org"}},
        {"log_record": make_log_record(bds_alert_group="suitecrm-orphan-dataset")},
    )

    assert event is not None

    assert event.get("logentry", {}).get("message") == "dataset 320cf690 has no reporting org"


def test_events_without_an_alert_group_are_left_alone():

    event = before_send({}, {"log_record": make_log_record()})

    assert event == {}


def test_events_which_did_not_come_from_a_log_record_are_left_alone():
    """Unhandled exceptions have no log record, and group on their stack trace,
    which is better than anything a fingerprint could do."""

    assert before_send({}, {}) == {}


def test_an_empty_alert_group_does_not_group_events_together():

    assert before_send({}, {"log_record": make_log_record(bds_alert_group="")}) == {}


def test_sentry_is_given_the_request_url_hooks():

    init_args = initialise_with({})

    assert init_args["before_breadcrumb"] is before_breadcrumb

    assert init_args["before_send_transaction"] is before_send_transaction


def test_query_strings_are_withheld_from_request_breadcrumbs():
    """Sentry records query strings with their values, and an Azure storage
    connection string which uses a shared access signature puts that signature in
    the query string of every request."""

    crumb = before_breadcrumb(
        {
            "type": "http",
            "data": {
                "method": "GET",
                "url": "https://example.blob.core.windows.net/iati-files/dataset.xml",
                "http.query": "sig=A-SHARED-ACCESS-SIGNATURE&se=2026-01-01",
                "http.fragment": "somewhere",
                "status_code": 403,
            },
        },
        {},
    )

    assert crumb is not None

    assert crumb["data"]["http.query"] == WITHHELD
    assert crumb["data"]["http.fragment"] == WITHHELD

    # what is left has to be enough to say which request failed
    assert crumb["data"]["method"] == "GET"
    assert crumb["data"]["url"] == "https://example.blob.core.windows.net/iati-files/dataset.xml"
    assert crumb["data"]["status_code"] == 403


def test_breadcrumbs_without_request_data_are_left_alone():

    assert before_breadcrumb({"type": "log", "message": "a message"}, {}) == {
        "type": "log",
        "message": "a message",
    }

    assert before_breadcrumb({"type": "http", "data": None}, {}) == {"type": "http", "data": None}


def test_query_strings_are_withheld_from_transaction_spans():

    # typed loosely because the SDK's Event marks every key as optional, so
    # reading one back is a type error even where the test has just supplied it
    transaction: Any = {
        "type": "transaction",
        "spans": [
            {"op": "http.client", "data": {"url": "https://example.com/x", "http.query": "sig=SECRET"}},
            {"op": "db", "data": {"db.system": "postgresql"}},
        ],
    }

    event: Any = before_send_transaction(transaction, {})

    assert event is not None

    assert event["spans"][0]["data"]["http.query"] == WITHHELD
    assert event["spans"][0]["data"]["url"] == "https://example.com/x"

    assert event["spans"][1]["data"] == {"db.system": "postgresql"}


def test_transactions_whose_spans_sentry_has_trimmed_are_left_alone():
    """Sentry replaces a value it has trimmed with a marker object, so the spans
    are not necessarily a list. The hook must not be the thing which raises."""

    trimmed: Any = {"type": "transaction", "spans": object()}

    assert before_send_transaction(trimmed, {}) is not None


class CapturingTransport(Transport):
    """Captures the envelopes the SDK would have transmitted, so that what would
    have left the machine can be inspected. Used in place of Sentry's own HTTP
    transport, so nothing is sent and no socket is opened."""

    def __init__(self):
        super().__init__()
        self.envelopes = []

    def capture_envelope(self, envelope) -> None:
        self.envelopes.append(envelope)

    @property
    def transmitted(self) -> str:
        """What the SDK serialised for transmission, which is what has to be free
        of credentials."""

        return "\n".join(
            item.get_bytes().decode("utf-8", "replace") for envelope in self.envelopes for item in envelope.items
        )


def initialise_sentry_with_captured_transport(config: dict, transport: CapturingTransport, logger: logging.Logger):
    """Runs the app's own initialisation, substituting only the transport, so that
    the options under test are the ones the app really uses."""

    real_init = sentry_sdk.init

    with mock.patch("config.sentry.sentry_sdk.init", lambda **kwargs: real_init(**kwargs, transport=transport)):
        initialise_sentry(config, "checker", logger)


DB_PASSWORD_CANARY = "CANARY-db-password-3f9c1e7a5b2d"


def test_a_failing_database_connection_does_not_send_the_password():
    """psycopg assembles the connection keywords into one string which contains
    the password, and holds it in a local variable. Sentry would attach the local
    variables of every frame, and its scrubber cannot withhold this one because it
    matches names and the name here is 'conninfo'.

    This drives the real library rather than a stand-in, so it keeps testing the
    real behaviour if psycopg changes how it holds the connection string."""

    config = get_basic_config() | {
        "SENTRY_DSN": "https://examplekey@example.invalid/1",
        "SENTRY_ENVIRONMENT": "test",
        "DB_NAME": "no-such-database",
        "DB_USER": "no-such-user",
        "DB_PASS": DB_PASSWORD_CANARY,
        "DB_HOST": "127.0.0.1",
        "DB_PORT": "1",  # nothing is listening, so connecting really fails
        "DB_SSL_MODE": "disable",
        "DB_CONNECTION_TIMEOUT": "1",
    }

    transport = CapturingTransport()
    logger = logging.getLogger("bds-sentry-test")

    initialise_sentry_with_captured_transport(config, transport, logger)

    try:
        # the config is passed directly rather than wrapped in a BDSContext:
        # get_db_connection only looks values up, and building a context coerces
        # unrelated variables which are unset in a bare test environment, so it
        # would fail before psycopg was ever reached
        try:
            get_db_connection(config)  # type: ignore[arg-type]
        except Exception:
            # what the checker's service loop does: catch it and log it with the
            # exception attached, which is what reports it to Sentry
            logger.exception("Exception in checker service loop.")

        sentry_sdk.flush()
    finally:
        sentry_sdk.get_client().close()

    assert transport.envelopes, "the SDK sent nothing, so this test would pass for the wrong reason"

    # confirms the failure which was reported is the one this test is about.
    # Without this the test would also pass if it never reached psycopg
    assert "OperationalError" in transport.transmitted, "psycopg was not reached, so nothing was proved"

    assert DB_PASSWORD_CANARY not in transport.transmitted
