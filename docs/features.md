---
myst:
  html_meta:
    "description": "Features of plone.exportimport"
    "property=og:description": "Features of plone.exportimport"
    "property=og:title": "Features"
    "keywords": "Plone 6, plone.exportimport"
---

(features-label)=

# Features

The `plone.exportimport` package provides support to export and import all kinds of data from and to Plone sites using a intermediate json-format.

Most features use `plone.restapi` to serialize and deserialize data.

## Supported Data

* Content (Dexterity content items)
    * Ordering
    * Local Roles
    * Versions
    * Default Pages
* Principals (Members and Groups)
* Relations (Relationship between content items)
* Translations (Translation groups)
* Discussions (Content comments)
* Redirects (Redirect information)

## Exported Data Structure

Some goals of the new data structure are:

* Support diff of exported data
* Have blob files near the content item that uses it

In the top level directory with the exported content, we have the following objects:

| Name | Description |
| --- | --- |
| `content` | Directory containing content item information exported from the site |
| `discussions.json` | JSON File with discussions (comments) exported from the site |
| `principals.json` | JSON File with members and groups exported from the site |
| `redirects.json` | JSON File with redirect information exported from the site |
| `relations.json` |  JSON File with content relations exported from the site  |
| `translations.json` | JSON File with translation groups exported from the site  |

### Content Directory structure

In the `content` directory we have all content items exported from the site. Each content item will have its own sub-directory, named with the UID of the content, including the serialized data and all blob files related to this content.

One special case is the directory for the `Plone Site` object, that will be named **plone_site_root**.

| Name | Description |
| --- | --- |
| `content/__metadata__.json` | JSON File with metadata information about the exported content |
| `content/<content uid>` | Directory with serialization for a content item |
| `content/plone_site_root` | Directory with serialization for the Plone Site Root |

#### Content Item Directory Structure

Considering we have a File content item with UID `3e0dd7c4b2714eafa1d6fc6a1493f953` and a PDF file named `plone.pdf` (added in the `file` field), the exported directory will look like:

| Name | Description |
| --- | --- |
| `content/3e0dd7c4b2714eafa1d6fc6a1493f953/data.json` | JSON File with serialized representation of a content item |
| `content/3e0dd7c4b2714eafa1d6fc6a1493f953/file/plone.pdf` | Blob file stored in the `file` field in the content item |

## Command Line Utilities

This package provides two command line utilities: `plone-exporter` and `plone-importer`.

## `plone-exporter`

Export content from a Plone site to a directory in the file system.

Usage:

  - `plone-exporter` [--include-revisions] <path-to-zopeconf> <site-id> <path-to-export-data>

Example:

```shell
plone-exporter instance/etc/zope.conf Plone /tmp/plone_data/
```

By default, the revisions history (older versions of each content item) are not exported.
If you do want them, add `--include-revisions` on the command line.

## `plone-importer`

Import content from a file system directory into an existing Plone site.

Usage:

  - `plone-importer` <path-to-zopeconf> <site-id> <path-to-import-data>

Example:

```shell
plone-importer instance/etc/zope.conf Plone /tmp/plone_data/
```
