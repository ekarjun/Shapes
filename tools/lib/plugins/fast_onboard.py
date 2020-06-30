from json import loads, dumps
from commands import getstatusoutput
import time
import sys

from porch_api_lib import Plugin, PorchApiLib
from save_baseline import BaselineQuery


class GitHelpers(PorchApiLib):

    TMP_DIR = '/tmp/fast-onboard-git-repo'
    BRANCH = "fast-onboard"
    PRODUCTION_BRANCH = "production"

    def get_git_url(self):
        self.heading("Find asset manager Git URL for models", False)
        url = [
            a['externalGitUrl'] for a in self.aget("/areas").json()['items']
            if a['name'] == 'model-definitions'
        ][0]
        print '  Git URL: %s' % url
        return url

    def cmd(self, cmd, err):
        ec, out = getstatusoutput(cmd)
        assert ec == 0, "%s: %s" % (err, out)
        return out

    def fresh_git_clone(self, url):
        self.heading("Preparing fresh git tree", False)

        # clean target git tree directory
        assert self.TMP_DIR.startswith("/tmp/"), "Git dir must be /tmp to avoid accidental removal of important things"
        self.cmd("rm -fr %s" % self.TMP_DIR,
                 "Could not remove dir %s" % self.TMP_DIR)

        # clone git tree into branch for fast onboarding
        self.cmd('git clone %s %s' % (url, self.TMP_DIR),
                 "Could not clone git tree")
        if self.has_remote_branch():
            self.cmd('cd %s; git push origin --delete %s' % (self.TMP_DIR, self.BRANCH),
                     "Could not delete remote branch %s" % self.BRANCH)
        self.cmd('cd %s; git checkout -b %s origin/%s' % (self.TMP_DIR, self.BRANCH, self.PRODUCTION_BRANCH),
                 "Could not switch to branch %s" % self.BRANCH)
        print "  Cloned git tree into %s as branch %s" % (self.TMP_DIR, self.BRANCH)

    def has_remote_branch(self):
        branches = self.cmd('cd %s; git branch -r' % self.TMP_DIR,
                            'Could not list remote branches').splitlines()
        return len([b for b in branches if b.strip() == 'origin/%s' % self.BRANCH]) == 1

    def commit_and_submit_pr(self):
        self.heading("Submitting pull request", False)
        self.cmd("cd %s; git add ." % self.TMP_DIR,
                 "Could not add files")
        self.cmd('cd %s; git commit -m "fast onboard overlay added"' % self.TMP_DIR,
                 "Could not commit")
        self.cmd('cd %s; git push origin %s' % (self.TMP_DIR, self.BRANCH),
                 "Failed to push branch changes to asset manager git server")
        req = dumps(dict(branch=self.BRANCH, title="Fast onboard pull request"))
        rep = self.apost('/areas/model-definitions/pullrequests', req)
        print '  PR request submitted: %d' % rep.status_code
        assert rep.status_code < 210, "Pull request submission failed: %s" % rep.text
        pr_id = rep.json()['requestId']
        print '  PR request id: %s' % pr_id
        return pr_id

    def wait_for_pr_validation(self, pr_id):
        self.heading("Wait till pull request is validated")
        while True:
            res = self.aget('/areas/model-definitions/pullrequests/%s' % pr_id)
            assert res.status_code == 200, "Pull request %s not found on server" % pr_id
            pr = res.json()
            if pr['status'] == 'accepted':
                break
            elif pr['status'] == 'pending':
                time.sleep(1)
                print '.',
            elif pr['status'] == 'rejected':
                print 'Pull request was rejected:'
                print pr['reason']
                sys.exit(1)
        print '  Pull request was accepted'


class FastOnboard(Plugin, BaselineQuery, GitHelpers):
    """ On-board additive content from overlay directory <dir> and optionally instantiate via template <template>
        with properties given in <properties> JSON string. Example:
        --fast-onboard 'tmp,tosca.serviceTemplates.MyTemplate,{"param1": 12, "param2": "foo"}'
    """
    LONG_OPTION = "--fast-onboard"
    PARAM_NAME = "<dir>[,<type>,<properties>]"

    def run(self, param):
        dirname, to_activate, properties = self.parse_param(param)
        baseline = self.load_baseline()
        git_url = self.get_git_url()
        self.onboard_types(git_url, dirname, baseline['types'])
        product_map = self.automake_new_products(old_types=baseline['types'])

        if to_activate:
            try:
                product_id = product_map[to_activate]
            except KeyError, e:
                print '  ERRRO: provided template URI %s is not found in %s' % (to_activate, product_map.keys())
                sys.exit(1)
            res_id = self.activate_resource(product_id, properties)
            self.wait_till_active(res_id)

        print '\nSuccess'

    def parse_param(self, param):
        print '    parsing input param %s' % param
        args = param.split(",", 2)
        dirname = args[0]
        to_activate = None if len(args) < 2 else args[1]
        try:
            properties = dict() if len(args) < 3 else loads(args[2])
        except ValueError, e:
            print 'ERROR: %s cannot be parsed as json: %s' % (args[2], e)
            sys.exit(1)
        return dirname, to_activate, properties

    def onboard_types(self, url, dirname, old_types):
        self.heading("Onboard files from overlay dir %s" % dirname)
        self.fresh_git_clone(url)
        self.copy_overlay(dirname)
        pr_id = self.commit_and_submit_pr()
        self.wait_for_pr_validation(pr_id)
        self.wait_till_new_types_onboarded(old_type_count=len(old_types))

    def copy_overlay(self, dirname):
        self.heading("Copying files from overlay dir %s" % dirname, False)
        self.cmd("cp -r %s/ %s" % (dirname, self.TMP_DIR),
                 "Could not copy files from %s to %s" % (dirname, self.TMP_DIR))
        print "  Copied all files into git repo dir"

    def wait_till_new_types_onboarded(self, old_type_count):
        self.heading("Wait till new types show up")
        while True:
            new_type_count = len(self.mget('/type-artifacts').json()['items'])
            if new_type_count > old_type_count:
                break
            print '  Waiting a bit more...'
            time.sleep(1)
        print '  Ok, I see them'

    def automake_new_products(self, old_types):
        self.heading("Auto-creating products")
        # auto-make new products for only the newly onboarded templates
        olds = set(old_types)
        types = self.mget('/type-artifacts').json()['items']
        new_template_urls = [
            t['uri'] for t in types
            if t['uri'] not in olds and t['artifactType'] == 'ServiceTemplate'
        ]
        print '  New templates to get products: %s' % (new_template_urls,)

        print '  Product ids:'
        template_url_to_product_id_map = {}
        for template_url in new_template_urls:
            template = self.mget('/type-artifacts/%s' % template_url).json()
            implements_url = template['model']['CompiledServiceTemplate']['implements']['path']
            print "This template implements resource_type %s" % implements_url

            product = dict(
                resourceType=implements_url,
                title='Product for template %s' % template_url,
                description='Auto-created product for template %s' % template_url,
                active=True,
                domain='built-in',
                providerData=dict(template=template_url)
            )

            rep = self.mpost('/products', dumps(product))
            assert rep.status_code < 210, "Failed to create product: %s" % rep.text
            id = rep.json()['id']
            print '    %s - %s' % (id, template_url)
            template_url_to_product_id_map[template_url] = id

        return template_url_to_product_id_map

    def activate_resource(self, product_id, properties):
        data = dict(
            label='FastOnboarded',
            productId=product_id,
            properties=properties
        )
        print '  Attempting to create new resource with:\n%s' % (dumps(data, indent=4))
        res = self.mpost('/resources', dumps(data))
        print '    Response code: %s' % res.status_code
        assert res.status_code == 201, '  Resource creation request failed: %s' % res.text
        r = res.json()
        print '    Resource created:\n%s' % dumps(r, indent=4)
        return r['id']

    def wait_till_active(self, resource_id, for_max_seconds=60, interval_seconds=2):
        self.heading("Waiting till resource becomes active")
        t_max = time.time() + for_max_seconds
        while time.time() < t_max:
            r = self.mget('/resources/%s' % resource_id).json()
            print '  Resource %s:\n%s' % (resource_id, dumps(r, indent=4))
            if r['orchState'] == 'active':
                return
            elif r['orchState'] == 'failed':
                print 'ERROR: resource failed activation:\n%s' % r['reason']
                sys.exit(1)
            time.sleep(interval_seconds)
        print 'ERROR: resource did not activate in %s seconds' % for_max_seconds
