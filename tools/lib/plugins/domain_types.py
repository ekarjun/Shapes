from porch_api_lib import Plugin


class DomainTypes(Plugin):
    """ List supported domain types.
    """
    LONG_OPTION = "--domain-types"

    def run(self):
        types = self.mget("/domain-types").json()["items"]
        self.heading("Supported domain types")
        fmt = "  %-37s %-20s"
        print fmt % ("Type", "Description")
        for t in types:
            print fmt % (t["name"], t["description"])
