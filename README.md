# IATI Bulk Data Service Tool

## Summary

| Product          | IATI Bulk Data Service                                                                                                                                                                                                              |
| ---------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Description      | A Python application which fetches the list of registered IATI datasets and periodically downloads them, making each available individually as an XML file and ZIP file, and also providing a ZIP file containing all the datasets. |
| Website          | https://bulk-data.iatistandard.org/                                                                                                                                                                                                 |
| Related          |
| Documentation    | Rest of `README`                                                                                                                                                                                                                    |
| Technical Issues | See https://github.com/IATI/bulk-data-service/issues                                                                                                                                                                                |
| Support          | https://iatistandard.org/en/guidance/get-support/                                                                                                                                                                                   |

## Description

The Bulk Data Service downloads a list of the IATI datasets from the Registry and attempts to download each one. It caches a copy of each successful download for up to 72 hours. These cached copies are available individually as XML or ZIP (the URLs are listed in the full dataset index, linked to from the [Bulk Data website](https://bulk-data.iatistandard.org/).

The update process is documented in [Dataset update process](docs/dataset-update-process.md).

## High-level requirements

- Python 3.12.6 or above
  - (This is specified in .python-version, Dockerfile, and pyproject.toml)
- Postgres DB
- Azure storage account with blob storage enabled

## Running the app locally

### First-time setup

#### 1. Setup and activate a Python virtual environment.

```
python -m venv .ve
source .ve/bin/activate
```

_Note: if you don't use `pyenv`, you may need to run `python3.12 -m venv .ve`_

#### 2. Install the dependencies

```
pip install -r requirements.txt
```

#### 3. Setup a `.env` file

The IATI Bulk Data Service app, the docker compose setup for local development (Azurite, Postgres), and the yoyo database migrations tool (which the Bulk Data Service app runs, but which it is sometimes useful to run from the command line during development), are all configured via environment variables. When running locally, these are set via a `.env` file. To create one, copy the example file and edit as needed:

```
cp .env-example .env
```

The example file is preconfigured to work with the local docker compose setup.

#### 4. Install some version of `dotenv` (optional)

The `.env` file is used when running things locally to store environment variables that configure the apps mentioned above. Docker Compose will read this automatically, but when running the bulk data service app or `yoyo` directly, you need to get these variables into the shell environment: you can either source this file to get the environment variables into your current terminal context, or you can use one of the various `dotenv` command line tools to import the environment on each run (using `dotenv` lets you quickly switch different `.env` files in and out, which can be useful for testing, debugging, etc).

### Running after first-time setup

Running the app successfully requires a Postgres database and a connection to an Azure blob storage account. There is a docker compose setup which can be used to start an instance of each service locally, that can be run with:

```bash
docker compose up -d
```

The example `.env` file (`.env-example`) is configured to use the above docker compose setup. If you don't use the docker compose setup, then you will need to change the values in the `.env` file accordingly.

Once the docker compose setup is running, you can run the dataset updater part of the app with (this will download the datasets and upload them to Azurite):

```bash
dotenv run python src/iati_bulk_data_service.py -- --operation checker --single-run --run-for-n-datasets=50
```

You can run the zipper operation with:

```bash
dotenv run python src/iati_bulk_data_service.py -- --operation zipper --single-run
```

It will store the ZIP files in the directory defined in the `ZIP_WORKING_DIR` environment variable.

The full range of command line arguments is listed below:

```
usage: iati_bulk_data_service.py [-h] --operation {checker,zipper,registry-changes-processor} [--single-run] [--run-for-n-datasets RUN_FOR_N_DATASETS] [--run-for-single-reporting-org RUN_FOR_SINGLE_REPORTING_ORG] [--skip-safety]

options:
  -h, --help            show this help message and exit
  --operation {checker,zipper,registry-changes-processor}
                        Operation to run: checker, downloader, registry-changes-processor
  --single-run          Perform a single run, then exit
  --run-for-n-datasets RUN_FOR_N_DATASETS
                        Run on the first N datasets from registration service (useful for testing)
  --run-for-single-reporting-org RUN_FOR_SINGLE_REPORTING_ORG
                        Run only for the datasets belonging to the specified reporting org short name (useful for testing)
  --skip-safety         Skip safety checks during the run (useful for testing)
```

To shutdown the docker compose setup, use (the Azure Service Bus emulator
appears to be a bit sensitive to Ctrl-C shutdowns, so always best to shutdown
with `docker compose down`):

```
docker compose down
```


_Note: not all versions of `dotenv` require a `run` subcommand._

## Development on the app

### Code checking and formatting

The project is set up with various code linters and formatters. You can setup your IDE to run them automatically on file save, or you can run them manually. (Configuration
files are included for VS Code).

To run these you need to install the extra development dependencies into the Python virtual environment using the following:

```
pip install -r requirements-dev.txt
```

#### isort

Import sorter `isort` is configured via `pyproject.toml` and can be run with:

```
isort .
```

#### mypy

Type checker `mypy` is configured via `pyproject.toml`. It can be run with:

```
mypy
```

#### flake8

Flake8 is configured via `pyproject.toml`, and can be run with:

```
flake8
```

#### black

Code formatter `black` is configured via `pyproject.toml` and can be run with:

```
black .
```

### Adding new dependencies to main project

New dependencies need to be added to `pyproject.toml`.

After new dependencies have been added, `requirements.txt` should be regenerated using:

```
pip-compile --upgrade -o requirements.txt pyproject.toml
```

### Adding new dependencies to the development environment

New development dependencies need to be added to `pyproject.toml` in the `dev` value of the `[project.optional-dependencies]` section.

After new dev dependencies have been added, `requirements-dev.txt` should be regenerated using:

```
pip-compile --upgrade --extra dev -o requirements-dev.txt pyproject.toml
```

### Database migrations

The Bulk Data Service's database schema management is handled by [yoyo](https://ollycope.com/software/yoyo/latest/). The database is created and migrated (if needed) whenever the app is run, so during development, it is always safe to drop the database if you want to start over.

`yoyo` has a command line tool which can be used to do this, and which can also be used to rollback the database schema to any particular revision, if that is useful during development.

`yoyo` is configured via `yoyo.ini` which draws values from environment variables, and so it is best run using `dotenv` which will configure it for whatever local setup you are using:

The following commands may be useful:

```
dotenv run yoyo -- list       # list available migrations
dotenv run yoyo -- rollback   # rollback, interactively
dotenv run yoyo -- new        # create file for a new migration
```

### Automated tests

Requirements: docker compose

Unit and integration tests are written in `pytest`. The integration tests work by running various bits of the code against running servers, and there is a docker compose setup which launches: Azurite, Postgres, and a Mockoon server.

The Azurite and Postgres services are ephemeral, and don't persist any data to disk.

The Mockoon server serves some of the artifacts in `tests/artifacts` over HTTP, and has some routes configured to return error codes so these can be tested

To run the tests, you must first start this docker compose setup with:

```
cd tests-automated-environment
docker compose up --remove-orphans
```

_Note: the `--remove-orphans` just helps keep things clean as you develop, and alter the setup._

The Azure Service Bus emulator takes a while to start, and `docker compose`
cannot wait for it because the emulator image is distroless. Running the tests
before it is ready causes the MQ integration tests to fail with connection
errors, so wait for it with:

```
./tests-local-environment/wait-for-mq-emulator.sh
```

(For the local development docker compose setup, rather than the test setup,
pass the dev environment's health URL:
`./tests-local-environment/wait-for-mq-emulator.sh http://localhost:5300/health`)

Once this is running, run the tests with:

```
pytest
```

This automated test environment is configured via the following files:

`tests-local-environment/.env`

`tests-local-environment/docker-compose.yml`

`tests-local-environment/mockoon-registration-and-data-server-config.json`

You can use the Mockoon GUI application to edit the mockoon server configuration file (`mockoon-registration-and-data-server-config.json`).

The automated tests are safe to run alongside the `docker compose` setup for development.

### Automatically running the automated tests

When you are developing you may want to have the tests run whenever you make changes. `pytest-watcher` is installed for this purpose and you can run it with the following command:

```bash
pytest-watcher .
```

## Error reporting

Errors are reported to [Sentry](https://sentry.io). Reporting is switched on by
setting `SENTRY_DSN` to the DSN of the Sentry project the errors should go to;
when it is unset — which is the default for local development and for the
automated tests — nothing is sent anywhere and the app is unaffected.

The following environment variables configure it:

| Variable | Purpose |
| --- | --- |
| `SENTRY_DSN` | The DSN of the Sentry project to report to. Unset disables reporting. Treated as a secret: it is never written to the log. |
| `SENTRY_ENVIRONMENT` | The environment name events are tagged with, e.g. `dev` or `prod`. Set automatically to the deployment's target environment. Defaults to `local-development`. |
| `SENTRY_TRACES_SAMPLE_RATE` | The proportion of transactions (`0.0` to `1.0`) sent for performance tracing. Defaults to `1.0`. |

Sentry is initialised in `src/config/sentry.py`, before anything else in the
app's startup which can fail, so that errors in the rest of the startup are
reported. Every event is tagged with the app version, the environment, and
which of the three operations (`checker`, `zipper`,
`registry-changes-processor`) it came from, since they run as separate
containers reporting to the same Sentry project.

Unhandled exceptions are reported automatically, as are messages logged at
`ERROR` or above.

### Error reporting and secrets

Sentry would otherwise attach the local variables of every stack frame to an
event, and the app's credentials reach the stack in forms which cannot be
recognised by name: `psycopg` assembles the database password into a single
`conninfo` string, and the Azure SDK holds the storage account key in locals of
its own. Local variables are therefore not sent at all
(`include_local_variables=False`), which costs the variable values in a
traceback but keeps the file, line, function and source line of every frame.

In addition, the variables which `src/config/config.py` marks as
`LogPolicy.SECRET` are scrubbed by name wherever the SDK collects them by other
means, using the same list that keeps them out of the startup log.

Deciding that a variable holds a credential is still a manual step:
`tests/unit/test_config.py::test_every_configuration_variable_is_either_logged_or_secret`
requires every configuration variable to be classified, but a credential
wrongly marked `LOGGABLE` would satisfy it. The
`SECRET_NAME_FRAGMENTS` backstop in that file is what catches the common cases
by name.

Sentry also records the query string of every outgoing HTTP request, with the
values intact. An Azure storage connection string which uses a
`SharedAccessSignature=` rather than an `AccountKey=` puts that signature in the
query string of every request to blob storage, so `before_breadcrumb` and
`before_send_transaction` in `src/config/sentry.py` withhold it. The method, the
URL without its query string and the response status are kept, so a breadcrumb
still says which request was being made.

`tests/unit/test_sentry.py::test_a_failing_database_connection_does_not_send_the_password`
is the regression test for all of this: it stands a fake Sentry endpoint up,
makes a real database connection fail with a recognisable password, and asserts
that the password is nowhere in what the SDK transmitted.

### What error reporting does not protect

Sentry withholds nothing from the following, so these are rules to follow rather
than protections to rely on. All of them hold at the time of writing.

- **Exception messages are never scrubbed.** Never let a credential reach an
  exception message. Note that `psycopg`'s own message names the database host,
  port, user and database — a deliberate trade, because those four are marked
  `SECRET` out of caution rather than because they are credentials, and losing
  them would make a database outage much harder to diagnose. The password itself
  does not appear there.
- **Log messages and breadcrumbs are never scrubbed.** The `LogPolicy` split in
  `src/config/config.py` is what keeps credentials out of them, and it governs
  only this app's own logging. Third-party libraries log too, and anything they
  log at `ERROR` becomes a Sentry event — `libsuitecrm`, for instance, logs
  response bodies.
- **The command line is sent with every event.** Never pass a credential as a
  command-line argument. The current arguments are `--operation`,
  `--single-run`, `--run-for-n-datasets`, `--run-for-single-reporting-org` and
  `--skip-safety`.
- **Never put a credential in a URL path.** The query string is withheld, the
  path is not.

### Sentry's own data scrubbing

The settings in the Sentry project are a second layer, and are relied on rather
than optional. Sentry applies them after the event has been transmitted but
before it is stored, so they are a backstop for anything the app fails to
withhold — not a substitute for withholding it.

- Leave the default data scrubber enabled.
- Add Advanced Data Scrubbing rules which replace credential-shaped patterns
  (`password=`, `AccountKey=`, `SharedAccessSignature=`, `sig=`) in
  `$error.value`, `$message`, `$breadcrumb` and `$http.query`. Pattern rules
  belong here rather than in the app: adding one is a settings change instead of
  a deploy.

Three things to know about those settings:

- the rules are not retroactive, and apply only to events received after they
  are saved;
- organisation-level settings override project-level ones, so a project rule can
  be silently ineffective;
- "Additional Sensitive Fields" matches field *values* by substring as well as
  field names, so a short entry such as `pass` would corrupt unrelated text.

## Provisioning and Deployment

### Initial Provisioning

#### Bulk Data Service App

You can create an Azure-based instance of Bulk Data Service using the `azure-create-resources.sh` script. It must be run from the root of the repository, and it requires (i) the environment variable `BDS_DB_ADMIN_PASSWORD` to be set with the password for the database, and (ii) a single parameter which is the name of the environment/instance. For instance, the following command will create a dev instance:

```bash
BDS_DB_ADMIN_PASSWORD=passwordHere ./azure-provision/azure-create-resources.sh dev`
```

This will create a resource group on Azure called `rg-bulk-data-service-dev`, and then create and configure all the Azure resources needed for the Bulk Data Service within that resource group (except for the Container Instance, which is created/updated as part of the deploy stage).

At the end of its run, the `azure-create-resources.sh` script will print out various secrets which need to be added to Github Actions.

**NOTE**: This is only really useful for temporary deployment or initial setup; once you're setup with CI/CD, the GitHub action does all this.

#### Bulk Data Service Network and Public IP

The Bulk Data Service is deployed to a dedicated vnet with subnet and attached NAT Gateway which has a public IP. To ensure the IP remains, these are not destroyed and re-created on every release (like the Azure Container Instances are). To create the networks and public IPs for dev and production, run:

```bash
./azure-provision/create-vnets-public-ips.sh
```

### Deployment - Versioning

The app version is set in `pyproject.toml`, and this is read by the app to use in the `User-Agent` header. When making a new release, set the version here to the appropriate value. Then, when releasing the app using the normal IATI Python app deployment process, choose the tag name to match the version chosen.

### Deployment - CI/CD

The application is setup to deploy to the dev instance when a PR is merged to
`develop`, and to production when a release is done on `main` branch.

Sometimes, when altering the CI/CD setup or otherwise debugging, it can be
useful to do things manually. The Bulk Data Service can be released to an Azure instance (e.g., a test instance) using the following command:

```bash
./azure-deployment/manual-azure-deploy-from-local.sh test
```

For this to work, you need to put the secrets you want to use in `azure-deployment/manual-azure-deploy-secrets.env` and the variables you want to use in `azure-deployment/manual-azure-deploy-variables.env`. These is an example of each of these files that can be used as a starting point.

### Manually building the docker image

It is sometimes useful for testing/debugging to manually build the docker image.

You can do so using the following command, replacing `INSTANCE_NAME` with the relevant instance:

```bash
docker build . -t criati.azurecr.io/bulk-data-service-INSTANCE_NAME
```

To run it locally:

```bash
docker container run --env-file=.env-docker "criati.azurecr.io/bulk-data-service-dev" --operation checker --single-run --run-for-n-datasets 20
```

## Resources

[Reference docs for the Azure deployment YAML file](https://learn.microsoft.com/en-us/azure/container-instances/container-instances-reference-yaml#schema) (`azure-deployment/deploy.yml`).
