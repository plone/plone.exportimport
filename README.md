<p align="center">
    <img alt="Plone Logo" width="200px" src="https://raw.githubusercontent.com/plone/.github/main/plone-logo.png">
</p>

<h1 align="center">
  Plone Content Export and Import
</h1>

Package supporting the export and import of content, principals, relations, translations, discussions, and redirects from and to a Plone site.

## Introduction

This package is a slimmer version of the awesome [collective.exportimport](https://github.com/collective/collective.exportimport).

While `collective.exportimport` supports older Plone versions and Python 2, and also takes care of data conversion from Archetypes to Dexterity, this package focuses only on latest Plone and Python.

## Documentation

[`plone.exportimport` documentation](https://6.docs.plone.org/admin-guide/export-import.html)

## REST API Endpoints

This package provides REST API endpoints for exporting and importing site data via HTTP requests.

### Export Endpoint

Export site data as a ZIP file.

**Endpoint:** `POST /plone/@export`

**Permission:** `plone.exportimport.export` (granted to Site Administrators by default)

**Response:** ZIP file containing all exported data (content, principals, relations, translations, discussions, redirects, portlets)

**Example:**

```bash
curl -X POST \
  -H "Authorization: Bearer <token>" \
  https://plone.example.com/plone/@export \
  -o export.zip
```

### Import Endpoint

Import site data from a ZIP file.

**Endpoint:** `POST /plone/@import`

**Permission:** `plone.exportimport.import` (granted to Site Administrators by default)

**Request:** Multipart form data with `file` field containing the ZIP file

**Response:** JSON object with status and import report

**Example:**

```bash
curl -X POST \
  -H "Authorization: Bearer <token>" \
  -F "file=@export.zip" \
  https://plone.example.com/plone/@import
```

**Response Example:**

```json
{
  "status": "success",
  "report": ["Principals imported: 5 principals", "Content imported: 12 items", "Relations imported: 3 relations", "..."]
}
```

## Installation

> [!IMPORTANT]
> This package supports sites running Plone version 6.0 and above.

> [!IMPORTANT]
> This package is now included with Plone 6.1 and above by default.

If `plone.exportimport` is not yet available in your Plone installation, add it using `pip`.

```shell
pip install plone.exportimport
```


## Contributing

See [Contributing to Plone](https://6.docs.plone.org/contributing/index.html) and [Contribute to Plone 6 core](Contribute to Plone 6 core) for general contributing policies and guidance.

The following sections specifically describe how to develop and contribute to `plone.exportimport`.


### Setup

You need a working Python environment version 3.8 or later.

Install the dependencies and a development instance using the following command.

```shell
make install
```


### Local environment Plone server

Start Plone, on port 8080, with the following command.

```shell
make start
```


### Format code base

Format the code base with the following command.

```shell
make format
```


### Run tests

Testing of this package is done with [`pytest`](https://docs.pytest.org/en/stable/) and [`tox`](https://tox.wiki/en/stable/).

Run all tests with the following command.

```shell
make test
```

Run all tests, but stop on the first error and open a `pdb` session.

```shell
./bin/tox -e test -- -x --pdb
```

Run tests named `TestUtilsDiscussions`.

```shell
./bin/tox -e test -- -k TestUtilsDiscussions
```


## License

The project is licensed under the GPLv2.
