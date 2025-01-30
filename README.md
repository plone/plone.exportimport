<p align="center">
    <img alt="Plone Logo" width="200px" src="https://raw.githubusercontent.com/plone/.github/main/plone-logo.png">
</p>

<h1 align="center">
  Plone Content Export and Import
</h1>

Package supporting the export and import of content, principals, relations, translations, discussions, and redirects from and to a Plone site.

## Introduction

This package is a slimmer version of the awesome [collective.exportimport](https://github.com/collective/collective.exportimport).

While `collective.exportimport` supports older Plone versions and Python 2, and also takes care of data conversion from Archetypes to Dexterity, this package focus only on latest Plone and Python.


## Documentation

[`plone.exportimport` documentation](https://6.docs.plone.org/admin-guide/export-import.html)



## Installation

> [!IMPORTANT]
> This package supports sites running Plone version 6.0 and above.

> [!IMPORTANT]
> This package is now included with Plone 6.1 and above by default.
> The following installation instructions are relevant only for Plone 6.0 sites.

Add `plone.exportimport` to the Plone installation using `pip`.

```shell
pip install plone.exportimport
```


### Load the package

To make this package available to a Plone installation, you need to load its ZCML configuration.

If your project has a Python package with custom code, add the following line to your package's `dependencies.zcml` or `configure.zcml`:

```xml
<include package="plone.exportimport" />
```

Alternatively, you can use the `instance.yaml` configuration file provided by [`cookiecutter-zope-instance`](https://github.com/plone/cookiecutter-zope-instance).

Look for the `zcml_package_includes` configuration, and add this package to the list of packages already listed there.

```yaml
zcml_package_includes: ['my.package', 'plone.exportimport']
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
