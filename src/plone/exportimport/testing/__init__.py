from plone.app.contenttypes.testing import PLONE_APP_CONTENTTYPES_FIXTURE
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PloneSandboxLayer
from plone.testing.zope import WSGI_SERVER_FIXTURE


class ExportImportLayer(PloneSandboxLayer):
    defaultBases = (PLONE_APP_CONTENTTYPES_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        import plone.exportimport
        import plone.volto

        self.loadZCML(package=plone.volto)
        self.loadZCML(package=plone.exportimport)

    def setUpPloneSite(self, portal):
        st = portal.portal_setup
        st.runAllImportStepsFromProfile("plone.volto:default")

        # Enable plone.constraintypes behavior,
        # which is not enabled by default in plone.volto
        portal.portal_types.Document.behaviors += ("plone.constraintypes",)


FIXTURE = ExportImportLayer()


INTEGRATION_TESTING = IntegrationTesting(
    bases=(FIXTURE,),
    name="ExportImportLayer:IntegrationTesting",
)

FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(FIXTURE, WSGI_SERVER_FIXTURE),
    name="ExportImportLayer:FunctionalTesting",
)
