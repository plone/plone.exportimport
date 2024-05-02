# Changelog

<!--
   You should *NOT* be adding new change log entries to this file.
   You should create a file in the news directory instead.
   For helpful instructions, please see:
   https://github.com/plone/plone.releaser/blob/master/ADD-A-NEWS-ITEM.rst
-->

<!-- towncrier release notes start -->

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
