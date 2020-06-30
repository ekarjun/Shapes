from porch_api_lib import Plugin

class DeleteResource(Plugin):
    """ Delete a given resource
    """
    SHORT_OPTION = "-d"
    LONG_OPTION = "--del-resource"
    PARAM_NAME = "resourceId"

    def run(self, id):
        self.heading('deleting resource %s' % id)
        r = self.mdelete('/resources/%s' % id)
        print r
