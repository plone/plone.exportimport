# Changelog

<!--
   You should *NOT* be adding new change log entries to this file.
   You should create a file in the news directory instead.
   For helpful instructions, please see:
   https://github.com/plone/plone.releaser/blob/master/ADD-A-NEWS-ITEM.rst
-->

<!-- towncrier release notes start -->

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
