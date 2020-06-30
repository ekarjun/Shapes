from json import dump, load
import sys

from porch_api_lib import Plugin, PorchApiLib


BASELINE_FILENAME = '.porch-base-line'


class BaselineQuery(PorchApiLib):

    def get_state(self):
        self.heading('Collecting current type/product/instance layer data', False)
        data = dict(
            commitHash=self.get_commit_hash(),
            types=self.get_types(),
            products=self.get_products(),
            resources=self.get_resources()
        )
        return data

    def get_commit_hash(self):
        return self.aget('/areas/model-definitions').json()['commitHash']

    def get_types(self):
        types = self.mget('/type-artifacts').json()['items']
        return sorted(t['uri'] for t in types)

    def get_products(self):
        products = self.mget('/products?includeInactive=true').json()['items']
        return sorted(p['id'] for p in products)

    def get_resources(self):
        resources = self.mget('/resources').json()['items']
        return sorted(r['id'] for r in resources if not r['discovered'])

    def load_baseline(self):
        self.heading('Loading baseline file', False)
        fname = BASELINE_FILENAME
        try:
            with file(fname, 'r') as f:
                baseline = load(f)
        except IOError, e:
            print >> sys.stderr, "Could not find baseline file %s" % fname
            sys.exit(1)
        print "    loaded %d type ids, %d product ids and %d resource ids from %s" % (
            len(baseline['types']), len(baseline['products']), len(baseline['resources']), fname
        )
        return baseline

    def save_baseline(self):
        data = self.get_state()

        print "    saving %d type ids, %d product ids and %d resource ids into %s" % (
            len(data['types']), len(data['products']), len(data['resources']), BASELINE_FILENAME
        )
        with file(BASELINE_FILENAME, 'w') as f:
            dump(data, f)
        print '    file %s updated' % BASELINE_FILENAME


class SaveBaseline(Plugin, BaselineQuery):
    """ Save a baseline, to be used in conjunction with -R (--revert-to-baseline)
    """
    SHORT_OPTION = "-S"
    LONG_OPTION = "--save-baseline"

    def run(self):
        self.save_baseline()
        print '\nSuccess'

