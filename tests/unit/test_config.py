from unittest import mock

from dotenv import load_dotenv

from config import config as config_module
from config.bds_context import BDSContext
from config.config import LogPolicy, get_basic_config, get_config_for_logging, get_secret_variable_names


def test_config_blob_storage_base_url_has_no_trailing_slash_1():

    load_dotenv("tests/artifacts/config-files/env-file-1", override=True)

    config = get_basic_config()

    assert config["WEB_BASE_URL"] == "http://127.0.0.1:10000/devstoreaccount1"


def test_config_blob_storage_base_url_has_no_trailing_slash_2():

    load_dotenv("tests/artifacts/config-files/env-file-2", override=True)

    config = get_basic_config()

    assert config["WEB_BASE_URL"] == "http://127.0.0.1:10000/devstoreaccount1"


def test_config_dataset_timeouts_loaded():
    load_dotenv("tests/artifacts/config-files/env-file-2", override=True)

    config = get_basic_config()

    context = BDSContext(config, mock.Mock(), mock.Mock())

    assert context.DATASET_GET_TIMEOUT == 22

    assert context.DATASET_HEAD_TIMEOUT == 7


# The configuration variables which may appear in the startup log, in the order in which
# they are logged. These lists are written out by hand rather than derived from
# config.py, so that they are an independent statement of what the log is allowed to
# contain: a variable added to config.py, or whose log policy is changed there, cannot
# silently start appearing in the log.
EXPECTED_LOGGABLE_VARIABLES = [
    "DATA_REGISTRATION",
    "DATA_REGISTRY_BASE_URL",
    "DATA_REGISTRY_PUBLISHER_PLAIN_LIST_URL",
    "DATA_REGISTRY_PUBLISHER_METADATA_URL",
    "DATA_REGISTRY_PUBLISHER_METADATA_BATCH_SIZE",
    "DATA_REGISTRY_SUITECRM_API_URL",
    "DATA_REGISTRY_SUITECRM_SECURE",
    "WEB_BASE_URL",
    "NUMBER_DOWNLOADER_THREADS",
    "FORCE_REDOWNLOAD_AFTER_HOURS",
    "REDOWNLOAD_FROM_NON_HEAD_SERVERS_AFTER_HOURS",
    "REMOVE_LAST_GOOD_DOWNLOAD_AFTER_FAILING_HOURS",
    "ZIP_WORKING_DIR",
    "DB_CONNECTION_TIMEOUT",
    "AZURE_STORAGE_BLOB_CONTAINER_NAME",
    "CHECKER_LOOP_WAIT_MINS",
    "AZURE_SERVICE_BUS_REGISTRY_TOPIC_NAME",
    "AZURE_SERVICE_BUS_REGISTRY_SUB_NAME",
    "AZURE_SERVICE_BUS_WAIT_TIME",
    "AZURE_SERVICE_BUS_DATASET_CHECK_RESULTS_TOPIC_NAME",
    "SEND_DATASET_CHECK_RESULT_MESSAGES",
    "DATASET_HEAD_TIMEOUT",
    "DATASET_GET_TIMEOUT",
    "SENTRY_ENVIRONMENT",
    "SENTRY_TRACES_SAMPLE_RATE",
]

# Configuration variables whose name and value must never appear in the log.
EXPECTED_SECRET_VARIABLES = [
    "DATA_REGISTRY_SUITECRM_CLIENT_ID",
    "DATA_REGISTRY_SUITECRM_CLIENT_SECRET",
    "DB_NAME",
    "DB_USER",
    "DB_PASS",
    "DB_HOST",
    "DB_PORT",
    "DB_SSL_MODE",
    "AZURE_STORAGE_CONNECTION_STRING",
    "AZURE_SERVICE_BUS_CONNECTION_STRING",
    "SENTRY_DSN",
]

# Settings which come from the command line rather than from the environment.
EXPECTED_RUNTIME_SETTINGS = [
    "single_run",
    "run_for_n_datasets",
    "run_for_single_reporting_org",
    "skip_safety",
]

# Set by get_basic_config, but not read from the environment.
EXPECTED_DERIVED_VARIABLES = ["BULK_DATA_SERVICE_VERSION"]

# Substrings which suggest that a variable holds a credential. A variable whose name
# contains one of these must never be logged, whatever config.py says about it. This is a
# backstop against a variable being mis-classified: unlike the lists above, it does not
# have to be updated when a variable is added, so it covers variables which nobody has
# thought about yet.
SECRET_NAME_FRAGMENTS = [
    "PASS",
    "API_KEY",
    "SECRET",
    "CLIENT_ID",
    "CREDENTIAL",
    "TOKEN",
    "CONNECTION_STRING",
    "DSN",
]


def get_config_lines(config: dict) -> list[str]:
    return get_config_for_logging(
        config
        | {
            "single_run": True,
            "run_for_n_datasets": 3,
            "run_for_single_reporting_org": None,
            "skip_safety": False,
        }
    )


def get_full_configuration() -> list[str]:
    load_dotenv("tests/artifacts/config-files/env-file-2", override=True)

    return get_config_lines(get_basic_config())


def get_config_lines_with_sentinel_values(monkeypatch) -> list[str]:
    """Returns the loggable config, with every configuration variable set to a value
    which identifies the variable it came from, so that the presence or absence of a
    particular variable's value in the output can be checked."""

    for name in EXPECTED_LOGGABLE_VARIABLES + EXPECTED_SECRET_VARIABLES:
        monkeypatch.setenv(name, f"sentinel-{name}")

    return get_config_lines(get_basic_config())


def test_config_for_logging_contains_exactly_the_loggable_variables():

    names_logged = [line.split("=", 1)[0] for line in get_full_configuration()]

    assert names_logged == EXPECTED_LOGGABLE_VARIABLES + EXPECTED_RUNTIME_SETTINGS


def test_config_for_logging_omits_secret_variables():

    config_output = "\n".join(get_full_configuration())

    for secret_name in EXPECTED_SECRET_VARIABLES:
        assert secret_name not in config_output


def test_config_for_logging_omits_anything_named_like_a_credential():

    names_logged = [line.split("=", 1)[0] for line in get_full_configuration()]

    for name in names_logged:
        matches = [fragment for fragment in SECRET_NAME_FRAGMENTS if fragment in name]

        assert not matches, f"{name} is logged, but its name suggests a credential: {matches}"


def test_config_for_logging_contains_every_loggable_value(monkeypatch):

    values_logged = dict(line.split("=", 1) for line in get_config_lines_with_sentinel_values(monkeypatch))

    for name in EXPECTED_LOGGABLE_VARIABLES:
        assert values_logged[name] == f"sentinel-{name}"


def test_config_for_logging_omits_secret_values(monkeypatch):

    config_output = "\n".join(get_config_lines_with_sentinel_values(monkeypatch))

    for name in EXPECTED_SECRET_VARIABLES:
        assert f"sentinel-{name}" not in config_output


def test_get_basic_config_reads_exactly_the_expected_variables():
    load_dotenv("tests/artifacts/config-files/env-file-2", override=True)

    config = get_basic_config()

    expected = set(EXPECTED_LOGGABLE_VARIABLES + EXPECTED_SECRET_VARIABLES + EXPECTED_DERIVED_VARIABLES)

    unclassified = sorted(set(config) - expected)
    no_longer_read = sorted(expected - set(config))

    assert not unclassified, (
        f"{unclassified} read by get_basic_config but not classified here: decide whether each may appear "
        f"in the startup log, then add it to EXPECTED_LOGGABLE_VARIABLES or EXPECTED_SECRET_VARIABLES"
    )

    assert not no_longer_read, f"{no_longer_read} no longer read by get_basic_config: remove from the lists above"


def test_get_secret_variable_names_returns_exactly_the_secret_variables():
    # compared as sets: the caller has no reason to depend on the order in which
    # the variables happen to be declared in config.py

    names = get_secret_variable_names()

    assert sorted(names) == sorted(EXPECTED_SECRET_VARIABLES)

    assert len(names) == len(set(names)), f"get_secret_variable_names returned duplicates: {names}"


def test_get_secret_variable_names_is_derived_from_the_log_policies(monkeypatch):
    """The Sentry event scrubber uses this as its denylist, so it has to track
    config.py: marking a new variable SECRET must be enough to keep its value out
    of anything sent off the machine, with nothing else to remember to update."""

    monkeypatch.setitem(config_module._config_variables, "A_NEWLY_ADDED_SECRET", LogPolicy.SECRET)
    monkeypatch.setitem(config_module._config_variables, "A_NEWLY_ADDED_SETTING", LogPolicy.LOGGABLE)

    names = get_secret_variable_names()

    assert "A_NEWLY_ADDED_SECRET" in names, "a variable marked SECRET in config.py was not reported as secret"

    assert "A_NEWLY_ADDED_SETTING" not in names


def test_every_configuration_variable_is_either_logged_or_secret():
    """A variable which is neither would be unclassified: withheld by nothing and
    deliberately allowed by nothing. Guards against a further LogPolicy value
    being added and applied without deciding how Sentry and the log should treat
    it."""

    load_dotenv("tests/artifacts/config-files/env-file-2", override=True)

    config = get_basic_config()

    secret_names = set(get_secret_variable_names())
    logged_names = {line.split("=", 1)[0] for line in get_config_lines(config)} - set(EXPECTED_RUNTIME_SETTINGS)
    read_names = set(config) - set(EXPECTED_DERIVED_VARIABLES)

    unclassified = sorted(read_names - secret_names - logged_names)

    assert not unclassified, (
        f"{unclassified} are read from the environment but are neither logged nor treated as secret: "
        f"give each a LogPolicy in config.py which the log and the Sentry scrubber both understand"
    )
