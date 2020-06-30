import json
from porch_api_lib import Plugin

class SubmitPullRequest(Plugin):
    """ Submit an asset manager pull request to the model-definitions area,
        using the head revision of the master branch, with the given comment.
    """
    LONG_OPTION = "--submit-pull-request"
    PARAM_NAME = "title"

    def run(self, title):
        self.heading('Submitting pull request')
        submission = dict(branch="master", title=title)
        reply = self.apost('/areas/model-definitions/pullrequests', json.dumps(submission)).json()
        print '  Reply: %s' % reply

