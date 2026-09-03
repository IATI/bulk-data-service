import logging
from typing import Any

import sentry_sdk
from sentry_sdk.scrubber import DEFAULT_DENYLIST, EventScrubber
from sentry_sdk.types import Breadcrumb, BreadcrumbHint, Event, Hint

from config.config import get_secret_variable_names

# Sentry's SDK sends no traces at all unless a sample rate is set, so a default
# is supplied here rather than leaving it to the SDK
DEFAULT_TRACES_SAMPLE_RATE = 1.0

# Used when SENTRY_ENVIRONMENT is not set, in preference to the SDK's own
# default of 'production', so that an unconfigured environment can never be
# mistaken for the live one
UNCONFIGURED_ENVIRONMENT = "local-development"

# What Sentry itself puts in place of a value it withholds
WITHHELD = "[Filtered]"

# The parts of a request's URL which Sentry records with their values intact,
# and which can therefore carry a credential
REQUEST_URL_PARTS_TO_WITHHOLD = ("http.query", "http.fragment")


def initialise_sentry(config: dict, operation: str, logger: logging.Logger):
    """Initialises Sentry error reporting, if a DSN has been configured.

    The Sentry SDK does nothing when it has no DSN, so local development and
    test runs need no Sentry setup at all: leaving SENTRY_DSN unset means
    nothing is sent anywhere."""

    if not config["SENTRY_DSN"]:
        logger.info("Sentry: SENTRY_DSN is not set, so error reporting is disabled")
        return

    environment = config["SENTRY_ENVIRONMENT"] or UNCONFIGURED_ENVIRONMENT

    sentry_sdk.init(
        dsn=config["SENTRY_DSN"],
        environment=environment,
        release="bulk-data-service@{}".format(config["BULK_DATA_SERVICE_VERSION"]),
        # the app has no end users and processes no personal data, so there is
        # nothing to be gained from letting the SDK attach identifying
        # information to events
        send_default_pii=False,
        # Sentry attaches the local variables of every stack frame to an
        # event, and the app's credentials reach the stack in forms which
        # cannot all be recognised: psycopg assembles the database password
        # into a single 'conninfo' string, and the Azure SDK holds the storage
        # account key in locals of its own. The scrubber can only match
        # variables by name, so local variables are not sent at all
        include_local_variables=False,
        # kept as well, because it scrubs the values which the SDK collects by
        # other means, and because a variable marked SECRET in config.py should
        # be withheld by name wherever it appears
        event_scrubber=EventScrubber(
            denylist=DEFAULT_DENYLIST + get_secret_variable_names(),
            recursive=True,
        ),
        before_send=before_send,
        before_breadcrumb=before_breadcrumb,
        before_send_transaction=before_send_transaction,
        traces_sample_rate=get_traces_sample_rate(config, logger),
        # the checker and the registry changes processor run until they are
        # stopped, so being interrupted is a normal way for the app to end
        # rather than a fault worth reporting
        ignore_errors=[KeyboardInterrupt],
    )

    # the three operations run as separate containers reporting to the same
    # Sentry project, so every event records which one it came from
    sentry_sdk.set_tag("bds.operation", operation)

    logger.info("Sentry: error reporting enabled for environment '{}'".format(environment))


def before_send(event: Event, hint: Hint) -> Event | None:
    """Groups events which the app has marked as belonging to one class of alert.

    An event made from a log message is otherwise grouped on the message text,
    and the app's messages name the record they are about, so each occurrence
    would arrive as a separate issue instead of accumulating on one. A call site
    opts in by logging with `extra={"bds_alert_group": "..."}`, which is a plain
    logging keyword and so needs no knowledge of the error reporting service."""

    record = hint.get("log_record")

    alert_group = getattr(record, "bds_alert_group", None) if record is not None else None

    if alert_group:
        event["fingerprint"] = [alert_group]

        # also recorded as a tag, so that alerting rules can be written against
        # a class of alert rather than against a message
        tags = event.setdefault("tags", {})
        tags["bds.alert_group"] = alert_group

    return event


def before_breadcrumb(crumb: Breadcrumb, _hint: BreadcrumbHint) -> Breadcrumb | None:
    """Withholds the query string of the outgoing HTTP requests which Sentry
    records as breadcrumbs.

    Sentry records each request's query string with its values intact, and an
    Azure storage connection string which uses a shared access signature puts
    that signature in the query string of every request. The event scrubber
    cannot withhold it, because the only name it sees is 'http.query'."""

    withhold_request_url_parts(crumb.get("data"))

    return crumb


def before_send_transaction(event: Event, _hint: Hint) -> Event | None:
    """Withholds the same query strings from the spans of a transaction, for the
    same reason as `before_breadcrumb`.

    The app creates no transactions, so no spans are sent at present. This is
    here because a sample rate is configured, so adding a transaction later would
    otherwise quietly start sending query strings again: `before_send` is not
    given transactions, and so cannot cover this."""

    spans = event.get("spans")

    # Sentry replaces a value it has trimmed with a marker object, so the spans
    # are not necessarily a list, and this must not be the thing which raises
    if isinstance(spans, list):
        for span in spans:
            withhold_request_url_parts(span.get("data"))

    return event


def withhold_request_url_parts(data: Any):
    """Replaces the parts of a recorded request URL which can carry a credential.
    The method, the URL without its query string, and the response status are
    left alone, so a breadcrumb still says which request was being made."""

    if not isinstance(data, dict):
        return

    for part in REQUEST_URL_PARTS_TO_WITHHOLD:
        if part in data:
            data[part] = WITHHELD


def get_traces_sample_rate(config: dict, logger: logging.Logger) -> float:
    """Returns the configured trace sample rate, falling back to the default if
    it is unset or unusable. A bad value here must not stop the app from
    starting, nor stop errors from being reported."""

    configured_rate = config["SENTRY_TRACES_SAMPLE_RATE"]

    if not configured_rate:
        return DEFAULT_TRACES_SAMPLE_RATE

    try:
        rate = float(configured_rate)
    except ValueError:
        logger.warning(
            "Sentry: SENTRY_TRACES_SAMPLE_RATE '{}' is not a number: using {}".format(
                configured_rate, DEFAULT_TRACES_SAMPLE_RATE
            )
        )
        return DEFAULT_TRACES_SAMPLE_RATE

    if not 0.0 <= rate <= 1.0:
        logger.warning(
            "Sentry: SENTRY_TRACES_SAMPLE_RATE '{}' is not between 0 and 1: using {}".format(
                configured_rate, DEFAULT_TRACES_SAMPLE_RATE
            )
        )
        return DEFAULT_TRACES_SAMPLE_RATE

    return rate
