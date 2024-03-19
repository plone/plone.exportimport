---
myst:
  html_meta:
    "description": "How to develop plone.exportimport"
    "property=og:description": "How to develop plone.exportimport"
    "property=og:title": "Develop plone.exportimport"
    "keywords": "Plone 6, plone.exportimport"
---

(develop-label)=

# Develop this package

## Setup

You need a working `python` environment (system, `virtualenv`, `pyenv`, etc) version 3.8 or superior.

Then install the dependencies and a development instance using:

```bash
make install
```

## Local Environment

### Plone Server

Start Plone, on port 8080, with the command:

```bash
make start
```

## Format codebase

```bash
make format
```

## Run tests

Testing of this package is done with [`pytest`](https://docs.pytest.org/) and [`tox`](https://tox.wiki/).

Run all tests with:

```bash
make test
```

Run all tests but stop on the first error and open a `pdb` session:

```bash
./bin/tox -e test -- -x --pdb
```

Run tests named `TestUtilsDiscussions`:

```bash
./bin/tox -e test -- -k TestUtilsDiscussions
```

## Documentation

Build this documentation

```bash
make docs-build
```

### Live version
To have a live version -- with auto-update -- of this documentation, run the command:

```bash
make docs-live
```

And then point your browser at [http://localhost:8000](http://localhost:8000)
