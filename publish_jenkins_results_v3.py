""" 
Python Script to publish Jenkins-api results into ServiceNow instance through the SN API
Developed by Simon Morris - ServiceNow
Modified by Sergio Maurenzi - Performen
"""


import jenkinsapi
from jenkinsapi.jenkins import Jenkins

import argparse
import json
import requests
from requests.auth import HTTPDigestAuth, HTTPBasicAuth
import datetime
import time
import pytz



parser = argparse.ArgumentParser()
parser.add_argument("job")
parser.add_argument("build")
parser.add_argument("git_tag_name")
parser.add_argument("jenkins_url")
parser.add_argument("jenkins_user")
parser.add_argument("jenkins_pass")
parser.add_argument("snc_url")
parser.add_argument("snc_user")
parser.add_argument("snc_pass")

args = parser.parse_args()


def publish_results():

    # If your Jenkins server has not authentication set you might want to change the following line
    # J = Jenkins(JENKINS_URL)
    J = Jenkins(args.jenkins_url, username=args.jenkins_user, password=args.jenkins_pass)
    print ">>>>job=%s" % args.job
    print ">>>>build=%s" % args.build
    
    job = J[args.job]
    build = job.get_build(int(args.build))
    
    output = {}
    
    status = build.get_status()
    console = build.get_console()
    revision = build.get_revision()
    duration = str(build.get_duration()) # Need to cook this
    git_tag = args.git_tag_name
    
    if build.is_running():
        durationSeconds = str((datetime.datetime.now(pytz.utc) - build.get_timestamp()).total_seconds())
    # If the job is completed
    else:
        durationSeconds = duration

    

    url = build.baseurl
    
    
    print ">>>>>status=%s" % status
    print ">>>>>console_length=%s" % len(console)
    print ">>>>>revision=%s" % revision
    print ">>>>>duration=%s" % duration
    print ">>>>>durationSeconds=%s" % durationSeconds
    print ">>>>>gitTag=%s" % git_tag
    
    output['job'] = args.job
    output['build_number'] = args.build
    output['status'] = status
    output['console'] = console
    output['revision'] = revision
    output['duration'] = durationSeconds
    output['url'] = url
    
    print ">>>>>url=%s" % url

    resulturl = build.get_result_url()

    #print ">>>>>resulturl=%s" % resulturl

    resultset = build.get_resultset()  

    #print ">>>>>resultset=%s" % resultset
    
    print ">>>>>passCount=%s" % resultset._data['passCount']  
    print ">>>>>failCount=%s" % resultset._data['failCount']
    print ">>>>>skipCount=%s" % resultset._data['skipCount']
    
    output['pass_count'] = resultset._data['passCount']
    output['fail_count'] = resultset._data['failCount']
    output['skip_count'] = resultset._data['skipCount']
    
    if not build.has_resultset():
        quit()

    results = resultset.items()
    
    output['results'] = []
    
    count = 1
    for i in results:
        d = {}
        print ">>>>>>>>>>>>>item=%s name=%s" % (count, i[0])
        d['name'] = i[0]
        
        print ">>>>>>>>>>>>>status=%s" % i[1].status
        d['status'] = i[1].status
        
        print ">>>>>>>>>>>>>error_details=%s" % i[1].errorDetails
        d['error_details'] = i[1].errorDetails
        
        print ">>>>>>>>>>>>>error_stackTrace=%s" % i[1].errorStackTrace
        d['error_stack_trace'] = i[1].errorStackTrace
        
        print ">>>>>>>>>>>>>test_case=%s" % i[1].className
        d['test_case'] = i[1].className + git_tag
        
        output['results'].append(d)
        count += 1
    
    
    _json = json.dumps(output, sort_keys=True)
    
    print "JSON OUTPUT=%s" % _json
    
    print "Sending results to ServiceNow"
    url = args.snc_url + "/api/snc/jenkinsimport/results"
    requests.post(url=url, data=_json, auth=HTTPBasicAuth(args.snc_user, args.snc_pass))
    
if '__main__' == __name__:
    publish_results()
