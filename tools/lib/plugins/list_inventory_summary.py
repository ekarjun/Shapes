from porch_api_lib import Plugin

class ListInventorySummary(Plugin):
    """ List resource inventory summary
    """
    SHORT_OPTION = "-L"
    LONG_OPTION = "--list-inventory"

    def run(self):
        self.print_resource_type_inventory()
        self.print_inventory()

    def print_inventory(self):
        self.heading('current resource inventory')
        self.count('/type-artifacts')
        self.count('/resource-types')
        self.count('/products?includeInactive=true')
        self.count('/resources')
        self.count('/relationships')
        self.count('/domains')
        self.count('/resource-providers')
        self.count('/tag-keys')

    def count(self, path, entity = None):
        entity = entity or path.replace('/', '').replace('-', ' ')
        n = self.mget(path).json()['total']
        print '%6d %s' % (n, entity)

    def print_resource_type_inventory(self):
        self.heading('resource type inventory')
        types = self.mget('/resource-types').json()['items']
        for t in sorted(types, key=lambda rt: rt['uri']):
            print '  %26s (%s)' % (t['uri'].rpartition('.')[2], t['uri'])

