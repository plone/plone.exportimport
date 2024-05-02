from pathlib import Path
from setuptools import find_packages
from setuptools import setup


long_description = f"""
{Path("README.md").read_text()}\n
{Path("CHANGES.md").read_text()}\n
"""

setup(
    name="plone.exportimport",
    version="1.0.0a3",
    description="Plone content export / import support",
    long_description=long_description,
    long_description_content_type="text/markdown",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Web Environment",
        "Framework :: Plone",
        "Framework :: Plone :: 6.0",
        "Framework :: Plone :: Core",
        "Framework :: Zope :: 5",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    keywords="Plone CMF Python Zope CMS",
    author="Plone Foundation",
    author_email="releasemanager@plone.org",
    url="https://plone.org",
    license="GPL version 2",
    project_urls={
        "Homepage": "https://plone.org",
        "Documentation": "https://6.docs.plone.org",
        "Source": "https://github.com/plone/plone.exportimport",
        "Issues": "https://github.com/plone/plone.exportimport/issues",
    },
    packages=find_packages("src"),
    namespace_packages=["plone"],
    package_dir={"": "src"},
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "python-dateutil",
        "plone.api",
        "plone.app.contenttypes",
        "plone.app.dexterity",
        "plone.app.discussion",
        "plone.app.multilingual",
        "plone.app.redirector",
        "plone.app.textfield",
        "plone.app.users",
        "plone.base",
        "plone.dexterity",
        "plone.namedfile",
        "plone.restapi",
        "plone.uuid",
        "Products.CMFEditions",
        "Products.CMFPlone",
        "Products.PlonePAS",
        "Products.PortalTransforms",
        "setuptools",
        "z3c.relationfield",
        "zc.relation",
        "Zope",
    ],
    extras_require={
        "test": [
            "zest.releaser[recommended]",
            "zestreleaser.towncrier",
            "plone.app.testing",
            "plone.restapi[test]",
            "plone.testing",
            "pytest",
            "pytest-cov",
            "pytest-plone>=0.2.0",
        ]
    },
    entry_points={
        "z3c.autoinclude.plugin": ["target = plone"],
        "console_scripts": [
            "plone-exporter = plone.exportimport.cli:exporter_cli",
            "plone-importer = plone.exportimport.cli:importer_cli",
        ],
    },
)
