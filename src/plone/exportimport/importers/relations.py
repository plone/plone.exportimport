from .base import BaseImporter
from plone import api
from plone.exportimport import logger
from plone.exportimport.utils import relations as utils


class RelationsImporter(BaseImporter):
    name: str = "relations"

    def do_import(self) -> str:
        """Import relations into a Plone Site."""
        data = self._read()
        if data is None:
            return f"{self.__class__.__name__}: No data to import"
        logger.debug(f"- Relations: Read {len(data)} from {self.filepath}")
        results = utils.set_relations(data)
        for item in results:
            # Reindex relations objects in case they contain
            #  `preview_image_link` fields to update the image scales
            api.content.get(UID=item["to_uuid"]).reindexObject()
            api.content.get(UID=item["from_uuid"]).reindexObject()

        return f"{self.__class__.__name__}: Imported {len(results)} relations"
