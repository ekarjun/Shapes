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

class TronApiConfig:
    def __init__(self, token, uri, appName):
        self.token = token
        self.uri = uri
        self.appName = appName

    @staticmethod
    def read(fileName):
        fp = open(fileName, 'r')
        cfgMap = json.load(fp)
        cfg = TronApiConfig(cfgMap['token'],
            cfgMap['uri'],
            cfgMap['appName'])
        return cfg

    # Return Uuid if successful; None otherwise
    def requestUuidFromName(self, reqUrl, headers, reqType, reqName):
        uuid = None

        try:
            resp = requests.get(reqUrl, headers = headers, verify = False)
            if (resp.status_code != 200):
                print("Error: Request for %s (%s) uuid failed: %s") % (reqType, reqName)
            else:
                uuids = [results['uuid'] for results in resp.json()['results']]
                if (len(uuids) == 0):
                    print("Error: Unable to find uuid from Tron for %s (%s)") % (reqType, reqName)
                else:
                    uuid = uuids[0]
        except Exception as e:
            print("Error (%s) obtaining uuid for %s (%s)") % (str(e), reqType, reqName)

        return uuid

    # Return Role UUid if already set; None if the user does not have the role
    def checkRole(self, reqUrl, headers, roleUuid):
        uuid = None

        try:
            resp = requests.get(reqUrl, headers = headers, verify = False)
            if (resp.status_code != 200):
                print("Error: Check role request failed")
            else:
                roles = resp.json()['roles']
                if (roleUuid in roles):
                    uuid = roleUuid
        except Exception as e:
            print("Error (%s) checking for user role") % (str(e))

        return uuid

    # Return true if successful; false otherwise
    def postRole(self, reqUrl, headers, data, userName, roleName, tenantName):
        status = False

        try:
            resp = requests.post(reqUrl, data = data, headers = headers, verify = False)
            if (resp.status_code != 200) and (resp.status_code != 201) and (resp.status_code != 204):
                print("Error: Post request to assign role (%s) to user (%s) in tenant (%s) failed with status (%s)") % (roleName, userName, tenantName, str(resp.status_code))
            else:
                status = True
        except Exception as e:
            print("Error: Post request to assign role (%s) to user (%s) in tenant (%s) failed with exception (%s)") % (roleName, userName, tenantName, str(e))

        return status

class AddUserRole(Plugin):
    """ Add a role to a user in the Tron UAC system
    """
    LONG_OPTION = "--add-user-role"

    # Return the user uuid if successful
    # None if unsuccessful
    def run(self):
        self.heading('Add User Role')

        userName = raw_input("Enter user name [admin]: ")
        if (len(userName) == 0):
            userName = "admin"

        roleName = raw_input("Enter role name [admin]: ")
        if (len(roleName) == 0):
            roleName = "admin"

        tenantName = raw_input("Enter tenant name [master]: ")
        if (len(tenantName) == 0):
            tenantName = "master"

        tronCfg = None

        while tronCfg == None:
            try:
                authConfigFile = raw_input("Enter application Tron authentication file [/etc/bpocore-application/tron.json]: ")
                if (len(authConfigFile) == 0):
                    authConfigFile = "/etc/bpocore-application/tron.json"

                tronCfg = TronApiConfig.read(authConfigFile)
            except Exception as e:
                print("Error (%s) reading Tron authentication file (%s)") % (str(e), authConfigFile)
                tronCfg = None

        headers = {'content-type': 'application/json', 'Authorization': 'token ' + tronCfg.token}

        # Obtain application Uuid from the application name
        reqUrl = tronCfg.uri + "/applications?name=" + tronCfg.appName
        appUuid = tronCfg.requestUuidFromName(reqUrl, headers, "application", tronCfg.appName)

        if (appUuid is None):
            return None

        # Obtain the role id
        reqUrl = tronCfg.uri + "/roles?name=" + roleName + "&application=" + appUuid
        roleUuid = tronCfg.requestUuidFromName(reqUrl, headers, "role", roleName)

        if (roleUuid is None):
            return None

        # Obtain the tenant id
        reqUrl = tronCfg.uri + "/tenants?name=" + tenantName
        tenantUuid = tronCfg.requestUuidFromName(reqUrl, headers, "tenantId", tenantName)
        if (tenantUuid is None):
            return None

        # Obtain the userUuid
        reqUrl = tronCfg.uri + "/users?tenant=" + tenantUuid + "&username=" + userName
        userUuid = tronCfg.requestUuidFromName(reqUrl, headers, "user", userName)
        if (userUuid is None):
            return None

        # Check to see if the role is already assigned to the user
        reqUrl = tronCfg.uri + "/users/" + userUuid
        retVal = tronCfg.checkRole(reqUrl, headers, roleUuid)

        if (retVal is None):
            # Assign the role to the user
            reqUrl = tronCfg.uri + "/users/" + userUuid + "/add_roles"
            rolesObj = {'roles': [roleUuid]}
            rolesData = json.dumps(rolesObj)
            if (tronCfg.postRole(reqUrl, headers, rolesData, userName, roleName, tenantName) is True):
                print("Successfully assigned role (%s) to user (%s) in tenant (%s)") % (roleName, userName, tenantName)
                retVal = userUuid
        else:
            print ("Successful: Role (%s) already assigned to user (%s) in tenant (%s)") % (roleName, userName, tenantName)

        return (retVal)


class AddUser(Plugin):
    """ Add a user to the Tron UAC system.
    """
    LONG_OPTION = "--add-user"

    # Return the user uuid if successful
    # None if unsuccessful
    def run(self):
        self.heading('Add New User')

        userName = None
        while userName == None:
            userNameStr = raw_input("Enter user name: ")
            if (len(userNameStr) > 0):
                userName = userNameStr

        firstName = None
        while firstName == None:
            firstNameStr = raw_input("Enter user first name: ")
            if (len(firstNameStr) > 0):
                firstName = firstNameStr


        lastName = None
        while lastName == None:
            lastNameStr = raw_input("Enter user last name: ")
            if (len(lastNameStr) > 0):
                lastName = lastNameStr

        userEmail = None
        while userEmail == None:
            userEmailStr = raw_input("Enter user email address: ")
            if (len(userEmailStr) > 0):
                userEmail = userEmailStr

        tenantName = raw_input("Enter tenant name [master]: ")
        if (len(tenantName) == 0):
            tenantName = "master"

        tronCfg = None

        while tronCfg == None:
            try:
                authConfigFile = raw_input("Enter application Tron authentication file [/etc/bpocore-application/tron.json]: ")
                if (len(authConfigFile) == 0):
                    authConfigFile = "/etc/bpocore-application/tron.json"

                tronCfg = TronApiConfig.read(authConfigFile)
            except Exception as e:
                print("Error (%s) reading Tron authentication file (%s)") % (str(e), authConfigFile)
                tronCfg = None

        headers = {'content-type': 'application/json', 'Authorization': 'token ' + tronCfg.token}

        # Obtain the tenant id
        reqUrl = tronCfg.uri + "/tenants?name=" + tenantName
        tenantUuid = tronCfg.requestUuidFromName(reqUrl, headers, "tenant", tenantName)
        if (tenantUuid is None):
            print("Error: Unable to determine UUID for tenant %s") % (tenantName)

        userObj = {'username': userName,
                   'lastName': lastName,
                   'firstName': firstName,
                   'email': userEmail,
                   'tenant': tenantUuid,
                   'isActive': True}

        userData = json.dumps(userObj)

        # Create the user
        reqUrl = tronCfg.uri + "/users"

        uuid = None

        try:
            resp = requests.post(reqUrl, headers = headers, data = userData, verify = False)
            if (resp.status_code != 201):
                respStr = json.dumps(resp.json())
                print("Error: Request to create user %s failed.  Status %s.  Response: %s") % (userName, str(resp.status_code), respStr)
            else:
                uuid = resp.json()['uuid']
                print("Successfully added user %s with uuid %s to tenant %s with tenant uuid %s") % (userName, uuid, tenantName, tenantUuid)
        except Exception as e:
            print("Error (%s) creating user %s") % (str(e), userName)

        return (uuid)

class AddUserKeypair(Plugin):
    """ Add a key-secret pair for an existing user
    """
    LONG_OPTION = "--add-user-keypair"

    # Return:
    # Successful = the Json response from Tron including the keyId and keySecret values
    # Unsuccessful = None
    def run(self):
        self.heading('Add User Keypair')

        userName = None
        while userName == None:
            userNameStr = raw_input("Enter user name: ")
            if (len(userNameStr) > 0):
                userName = userNameStr

        tenantName = raw_input("Enter tenant name [master]: ")
        if (len(tenantName) == 0):
            tenantName = "master"

        tronCfg = None

        while tronCfg == None:
            try:
                authConfigFile = raw_input("Enter application Tron authentication file [/etc/bpocore-application/tron.json]: ")
                if (len(authConfigFile) == 0):
                    authConfigFile = "/etc/bpocore-application/tron.json"

                tronCfg = TronApiConfig.read(authConfigFile)
            except Exception as e:
                print("Error (%s) reading Tron authentication file (%s)") % (str(e), authConfigFile)
                tronCfg = None

        headers = {'content-type': 'application/json', 'Authorization': 'token ' + tronCfg.token}

        # Obtain the tenant id
        reqUrl = tronCfg.uri + "/tenants?name=" + tenantName
        tenantUuid = tronCfg.requestUuidFromName(reqUrl, headers, "tenant", tenantName)
        if (tenantUuid is None):
            print("Error: Unable to determine UUID for tenant %s") % (tenantName)
            return None

            # Obtain the userUuid
        reqUrl = tronCfg.uri + "/users?tenant=" + tenantUuid + "&username=" + userName
        userUuid = tronCfg.requestUuidFromName(reqUrl, headers, "user", userName)
        if (userUuid is None):
            print("Error: Unable to determine UUID for username %s in tenant") % (userName, tenantName)
            return None


        # Create the keyPair
        reqUrl = tronCfg.uri + "/api-keys"

        dataObj = {'owner': userUuid}

        data = json.dumps(dataObj)

        keyPair = None

        try:
            resp = requests.post(reqUrl, data = data, headers = headers, verify = False)
            if (resp.status_code != 201):
                respStr = json.dumps(resp.json())
                print("Error: Request to create user key-pair failed for user %s.  Status %s.  Response: %s") % (userName, str(resp.status_code), respStr)
            else:
                keyId = resp.json()['keyId']
                keySecret = resp.json()['keySecret']
                keyPair = resp.json()
                print("Successfully added key-pair for user %s with uuid %s to tenant %s with tenant uuid %s") % (userName, userUuid, tenantName, tenantUuid)
                print("KeyPair = %s, %s") % (keyId, keySecret)
        except Exception as e:
            print("Error (%s) creating user key-pair for user %s in tenant %s") % (str(e), userName, tenantName)

        return (keyPair)
