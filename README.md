
# IATI Bulk Data Service Tool

## Summary

 Product  |  IATI Bulk Data Service
--- | ---
Description | A Python application which fetches the list of registered IATI datasets and periodically downloads them, making each available individually as an XML file and ZIP file, and also providing a ZIP file containing all the datasets.
Website |  None
Related |
Documentation | Rest of README.md
Technical Issues | See https://github.com/IATI/bulk-data-service/issues
Support | https://iatistandard.org/en/guidance/get-support/

## High-level requirements

* Python 3.12
* Postgres 16
* Azure storage account with blob storage enabled

## Running the app locally

### First-time setup

#### 1. Setup and activate a Python virtual environment.

```
python3.12 -m venv .ve
source .ve/bin/activate
```

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

The `.env` file is used when running things locally to store environment variables that configure the apps mentioned above. To run the apps below, you can either source this file to get the environment variables into your current terminal context, or you can one of the various `dotenv` command line tools to import the environment on each run.

### Running after first-time setup

Running the app successfully requires a Postgres database and a connection to an Azure blob storage account. There is a docker compose setup which can be used to start an instance of each service locally, that can be run with:

```
docker compose up
```

The example `.env` file (`.env-example`) is configured to use the above docker compose setup. If you don't use the docker compose setup, then you will need to change the values in the `.env` file accordingly.

Once the docker compose setup is running, start the bulk download app with:

```
dotenv run python src/iati_bulk_data_service.py -- --operation checker --single-run --run-for-n-datasets=50
```


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

`yoyo` has a command line tool which can be used to do this, and which can also be used to rollback the database schema to any particula revision, if that is useful during development.

`yoyo` is configured via `yoyo.ini` which draws values from environment variables, and so it is best run using `dotenv` which will configure it for whatever local setup you are using:

The following commands may be useful:

```
dotenv yoyo -- list       # list available migrations
dotenv yoyo -- rollback   # rollback, interactively
dotenv yoyo -- new        # create file for a new migration
```


### Automated tests

Requirements: docker compose

There are some unit and integration tests written in `pytest`. The integration tests work by running various bits of the code against running servers, and there is a docker compose setup which launches: Azurite, Postgres, and a Mockoon server. The Azurite and Postgres services are ephemeral, and don't persist any data to disk. The Mockoon server serves some of the artifacts in `tests/artifacts` over HTTP, and has some routes configured to return error codes so these can be tested

To run the tests, you must first start this docker compose setup with:

```
cd tests-automated-environment
docker compose up --remove-orphans
```

Note: the `--remove-orphans` just helps keep things clean as you develop, and alter the setup.

Once this is running, run the tests with:

```
pytest
```

This automated test environment is configured via the following files:

`tests-local-environment/.env`

`tests-local-environment/docker-compose.yml`

`tests-local-environment/mockoon-registration-and-data-server-config.json`

You can use the Mockoon GUI application to edit the mockoon server configuration file (`mockoon-registration-and-data-server-config.json`).

## Deployment

### Building the docker image

```
docker build . -t criati.azurecr.io/bulk-data-service-test
```

```
docker container run --env-file=.env-docker "criati.azurecr.io/bulk-data-service-dev" --operation checker --single-run --run-for-n-datasets 20
```


## Resources

[Reference docs for the Azure deployment YAML file](https://learn.microsoft.com/en-us/azure/container-instances/container-instances-reference-yaml#schema) (`azure-deployment/deploy.yml`).


