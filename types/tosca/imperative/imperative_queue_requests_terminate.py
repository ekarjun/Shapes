#!/usr/bin/env python

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

    def mdelete(path):
        url = muri + path
        log("DELETE %s" % (url,))
        res = requests.delete(url, headers=headers)
        log("  %d" % (res.status_code, ))
        if res.status_code >= 300:
            log("  Error: %s" % res.text)
        return res

    log("Grabbing resource %s" % rid)
    resource = mget("/resources/%s" % rid).json()

    dependencies = mget('/resources/%s/dependencies' % rid).json()['items']
    log(dependencies)

    for subRes in dependencies:
        id = subRes['id']
        res = mdelete('/resources/%s' % id)
        log('Deleting Interface: %s' % res.status_code)
