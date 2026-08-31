import logging

import sentry_sdk
from sentry_sdk.scrubber import DEFAULT_DENYLIST, EventScrubber

from config.config import get_secret_variable_names

# Sentry's SDK sends no traces at all unless a sample rate is set, so a default
# is supplied here rather than leaving it to the SDK
DEFAULT_TRACES_SAMPLE_RATE = 1.0

# Used when SENTRY_ENVIRONMENT is not set, in preference to the SDK's own
# default of 'production', so that an unconfigured environment can never be
# mistaken for the live one
UNCONFIGURED_ENVIRONMENT = "local-development"


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
        # Sentry attaches the local variables of every stack frame to an event,
        # and the config dict (which holds the app's credentials) is a local
        # variable in much of the app, so the secret config variables are
        # scrubbed by name. 'recursive' is needed because the values sit inside
        # the dict rather than being locals in their own right
        event_scrubber=EventScrubber(
            denylist=DEFAULT_DENYLIST + get_secret_variable_names(),
            recursive=True,
        ),
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
