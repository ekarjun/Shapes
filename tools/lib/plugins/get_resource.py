import pprint
import time

from porch_api_lib import Plugin

class GetResource(Plugin):
    """ Get info on given resource
    """
    SHORT_OPTION = "-g"
    LONG_OPTION = "--get-resource"
    PARAM_NAME = "resourceId"

    def run(self, id):
        self.print_resource_status(id)
