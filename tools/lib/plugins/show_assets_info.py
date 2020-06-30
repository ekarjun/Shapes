from porch_api_lib import Plugin

class ShowAssetsInfo(Plugin):
    """ Show asset manager key information
    """
    LONG_OPTION = "--show-asset-areas"

    def run(self):

        areas = self.list_areas()

        for area in areas:
            self.show_area(area)

    def list_areas(self):
        self.heading('Areas')
        areas = self.aget('/areas').json()['items']
        print '  Area names: ' + ", ".join(a['name'] for a in areas)
        return areas

    def show_area(self, area):

        name = area['name']
        self.heading("Asset area '%s'" % name)

        details = self.aget('/areas/%s' % name).json()

        print '  Head revision: %s' % details['commitHash']

        print '  External GIT URL: %s' % area['externalGitUrl']
        print '  Internal GIT URL: %s' % area['internalGitUrl']

        print '  To clone repo externally: git clone %s' % area['externalGitUrl']
        print '  To clone repo externally: git clone %s' % area['externalGitUrl']

        print '  Pending pull requests:'
        prs = self.aget('/areas/%s/pullrequests' % name).json()['items']
        if prs:
            self.print_pull_requests(prs)
        else:
            print '    no pull requests'

        print '  All pull requests:'
        prs = self.aget('/areas/%s/pullrequests?pendingOnly=false' % name).json()['items']
        if prs:
            self.print_pull_requests(prs)
        else:
            print '    no pull requests'

    def print_pull_requests(self, prs):
        fmt = '    %24s %10s  %-30s  %12s   %24s   %s'
        print fmt % ('Requested', 'Status', 'Title', 'Commit Hash',  'Commit Date', 'Author')
        for pr in reversed(prs):
            title = pr['title']
            title = title if len(title) <= 30 else title[:18] + "..." + title[-9:]
            print fmt % (pr['requestDate'], pr['status'], title, pr['commitHash'][:12], pr['commitDate'], pr['email'])
            if pr['status'] == 'rejected':
                lines = pr['reason'].splitlines()
                print '      reason: %s' % lines[0]
                for line in lines[1:]:
                    print '              %s' % line
