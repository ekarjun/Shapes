#!/usr/bin/env python

# This program is invoked by the orchestrator to execute the "Update" operation
# of a demo update script. Operation is determined by the "prop1" property of
# the updated resource.
#

import json
import requests
import os
import time

# CREATE A LOG FILE
with open(os.environ["LOG_FILE"], "w") as f:

    def log(msg):
        print >> f, msg

    log("First line of log")

    # EXTRACTING DATA FROM REQUESTED RESOURCE
    log("Extracting input data")
    rid = os.environ["RESOURCE_ID"]
    muri = os.environ['API_URI'] + '/market/api/v1'
    headers = {
        'content-type': 'application/json',
        'accept': 'application/json',
        'Cyan-Internal-Request': '1',
        'bp-user-id': os.environ["BP_USER_ID"],
        'bp-tenant-id': os.environ["BP_TENANT_ID"],
        'bp-role-ids': os.environ["BP_ROLE_ID"]
    }

    def mget(path):
        url = muri + path
        log("GET %s" % url)
        res = requests.get(url, verify=True, headers=headers)
        log("  %d" % (res.status_code, ))
        if res.status_code >= 300:
            log("  Error: %s" % res.text)
        else:
            log("  Got back (raw): %s" % res.text)
        return res

    def mpatch(path, data):
        url = muri + path
        log("PATCH %s %s" % (url, data))
        res = requests.patch(url, data=json.dumps(data), headers=headers)
        log("  %d" % (res.status_code, ))
        if res.status_code >= 300:
            log("  Error: %s" % res.text)
        return res

    log("Grabbing resource %s" % rid)
    resource = mget("/resources/%s" % rid).json()
    log("Got back JSON: %s" % str(resource))

    props = resource['properties']
    prop1 = props['prop1']
    prop2 = props['prop2'] if 'prop2' in props else None

    log("prop1 is: %s" % str(prop1))

    if prop1.startswith("successpatch"):
        log ("Patching market")
        mpatch("/resources/%s/observed" % rid, dict(properties=dict(prop1=prop1),
                                                    orchState="active", reason="Update to %s Successful" % prop1))
    elif prop1 == "failthrow":
        log ("Throwing exception")
        raise Exception("Something is not right")

    elif prop1 == "failpatch":
        log ("Patching failed")
        mpatch("/resources/%s/observed" % rid, dict(properties=dict(prop1="observed"),
                                                    orchState="failed", reason="Seeing something else"))
    elif prop1.startswith("waitpatch"):
        time.sleep(0.25)
        log ("Patching market")
        mpatch("/resources/%s/observed" % rid, dict(properties=dict(prop1=prop1),
                                                    orchState="active", reason="Update to %s Successful" % prop1))

    # if key1 = prop4
    # indexpatch:idx1:key1:idx2:key2:val
    # if key1 = prop7
    # indexpatch:idx1:key1:val
    # if key1 == prop8
    # indexpatch:idx1:key1:idx2:op:val
    # if key1 == prop9
    # indexpatch:idx1:key1 (val will be [v1,v2,v3,v4])
    elif prop1.startswith("indexpatch:"):
        params = prop1.split(":")
        idx1 = int(params[1])
        key1 = params[2]
        if key1 == "prop4":
            idx2 = int(params[3])
            key2 = params[4]
            val = params[5]
            patch = props['prop3']
            patch[idx1][key1][idx2][key2] = val
            mpatch("/resources/%s/observed" % rid, dict(properties=dict(prop3=patch),
                                                        orchState="active", reason="Update to %s Successful" % patch))
        elif key1 == "prop7":
            val = params[3]
            patch = props['prop3']
            patch[idx1][key1] = val
            mpatch("/resources/%s/observed" % rid, dict(properties=dict(prop3=patch),
                                                        orchState="active", reason="Update to %s Successful" % patch))

        elif key1 == "prop8":
            idx2 = int(params[3])
            op = params[4]
            patch = props['prop3']

            if op == "remove":
                del patch[idx1][key1][idx2]
                mpatch("/resources/%s/observed" % rid, dict(properties=dict(prop3=patch),
                                                            orchState="active", reason="Update to %s Successful" % patch))
            elif op == "replace":
                val = params[5]
                patch[idx1][key1][idx2] = val
                mpatch("/resources/%s/observed" % rid, dict(properties=dict(prop3=patch),
                                                            orchState="active", reason="Update to %s Successful" % patch))

            elif op == "insert":
                val = params[5]
                patch[idx1][key1].insert(idx2, val)
                mpatch("/resources/%s/observed" % rid, dict(properties=dict(prop3=patch),
                                                            orchState="active", reason="Update to %s Successful" % patch))


        elif key1 == "prop9":
            patch = props['prop3']
            patch[idx1][key1] = ["v1","v2","v3","v4"]
            mpatch("/resources/%s/observed" % rid, dict(properties=dict(prop3=patch),
                                                        orchState="active", reason="Update to %s Successful" % patch))

    # Remove an element from prop3
    elif prop1.startswith("removeelem:"):
        params = prop1.split(":")
        idx1 = int(params[1])
        patch = props['prop3']
        del patch[idx1]
        mpatch("/resources/%s/observed" % rid, dict(properties=dict(prop3=patch),
                                                    orchState="active", reason="Update to %s Successful" % patch))

    # Remove all elements from prop3
    elif prop1.startswith("removeprop"):
        patch = []
        mpatch("/resources/%s/observed" % rid, dict(properties=dict(prop3=patch),
                                                    orchState="active", reason="Update to %s Successful" % patch))

    if prop2 and prop2.startswith("slowpatch"):
        log ("Patching market")
        time.sleep(0.25)
        mpatch("/resources/%s/observed" % rid, dict(properties=dict(prop2=prop2),
                                                    orchState="active", reason="Update to %s Successful" % prop2))
