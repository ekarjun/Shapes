from porch_api_lib import Plugin


class DomainsDelete(Plugin):
    """ Delete an existing domain.
    """
    LONG_OPTION = "--domains-delete"
    PARAM_NAME = 'Domain id'

    def run(self, id):
        self.domain_delete(id)

    def domain_delete(self, id):
        self.heading("Deleting domain %s" % id)
        res = self.mdelete("/domains/%s" % id)
        self.check_ok(res, "Failed to delete domain %s" % id)
