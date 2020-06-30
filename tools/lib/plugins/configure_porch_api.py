from porch_api_lib import Plugin, PorchApiConfig, PorchApiLib

import json
import getpass
import os

try:
    import requests
except ImportError:
    print 'Please install the "requests" python library, e.g., by'
    print 'sudo apt-get install python-requests # on Ubuntu systems'
    print 'sudo pip install requests # on most Linux systems and Mac'
    sys.exit(1)

class ConfigurePorchApi(Plugin):
    """ Configure Porch API information and save to initialization file
    """
    SHORT_OPTION = "-c"
    LONG_OPTION = "--configure"

    def run(self):
        yes_or_no = {"y", "n"}

        self.heading('configure')

        auth = None

        host = raw_input("Enter hostname or IP address [localhost]: ")
        if (len(host) == 0):
            host = "localhost"

        port = raw_input("Enter port [8181]: ")
        if (len(port) == 0):
            port = "8181"

        protocol = raw_input("Enter protocol [http]: ")
        if (len(protocol) == 0):
            protocol = "http"

        # For now, only token-based authentication is supported
        # Add HMAC
        authTypes = {"none", "token"}

        authType = None

        while authType == None:
            authType = raw_input("Enter authentication type (None or token) [None]: ")
            authType = authType.lower()
            if (authType in authTypes is False):
                print("Invalid authentication type")
                authType = None

        if (authType == "token"):
            print("Authenticating to obtain API token")
            userName = raw_input("Enter user name [admin]: ")
            if (len(userName) == 0):
                userName = "admin"

            passwd = getpass.getpass("Enter password [adminpw]: ")

            # passwd = raw_input("Enter password [adminpw]: ")
            if (len(passwd) == 0):
                passwd = "adminpw"

            domain = raw_input("Enter domain [master]: ")
            if (len(domain) == 0):
                domain = "master"

            headers = {'content-type': 'application/json'}

            authCfg = PorchApiConfig(protocol, host, port, None)

            authUrl = authCfg.url_base + "/bpocore/authentication/api/v1/tokens"

            dataObj = {'name': userName,
              'password': passwd,
              'tenant': {
                'name': domain
              }
            }

            data = json.dumps(dataObj)

            try:
                authResp = requests.post(authUrl, data = data, headers = headers,
                    verify = False)

                if (authResp.status_code != 201):
                    print("Error: Authentication failed: %s") % (str(authResp))
                else:
                    token = authResp.headers['X-Subject-Token']
                    print("Obtained Token: %s") % (token)

                    auth = {'authType': 'token',
                    'token': token
                    }

            except Exception as e:
                print("Error: Authentication failed: %s") % (str(e))

        cfg = PorchApiConfig(protocol, host, port, auth)

        fileWritten = False

        while fileWritten == False:
            filePrompt = "Write configuration to filename [%s.json]" % (host)

            fileName = raw_input(filePrompt)

            if (len(fileName) == 0):
                fileName = "%s.json" % (host)

            try:
                cfg.write(fileName)
                fileWritten = True
            except Exception as e:
                print("Error writing file (%s): %s") % (fileName, str(e))

        asDefault = None

        while asDefault == None:
            asDefault = raw_input("Set configuration as default (y/n) [y]: ")
            if len(asDefault) == 0:
                asDefault = "y"

            if (asDefault.lower() in yes_or_no is False):
                asDefault = None

        if asDefault.lower() == 'y':
            defFile = PorchApiConfig.DEFAULT_CFG_FILE

            exists = False

            if os.path.exists(defFile) is True or os.path.islink(defFile) is True:
                exists = True

            if (exists is True and os.path.islink(defFile) is False):
                print("Warning: %s already exists and is not a symlink.  Cannot save as default configuration") % (defFile)
            elif (exists is True):
                try:
                    os.remove(defFile)
                except Exception as e:
                    print("Warning: Unable to remove %s") % (str(e))

            if os.path.exists(defFile) is False:
                try:
                    os.symlink(fileName, defFile)
                except Exception as e:
                    print("Warning: Unable to save %s as default configuration (%s)") % (fileName, defFile)

        PorchApiLib.cfg = cfg





