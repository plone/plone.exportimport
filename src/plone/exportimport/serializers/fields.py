from plone.dexterity.interfaces import IDexterityContent
from plone.exportimport.interfaces import IExportImportRequestMarker
from plone.restapi.interfaces import IFieldSerializer
from plone.restapi.serializer.converters import json_compatible
from plone.restapi.serializer.dxfields import DefaultFieldSerializer
from zope.component import adapter
from zope.interface import implementer
from zope.schema.interfaces import IChoice
from zope.schema.interfaces import ICollection
from zope.schema.interfaces import IField
from zope.schema.interfaces import IVocabularyTokenized

import logging

logger = logging.getLogger(__name__)


@adapter(ICollection, IDexterityContent, IExportImportRequestMarker)
@implementer(IFieldSerializer)
class CollectionFieldSerializer(DefaultFieldSerializer):
    def __call__(self):
        """Override default serializer:
        1. Export only the value, not a token/title dict.
        2. Do not drop values that are not in the vocabulary.
           Instead log info so you can handle the data.
        """
        # Binding is necessary for named vocabularies
        if IField.providedBy(self.field):
            self.field = self.field.bind(self.context)
        value = self.get_value()
        value_type = self.field.value_type
        if (
            value is not None
            and IChoice.providedBy(value_type)
            and IVocabularyTokenized.providedBy(value_type.vocabulary)
        ):
            for v in value:
                try:
                    value_type.vocabulary.getTerm(v)
                except LookupError:
                    if v not in [self.field.default, self.field.missing_value]:
                        logger.info(
                            "Term lookup error: %r not in vocabulary %r for field %r of %r",
                            v,
                            value_type.vocabularyName,
                            self.field.__name__,
                            self.context,
                        )
        return json_compatible(value)


@adapter(IChoice, IDexterityContent, IExportImportRequestMarker)
@implementer(IFieldSerializer)
class ChoiceFieldSerializer(DefaultFieldSerializer):
    def __call__(self):
        """Override default serializer:
        1. Export only the value, not a token/title dict.
        2. Do not drop values that are not in the vocabulary.
           Instead log info so you can handle the data.
        """
        # Binding is necessary for named vocabularies
        if IField.providedBy(self.field):
            self.field = self.field.bind(self.context)
        value = self.get_value()
        if value is not None and IVocabularyTokenized.providedBy(self.field.vocabulary):
            try:
                self.field.vocabulary.getTerm(value)
            except LookupError:
                if value not in [self.field.default, self.field.missing_value]:
                    logger.info(
                        "Term lookup error: %r not in vocabulary %r for field %r of %r",
                        value,
                        self.field.vocabularyName,
                        self.field.__name__,
                        self.context,
                    )
        return json_compatible(value)
