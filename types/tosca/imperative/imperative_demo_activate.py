#!/usr/bin/env python

# This program is invoked by the orchestrator to execute the "Create" operation
# of an IpVpnStaticNat service.
#
# The following input variable are passed in as environment variables
#
# API_URI          - Base URI for the orchestrator. E.g., "http://localhost:8181"
# LOG_FILE         - Place of log file to log progress
# DOMAIN           - UAC domain (tenant)
# BP_USER_ID       - User ID
# BP_TENANT_ID     - Tenant ID
# BP_ROLE_ID       - Set of Role IDs
# C_TRACE          - trace ID
# C_UPSTREAM       - hop ID of the caller
# RESOURCE_ID      - The ID of the resource on which this operation is invoked
# OPERATION        - Name of the operation
# OPERATION_ARG_<name> - Named operation argument (per the definition of the
#                    the operation.
#
# The process is expected to do the following:
#
# Successful execution means the process exited with exit code 0, and provided
# its output to the standard output, as JSON data. The format of the JSON data
# should be usable as a patch blob to augment the resource, including all
# legally writable attributes.
#
# The failure of the operation should be signaled with non-zero exit code, and
# the last line observed on the stderr will be used as reason code. A failed
# Create operation will result in marking the resource orchState as "failed".
#

import json
import requests
import os
import sys
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
        log("res is  %d" % (res.status_code, ))
        if res.status_code >= 300:
            log("  Error: %s" % res.text)
        else:
            log("  Got back (raw): %s" % res.text)
        return res


    def get_noop_product_id():
        prod = mget('/products?q=resourceTypeId:tosca.resourceTypes.Noop').json()['items']
        assert(len(prod) == 1)
        return prod[0]['id']

    def mpost(path, data=None):
        url = muri + path
        log("POST %s %s" % (url, data))
        res = requests.post(url, data=data, headers=headers)
        if res.status_code >= 300:
            log("  Error: %s" % res.text)
        return res

    def add(what, path, data):
        log("Adding %s" % what)
        r = mpost(path, json.dumps(data))
        assert(r.status_code < 210)
        obj = r.json()
        return obj

    # log("Grabbing resource %s" % rid)
    # resource = mget("/resources/%s" % rid).json()
    # log("Got back JSON: %s" % str(resource))

    # props = resource['properties']
    prop1 = "test"  # props['prop1']

    # SIMPLY WRITE BACK VALUES AS PROP1-PROP6

    prop2 = "This value was written by the activation script (prop1 was %s)" % prop1
    prop3 = 42
    prop4=os.environ["BP_USER_ID"]
    prop5=os.environ["BP_TENANT_ID"]
    prop6=os.environ["BP_ROLE_ID"]
    prop8=os.environ["OPERATION"]

    # EXAMPLE ERROR CONDITION
    if (prop6 == "bad-id"):
        sys.stderr.write("BP_ROLE_ID must not equal bad-id")
        sys.exit(1)

    data = dict(prop1=prop1, prop2=prop2, prop3=prop3, prop4=prop4, prop5=prop5, prop6=prop6, prop8=prop8)
    log("Sending back as response: %s" % str(data))


    log("Grabbing resource {}".format(rid))
    resource = mget("/resources/{}".format(rid)).json()
    if  resource['label'] == "queue":
        for x in xrange(5):
            time.sleep(0.25)
            res = add("Resource", "/resources", dict(
                    label = "queue_noop_resource_{}".format(x),
                    productId = get_noop_product_id(),
                    properties = {"data": {}}))
            subResId = res['id']
            add("Relationship", "/relationships", {
                "relationshipTypeId": "tosca.relationshipTypes.MadeOf",
                "sourceId":           resource['id'],
                "requirementName":  "composed",
                "targetId":           subResId,
                "capabilityName":   "composable",
                "orchState":        "active"
            })
    if  resource['label'] == "failAfterFewSubResources":
        for x in xrange(3):
            time.sleep(0.25)
            res = add("Resource", "/resources", dict(
                    label = "queue_noop_resource_{}".format(x),
                    productId = get_noop_product_id(),
                    properties = {"data": {}}))
            subResId = res['id']
            add("Relationship", "/relationships", {
                "relationshipTypeId": "tosca.relationshipTypes.MadeOf",
                "sourceId":           resource['id'],
                "requirementName":  "composed",
                "targetId":           subResId,
                "capabilityName":   "composable",
                "orchState":        "active"
            })
        log ("Throwing activation exception")
        raise Exception("Something is not right")

    print json.dumps(data)

