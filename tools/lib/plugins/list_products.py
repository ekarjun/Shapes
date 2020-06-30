from porch_api_lib import Plugin

class ListProducts(Plugin):
    """ List products
    """
    SHORT_OPTION = "-P"
    LONG_OPTION = "--list-products"

    def run(self):
        self.heading('products per resource type')
        uris = [rt['id'] for rt in self.mget('/resource-types').json()['items']]
        p_groups = [self.mget('/resource-types/%s/products?includeInactive=true' % u).json()['items'] for u in uris]
        for (uri, count, ps) in sorted([(line[0], len(line[1]), line[1]) for line in zip(uris, p_groups)], key=lambda e: -e[1]):
            print '%d %s(s)' % (count, uri)
            for p in ps:
                #print p
                print '     %s   %-32s %-36s %-10s' % (p['id'], p['title'], p['domainId'], p['providerData'])

