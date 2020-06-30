import sys
import time
from json import dumps

from porch_api_lib import Plugin

from save_baseline import BaselineQuery
from fast_onboard import GitHelpers


class RevertToBaseline(Plugin, BaselineQuery, GitHelpers):
    """ Revert to a baseline, saved by the -S (--save-baseline) command
    """
    SHORT_OPTION = "-R"
    LONG_OPTION = "--revert-to-baseline"

    def run(self):
        baseline = self.load_baseline()

        # first, we identify what top-level resources if any have been crated since baseline
        self.terminate_new_resources(baseline['resources'])
        self.delete_new_products(baseline['products'])
        self.roll_back_types(baseline['commitHash'])
        print '\nSuccess'

    def terminate_new_resources(self, old_resources):
        self.heading("Terminating resources added since baseline")
        # we are looking for the resources that are:
        # - listed in new but not in old
        # - not discovered resources (double-check)
        # - not in terminated porch state (which none of them should really be)
        # - do not have dependents (in other words, top-level objects)

        # find what is new and not discovered
        old_set = set(old_resources)
        resources = self.mget('/resources').json()['items']
        candidates = set([r['id'] for r in resources if r['id'] not in old_set and not r['discovered']])

        # narrow it down to those that have no incoming containment relationships
        relationships = self.mget('/relationships').json()['items']
        targets = set(r['target'] for r in relationships)

        to_delete = candidates.difference(targets)
        print "  new resources to delete: %s" % self.iterable_to_str(to_delete)

        # terminate such resources one-by-one
        for id in to_delete:
            print "    terminating resource %s" % id
            self.mdelete('/resources/%s' % id)

        # wait till all are terminated
        try_again = True
        while try_again:
            time.sleep(1)
            try_again = False
            for id in to_delete:
                rep = self.mget('/resources/%s' % id)
                if rep.status_code == 404:
                    try_again = False
                    continue
                elif rep.status_code == 200:
                    r = rep.json()
                    if r['orchState'] == 'failed':
                        print '  Failed to terminate resource %s: %s' % (id, r)
                        sys.exit(1)
                    elif r['orchState'] == 'terminating':
                        try_again = True
                        break
                    else:
                        print '  <<<< unhandled state: %s >>>>' % r['orchState']
                        sys.exit(1)

    def delete_new_products(self, old_products):
        self.heading("Deleting products added since baseline")
        old_set = set(old_products)
        products = self.mget('/products?includeInactive=true').json()['items']
        to_delete = set(p['id'] for p in products if p['id'] not in old_set)
        print '  products to delete: %s' % self.iterable_to_str(to_delete)

        for id in to_delete:
            print '    deleting product %s' % id
            res = self.mdelete('/products/%s' % id)
            print '      response: %s' % res.status_code
            assert res.status_code == 204, 'Could not delete product %s: %s' % (id, res.text)
            print '        deleted'

    def iterable_to_str(self, lst):
        return ", ".join(str(e) for e in lst) if lst else "<none>"

    def roll_back_types(self, commit_hash):
        self.heading("Rolling back type layer to commit hash %s" % commit_hash)
        git_url = self.get_git_url()
        self.fresh_git_clone(git_url)

        # we will undo the change by create a reverse patch and undoing it
        self.cmd('cd %s; git diff HEAD %s > ../fast-onboard-rollback.patch' % (self.TMP_DIR, commit_hash),
                 'Failed to create reverse patch file')
        patch_size = int(self.cmd('cd %s; cat ../fast-onboard-rollback.patch | wc -c' % self.TMP_DIR,
                                  "Could not read patch file").strip())
        if patch_size == 0:
            print '  Nothing to roll back'
        else:
            self.cmd('cd %s; git apply ../fast-onboard-rollback.patch' % self.TMP_DIR,
                     'Failed to apply reverse patch file')
            self.cmd('cd %s; git commit -am "fast onboard rollback"' % self.TMP_DIR,
                     'Failed to commit')
            self.cmd('cd %s; git push origin %s' % (self.TMP_DIR, self.BRANCH),
                     'Failed to push branch rollback changes to asset manager git server')
            req = dumps(dict(branch=self.BRANCH, title="Fast onboard rollback pull request"))
            rep = self.apost('/areas/model-definitions/pullrequests', req)
            print '  PR request submitted: %d' % rep.status_code
            assert rep.status_code < 210, "Pull request submission failed: %s" % rep.text
            pr_id = rep.json()['requestId']
            print '  PR request id: %s' % pr_id
            self.wait_for_pr_validation(pr_id)
            print '  Types are rolled back'
