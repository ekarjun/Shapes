import sys
import commands

from porch_api_lib import Plugin

class GraphResources(Plugin):
    """ Create and view a resource graph
    """
    SHORT_OPTION = "-G"
    LONG_OPTION = "--graph-resources"

    DIR = "."
    FILE_PREFIX = "porch-resource-graph"
    DOT_FILE = DIR + "/" + FILE_PREFIX + ".dot"
    PDF_FILE = DIR + "/" + FILE_PREFIX + ".pdf"

    def run(self):
        prods = self.get_all_products()
        ress = self.get_all_resources()
        rels = self.get_all_relationships()
        self.create_dot_file(prods, ress, rels)
        self.make_pdf()
        self.launch_viewer()

    def get_all_products(self):
        self.heading('reading all products')
        prods = self.mget('/products?includeInactive=true').json()['items']
        print "Got %d products" % len(prods)
        return prods

    def get_all_resources(self):
        self.heading('reading all resources')
        ress = self.mget('/resources').json()['items']
        print "Got %d resources" % len(ress)
        return ress

    def get_all_relationships(self):
        self.heading('reading all relationships')
        rels = self.mget('/relationships').json()['items']
        print "Got %d relationships" % len(rels)
        return rels

    def create_dot_file(self, prods, ress, rels):
        prod_type_map = dict((p["id"], p["resourceTypeId"].rpartition(".")[2]) for p in prods)
        nodes = dict((res["id"], res) for res in ress)
        self.heading('creating graphviz dot file')
        with file(self.DOT_FILE, "w+") as f:
            print >> f, 'digraph porch_resource_graph {'
            print >> f, '        rankdir=TB;'
            #print >> f, '        size="64,40"'
            print >> f, '        node [shape=rectangle,style="rounded,filled"];'
            for res in ress:
                # print >> f, '        "%s" [label="%s&#92;n%s&#92;n%s"];' % \
                print >> f, '        "%s" [fillcolor="%s",label=<<FONT FACE="Areal"><TABLE BORDER="0" CELLSPACING="0"><TR><TD><B> %s </B></TD></TR><TR><TD><FONT POINT-SIZE="12.0">%s</FONT></TD></TR><TR><TD><FONT POINT-SIZE="12.0">%s</FONT></TD></TR></TABLE></FONT>>];' % \
                            (res["id"][24:], self.get_color(res["orchState"]),
                             res.get("label"), prod_type_map[res["productId"]], res["id"][24:])
            for rel in rels:
                a = nodes[rel["sourceId"]]["id"][24:]
                z = nodes[rel["targetId"]]["id"][24:]
                l = rel["relationshipTypeId"].rpartition(".")[2]
                print >> f, '        "%s" -> "%s" [ label = "%s" ];' % (a, z, l)
            print >> f, '}'

    def get_color(self, _os):
        if _os == "active": return "#bbffcc"
        elif _os == "activating": return "#bbffff"
        elif _os == "failed": return "#ffbbbb"
        elif _os == "inactive": return "#ffbbff"
        else:
            print "pick color for: ", _os
            return "#cccccc"

    def make_pdf(self):
        code, out = commands.getstatusoutput("dot -Tpdf %s > %s" % (self.DOT_FILE, self.PDF_FILE))
        if code != 0:
            print >> sys.stderr, "Failed to run dot (may be graphviz is not installed?): %s" % out
            sys.exit(code)

    def launch_viewer(self):
        system = commands.getoutput("uname -s")
        if system.startswith("Darwin"):
            # launch pdf using Mac OS X Preview
            cmd = "open -g -a Preview %s" % self.PDF_FILE
            print "Calling %s" % cmd
            code, out = commands.getstatusoutput(cmd)
            if code != 0:
                print >> sys.stderr, "Could not launch pdf viewer: %s" % out
                sys.exit(1)


