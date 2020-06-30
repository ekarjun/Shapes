import json
import pprint
import sys
import time
try:
    import requests
except ImportError:
    print 'Please install the "requests" python library, e.g., by'
    print 'sudo apt-get install python-requests # on Ubuntu systems'
    print 'sudo pip install requests # on most Linux systems and Mac'
    sys.exit(1)


class PorchApiConfigJSONEncoder (json.JSONEncoder):
    def default (self, o):
        jsonable = o.JSONEncoder (flat=False)
        return jsonable

class PorchApiConfig:
    # auth is either None or a map
    # map should have authType and type specific values
    # Currently only authType == "token" is supported
    # For token type, the attribute "token" should be defined

    def __init__(self, protocol = "http", host = "localhost", port = "8181", auth = None):
        self.protocol = protocol
        self.host = host
        self.port = port
        self.auth = auth
        self.url_base = self.protocol + "://" + self.host + ":" + str(self.port)
        self.verify = False

    DEFAULT_CFG_FILE = "default.json"

    def write(self, fileName):
        fp = open (fileName, 'w')
        json.dump (self, fp, cls = PorchApiConfigJSONEncoder, indent=4)
        fp.close()

    @staticmethod
    def read(fileName):
        fp = open(fileName, 'r')
        cfgMap = json.load(fp)
        cfg = PorchApiConfig(cfgMap['protocol'],
            cfgMap['host'],
            cfgMap['port'],
            cfgMap['auth'])

        return cfg

    def JSONEncoder (self, **kwarg):
        jsonable = {}
        jsonable ["protocol"] = self.protocol
        jsonable ["host"] = self.host
        jsonable ["port"] = self.port
        jsonable ["auth"] = self.auth
        return jsonable

    def print_config(self):
        print("\nPlanet Orchestrate System: %s\n") % (self.url_base)

    def getAuthHeader(self):
        authHeader = {}
        if self.auth is not None:
           if (self.auth.get("authType") == "token"):
               authHeader["X-Auth-Token"] = self.auth.get("token")
        return authHeader


class PorchApiLib:

    cfg = PorchApiConfig()
    market_path = '/bpocore/market/api/v1'
    assets_path = '/bpocore/asset-manager/api/v1'
    rest_path = '/bpocore/rest-server/api/v1'

    vm_type_uri = 'tosca.resourceTypes.VirtualMachine'
    keypair_type_uri = 'tosca.resourceTypes.KeyPair'
    security_group_type_uri = 'tosca.resourceTypes.SecurityGroup'
    image_type_uri = 'tosca.resourceTypes.Image'
    network_type_uri = 'tosca.resourceTypes.Network'
    subnet_type_uri = 'tosca.resourceTypes.Subnet'
    sg_type_uri = 'tosca.resourceTypes.SecurityGroup'
    vdns_type_uri = 'tosca.resourceTypes.VirtualDns'
    uniport_type_uri = 'tosca.resourceTypes.UniPort'
    e2dc_type_uri = 'tosca.resourceTypes.E2dcEvpl'
    ne_type_uri = 'tosca.resourceTypes.NetworkElement'
    gw_port_type_uri = 'tosca.resourceTypes.GatewayPort'
    phys_xc_type_uri = 'tosca.resourceTypes.PhysicalXc'
    stack_type_uri = 'tosca.resourceTypes.HeatStack'
    vcpe_ems_type_uri = 'tosca.resourceTypes.VcpeEms'
    vcpe_type_uri = 'tosca.resourceTypes.Vcpe'
    p2p_vcpe_type_uri = 'tosca.resourceTypes.P2pVcpe'
    vepc_type_uri = 'tosca.resourceTypes.Vepc'
    mzone_type_uri = 'tosca.resourceTypes.Mzone'

    # Get the full URL w/o options or query parameters
    # componentPath - A component (e.g., market) path including the initial slash
    # resourcePath - A resource (e.g., /products) including the initial slash
    def getUrl(self, componentPath, resourcePath):
        url = self.cfg.url_base + componentPath + resourcePath
        return url

    def heading(self, msg, main_heading=True):
        if main_heading: print '\n' + msg + ':\n' + '-' * 78
        else: print '\n  %s:' % msg

    def getHeaders(self):
        headers = {'content-type': 'application/json', 'accept': 'application/json'}
        headers.update(self.cfg.getAuthHeader())
        return headers

    def mget(self, path):
        return requests.get(self.getUrl(self.market_path, path),
            verify = self.cfg.verify,
            headers = self.getHeaders())

    def mpost(self, path, data = None):
        return requests.post(self.getUrl(self.market_path, path), data = data,
            headers = self.getHeaders(),
            verify = self.cfg.verify)

    def mpatch(self, path, data = None):
        return requests.patch(self.getUrl(self.market_path, path), data = data,
            headers = self.getHeaders(),
            verify = self.cfg.verify)

    def mput(self, path, data = None):
        return requests.put(self.getUrl(self.market_path, path), data = data,
            headers = self.getHeaders(),
            verify = self.cfg.verify)

    def mdelete(self, path):
        return requests.delete(self.getUrl(self.market_path, path),
            verify = self.cfg.verify,
            headers = self.getHeaders())

    def add(self, what, path, data):
        self.heading("Adding %s" % what)
        r = self.mpost(path, json.dumps(data))
        print "  result: %s\n" % r.status_code
        assert r.status_code < 210
        obj = r.json()
        print "  %s:" % what
        pprint.pprint(obj)
        return obj

    def aget(self, path):
        return requests.get(self.getUrl(self.assets_path, path),
            verify = self.cfg.verify,
            headers = self.getHeaders())

    def apost(self, path, data = None):
        return requests.post(self.getUrl(self.assets_path, path),
            data = data, headers = self.getHeaders(), verify = self.cfg.verify)

    def adelete(self, path):
        return requests.delete(self.getUrl(self.assets_path, path),
            headers = self.getHeaders(),
            verify = self.cfg.verify)

    def errexit(self, msg):
        print >> sys.stderr, "*ERROR: ", msg
        sys.exit(1)

    def check_ok(self, res, msg):
        code = res.status_code
        if code < 200 or code >= 300:
            print >> sys.stderr, msg
            print >> sys.stderr, "Unexpected result: %s %s" % (code, res.reason)
            print >> sys.stderr, res.content
            return False
        else:
            return True


class Plugin(PorchApiLib):

    # at least one of the following has to be overwritten by a plugin
    SHORT_OPTION = None
    LONG_OPTION = None
    PARAM_NAME = None # or can be a string placeholder

    def run(self, *args):
        """ the implementation of the plugin """
        pass

    def monitor_resource_state(self, id, for_max_seconds=60, interval_seconds=5):
        self.heading('monintoring progress of resource %s' % id)
        t_max = time.time() + for_max_seconds
        while (time.time() < t_max):
            self.print_resource_status(id)
            time.sleep(interval_seconds)

    def print_resource_status(self, id):
        self.heading('state at %s:' % time.ctime())
        info = self.mget('/resources/%s' % id).json()
        pprint.pprint(info, indent=4)
        self.print_outgoing_relationships(id)

    def print_outgoing_relationships(self, resource_id, rels=None):
        # TODO the api should allow a more targeted fetch, instead of fetching all
        rels = rels or self.mget('/relationships').json()['items']
        outs = [r for r in rels if r['sourceId'] == resource_id]
        # pprint.pprint(outs)
        print '\n    outgoing relationships (satisfied requirements):'
        for o in outs:
            print '      %10s  ---(%s)---> %s:%s' % (
                o['requirementName'], o['relationshipTypeId'].rpartition('.')[2],
                o['targetId'], o['capabilityName'])

    def get_product_map(self):
        prods = self.mget('/products?includeInactive=true').json()['items']
        # pprint.pprint(prods)
        return dict([(p['id'], p['domainId']) for p in prods])

    def get_resource_by_type_and_domain(self, type_uri, domain_id):
        # TODO lookup could be more tightly filtered by API
        product_map = self.get_product_map()
        things = self.mget('/resources?resourceTypeId=%s' % type_uri).json()['items']
        filtered = [t for t in things if product_map[t['productId']] == domain_id]
        print '  found %d %s resources' % (len(filtered), type_uri.rpartition('.')[2])
        #pprint.pprint(things)
        return things

    def get_resource_by_label_and_type(self, resource_label, resource_type_uri):
        self.heading('find resource %s of type %s'  % (resource_label, resource_type_uri))
        resources = [u for u in
                     self.mget("/resources?resourceTypeId=%s" % resource_type_uri).json()["items"]
                     if u["label"] == resource_label
        ]
        assert len(resources) == 1
        resource = resources[0]
        print "  Market ID: " + resource["id"]
        print "  Provider ID: " + resource["providerResourceId"]
        return resource

    def get_resource_by_provider_resource_id(self, domain_id, provider_resource_id):
        self.heading('find resource with provider id %s in domain %s'  % (provider_resource_id, domain_id))
        reply = self.mget("/resources?domainId=%s&providerResourceId=%s" % (domain_id, provider_resource_id))
        assert reply.status_code == 200
        resource = reply.json()['items'][0]
        print "  Market ID: " + resource["id"]
        print "  Provider ID: " + resource["providerResourceId"]
        return resource

    def get_resource(self, resource_id):
        self.heading('find resource with id %s'  % (resource_id))
        reply = self.mget("/resources/%s" % (resource_id))
        assert reply.status_code == 200
        resource = reply.json()
        return resource

    def get_resource_dependencies(self, resource_id):
        self.heading('find resources which resource %s depends on'  % resource_id)
        reply = self.mget("/resources/%s/dependencies?recursive=true" % resource_id)
        assert reply.status_code == 200
        resources = reply.json()['items']
        return resources

    def get_outgoing_relationships(self, resource_id):
        self.heading('find outgoing relationships from resource %s'  % resource_id)
        reply = self.mget("/relationships?q=sourceId:%s" % (resource_id))
        assert reply.status_code == 200
        relationships = reply.json()['items']
        return relationships

    def get_products_by_type_and_title(self, resource_type_uri, title = None):
        return [
            p for p in self.mget('/products?includeInactive=true').json()['items']
            if p['resourceType'] == resource_type_uri and
            (title is None or p['title'] == title)
        ]

    def get_products_by_type_and_domain(self, resource_type_uri, domain_id):
        return [
            p for p in self.mget('/products?includeInactive=true').json()['items']
            if p['resourceTypeId'] == resource_type_uri and p['domainId'] == domain_id
        ]

    def monitor_resource_state(self, id, for_max_seconds=60, interval_seconds=5):
        self.heading('monintoring progress of resource %s' % id)
        t_max = time.time() + for_max_seconds
        while (time.time() < t_max):
            self.print_resource_status(id)
            time.sleep(interval_seconds)

    def get_resource_provider_by_type(self, domain_type):
        self.heading('find resource provider for type %s' % domain_type)
        rps = self.mget("/resource-providers?q=domainType:%s" % domain_type).json()["items"]
        assert len(rps) >= 1
        rp = rps[0]
        return rp

