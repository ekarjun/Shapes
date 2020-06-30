from porch_api_lib import Plugin


class DomainsCreate(Plugin):
    """ Add a domain.
    Address is phony.
    The domain info is to be provided in the following format "<title>,<type>,<access-url>,<prop1>,<value1>,<prop2>,<value2>...".
    Type should be one of the supported domain type. List supported domain type with --domain-types.
    """
    LONG_OPTION = "--domains-create"
    PARAM_NAME = 'Domain info'

    def run(self, info):
            details = [d.strip() for d in info.split(",")]
            if len(details) %2 != 1 or len(details) < 3:
                self.errexit("Domain details tuple %s has incorrect length (should >= 3 and not be even)" % (details,))
            ((title, typ, url), props) = (details[:3], details[3:])

            domain = self.add("Domain", "/domains", dict(
                title=title,
                accessUrl=url,
                properties = {props[i]: props[i+1] for i in range(0, len(props), 2)},
                address=dict(
                    city="Petaluma",
                    zip=94954,
                    street="1383 N McDowell Ave, Ste 300",
                    state="CA",
                    country="USA",
                    latitude=38.285762,
                    longitude=-122.660017
                ),
                rpId=self.get_resource_provider_by_type(typ)['id']
            ))

