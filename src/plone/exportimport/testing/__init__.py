from plone.app.contenttypes.testing import PLONE_APP_CONTENTTYPES_FIXTURE
from plone.app.testing import IntegrationTesting
from plone.app.testing import PloneSandboxLayer


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


FIXTURE = ExportImportLayer()


INTEGRATION_TESTING = IntegrationTesting(
    bases=(FIXTURE,),
    name="ExportImportLayer:IntegrationTesting",
)
