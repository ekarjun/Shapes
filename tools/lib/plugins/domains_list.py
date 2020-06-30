from porch_api_lib import Plugin


class DomainsList(Plugin):
    """ List existing domains.
    """
    LONG_OPTION = "--domains-list"

    def run(self):
        domains = self.mget("/domains").json()["items"]
        self.heading("Summary of domains")
        for d in domains:
            fmt = "  %-37s %-30s  %-20s %-30s %s"
            print fmt % ("Id", "Title", "Type", "URL", "Properties")
            print fmt % (d["id"], d["title"], d["domainType"], d["accessUrl"], d["properties"])

