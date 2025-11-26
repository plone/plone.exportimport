# Changelog

<!--
   You should *NOT* be adding new change log entries to this file.
   You should create a file in the news directory instead.
   For helpful instructions, please see:
   https://github.com/plone/plone.releaser/blob/master/ADD-A-NEWS-ITEM.rst
-->

<!-- towncrier release notes start -->

## 2.0.0a1 (2025-11-26)


### Breaking changes:

- Replace ``pkg_resources`` namespace with PEP 420 native namespace.
  Support only Plone 6.2 and Python 3.10+. #3928

## 1.3.1 (2025-10-06)


### New features:

- Implement regular commits to reduce memory usage in larger import processes. @ericof #55


### Internal:

- Add a prefix to progress loggers. @ericof 
- Fix type annotations. @ericof 
- Import: Move plone.importer.principals to the top of the importers to be processed. @ericof 

## 1.3.0 (2025-09-24)


### New features:

- Support export/import of user `login_name` @ewohnlich #69


### Bug fixes:

- Fix import of ordering inside folderish components. @ericof #60


### Internal:

- Update package metadata @ericof #78

## 1.2.1 (2025-09-05)


### Bug fixes:

- Fix export of remoteUrl to an internal page keeping the site url in the exported data. @ericof #73

## 1.2.0 (2025-08-14)


### New features:

- Support non-root PloneSite import/export [ewohnlich] #67


### Bug fixes:

- Export all paths in Posix format to support export-import across platforms [ewohnlich] #66

## 1.1.1 (2025-06-26)


### Bug fixes:

- Fix error getting parent object on Windows. @ewohnlich #64

## 1.1.0 (2025-03-11)


### New features:

- Report object creation during import using the plone-importer cli. Use --quiet to disable it. @ericof #54
- Do not stop the import if an object parent is missing @ericof #56


### Bug fixes:

- Set site during plone-importer transaction commit. @ericof #52
- Sort `relations.json` and `translations.json` so their contents are stable.  @mauritsvanrees #57

## 1.0.0 (2025-01-31)


### Bug fixes:

- Export the raw value of rich text fields, instead of the transformed output.
  This fixes internal links in Classic UI based distributions.
  @mauritsvanrees #48
- Fix traceback when translation group does not have the default language.
  @mauritsvanrees #50


### Documentation:

- Migrate documentation to README.md and https://6.docs.plone.org/admin-guide/export-import.html. @stevepiercy #46

## 1.0.0b1 (2025-01-23)


### New features:

- Include revisions only when passing `--include-revisions`.  @mauritsvanrees #39


### Bug fixes:

- Export principals: sort groups, roles, and members.  @mauritsvanrees #39
- Import: update modification dates again at the end. The original modification dates may have changed.  @mauritsvanrees #39
- Do not export parent info.
  This information is no longer needed: during import, parents are now always found by path and not by UID.
  From now on, the import ignores any parent info that is set.
  @mauritsvanrees #39

## 1.0.0a8 (2024-10-11)


### Bug fixes:

- Use plone.app.discussion and plone.app.multilingual as optional dependencies.
  @davisagli #18
- Include 'isReferencing' relations in import. @ksuess #32
- Set constraints after setting local permissions on content [@ericof] #33
- Export adds a newline at the end of all files.
  This matches the `.editorconfig` settings that we have in most Plone packages.
  [maurits] #35
- Do not export or import translations when `plone.app.multilingual` is not available.
  [maurits] #35
- Disallowlisted portlets were not imported when there was no accompanying change in the actual portlet list.
  [maurits] #35
- Add a fixer for the `allow_discussion` key: this should only contain True or False when this is explicitly set on the object.
  [maurits] #35
- Do not export or import discussions/comments when `plone.app.discussion` is not available.
  [maurits] #35
- Renamed `blacklisted_status` key to `blocked_status` to be sensitive.
  We still read the old key for backwards compatibility.
  [maurits] #35

## 1.0.0a7 (2024-06-13)


### New features:

- Export / Import local permissions for each content [@ericof] #15


### Bug fixes:

- Fix `plone.exportimport.utils.principals.members._run_as_manager` function [@ericof] #29

## 1.0.0a6 (2024-06-10)


### Bug fixes:

- Allow granting roles other than Manager and Member to principals [@ericof] #25
- Fix export of language for content [@sneridagh] #26

## 1.0.0a5 (2024-05-16)


### Internal:

- Fix list of test dependencies [@ericof] 

## 1.0.0a4 (2024-05-15)


### New features:

- Add pre_deserialize_hooks to content import [@pbauer] #22


### Bug fixes:

- Reindex members of relations in case that they contain preview_image_links
  [sneridagh] #13
- Avoid duplicating portlets registration during import [@ericof] #16


### Internal:

- Update plone/meta [@ericof] #20


## 1.0.0a3 (2024-05-02)


### Bug fixes:

- Fix importer by issuing a transaction commit
  [sneridagh] #9
- Account for use case language is empty string
  [sneridagh] #10


## 1.0.0a2 (2024-04-18)


### New features:

- Support export/import of portlets if plone.app.portlets is installed. @davisagli #8


## 1.0.0a1 (2024-04-17)


### New features:

- Implement exporter and importer for content [@ericof] #1
- Implement exporter and importer for members and groups [@ericof] #2
- Implement exporter and importer for redirects [@ericof] #3
- Implement exporter and importer for relations [@ericof] #4
- Implement exporter and importer for translations [@ericof] #5
- Implement exporter and importer for discussions [@ericof] #6
