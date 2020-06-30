from porch_api_lib import Plugin

class ListResources(Plugin):
    """ List Resources
    """
    SHORT_OPTION = "-l"
    LONG_OPTION = "--list-resources"

    def run(self):
        self.heading('resources per resource type')
        uris = [rt['id'] for rt in self.mget('/resource-types').json()['items']]
        ris_groups = [self.mget('/resources?resourceTypeId=%s' % u).json()['items'] for u in uris]
        for (uri, count, ris) in sorted([(line[0], len(line[1]), line[1]) for line in zip(uris, ris_groups)], key=lambda e: -e[1]):
            if count == 0:
                continue
            print '%d %s(s)' % (count, uri.rpartition('.')[2])
            for ri in ris:
                # print ri
                print '     %s   %-35s %15s (%-10s)' % (ri['id'], ri.get('label', '-'), ri['orchState'], ri['desiredOrchState'])

