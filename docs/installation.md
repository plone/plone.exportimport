---
myst:
  html_meta:
    "description": "Installation of plone.exportimport"
    "property=og:description": "Installation of plone.exportimport"
    "property=og:title": "Installation"
    "keywords": "Plone 6, plone.exportimport"
---

(installation-label)=

# Installation

**This package supports sites running Plone version 6.0 and above.**

Add **plone.exportimport** to the Plone installation using `pip`:

```bash
pip install plone.exportimport
```

## Load the package

To make this package available to a Plone installation, you need to load its ZCML configuration.

If your project has a Python package with custom code, add the following line to your package's `dependencies.zcml` or `configure.zcml`:

```xml
   <include package="plone.exportimport" />
```

An alternative to that is to use the `instance.yaml` configuration file provided by [`cookiecutter-zope-instance`](https://github.com/plone/cookiecutter-zope-instance).

Look for the `zcml_package_includes` configuration and add this package to the list of packages already listed there:

```yaml
   zcml_package_includes: ['my.package', 'plone.exportimport']
```
