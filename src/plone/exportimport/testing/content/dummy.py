from plone.autoform import directives
from plone.autoform.interfaces import IFormFieldProvider
from plone.dexterity.content import Container
from plone.supermodel.model import Schema
from zope import schema
from zope.interface import implementer
from zope.interface import provider


class IDummyContent(Schema):
    """Schema with fields protected by custom read and write permissions."""

    secure_field = schema.TextLine(
        title="Secure field",
        description="Secure field.",
        required=False,
    )

    secure_setting = schema.Bool(
        title="Secure Setting",
        description="Secure setting.",
        required=False,
        default=True,
    )

    directives.read_permission(
        secure_field="plone.exportimport.testing.dummy.view",
        secure_setting="plone.exportimport.testing.dummy.view",
    )
    directives.write_permission(
        secure_field="plone.exportimport.testing.dummy.edit",
        secure_setting="plone.exportimport.testing.dummy.edit",
    )


@provider(IFormFieldProvider)
class IDummySettings(IDummyContent):
    """Behavior exposing the protected fields, used on the Plone Site root."""


@implementer(IDummyContent)
class DummyContent(Container):
    """Dexterity container that represents a dummy content."""
