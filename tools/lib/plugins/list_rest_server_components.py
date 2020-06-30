from porch_api_lib import Plugin
import requests
import json

class ListRestServerComponents(Plugin):
    """ List components registered with the REST Server
    """
    LONG_OPTION = "--list-rest-server-components"

    def run(self):
        self.heading('list components registered with rest server')
        print("Writing Json to file: /tmp/rest_server_components.json")
        comps = self.listComponents()
        print(json.dumps(comps, sort_keys=True, indent=4))
        fp = open ("/tmp/rest_server_components.json", 'w')
        json.dump (comps, fp, sort_keys=True, indent=4)
        fp.close()


    def listComponents(self):
        headers = {'content-type': 'application/json'}

        restUrl = self.getUrl(self.rest_path, "components")

        respJson = {}

        try:
            resp = requests.get(restUrl, headers = headers, verify = False)

            if (resp.status_code != 200):
                print("Error: ListRestServerComponents failed: %s") % (str(resp))
            else:
                print("ListRestServerComponents success: %s") % (str(resp))
                respJson = resp.json()['items']

        except Exception as e:
            print("Error: ListRestServerComponents: %s") % (str(e))


        return respJson