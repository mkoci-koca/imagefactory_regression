#!/usr/bin/env python
# encoding: utf-8
#   Copyright 2011 Red Hat, Inc.
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#        Regression test for Image Factory #bug783590
#        Created by koca (mkoci@redhat.com)
#        Date: 26/01/2012
#        Issue: https://bugzilla.redhat.com/show_bug.cgi?id=783590 -mount_options: /dev/vda2 on /boot: mount: unknown filesystem type 'LVM2_member' for f15 builds
# return values:
# 0 - OK: everything OK
# 1 - Fail: setupTest wasn't OK
# 2 - Fail: bodyTest wasn't OK
# 3 - Fail: cleanTest wasn't OK
# 4 - Fail: any other error (reserved value)

#necessary libraries
import os
import sys
import time
import subprocess
import re
import shutil
import oauth2 as oauth
import httplib2
import json
from syck import *
configuration = load(file("configuration.yaml", 'r').read())
#constants 
SUCCESS=0
FAILED=1
RET_SETUPTEST=1
RET_BODYTEST=2
RET_CLEANTEST=3
RET_UNEXPECTED_ERROR=4
ROOTID=0
TIMEOUT=360
MINUTE=60
#setup variables, constants
CrazyCommand=["aeolus-image build --target vsphere --template templates/bug783590.tdl;"]
LogFileIF=configuration["LogFileIF"]
LogFileIWH=configuration["LogFileIWH"]

consumer = oauth.Consumer(key='key', secret='secret')
sig_method = oauth.SignatureMethod_HMAC_SHA1()
params = {'oauth_version':"0.4.4",
          'oauth_nonce':oauth.generate_nonce(),
          'oauth_timestamp':oauth.generate_timestamp(),
          'oauth_signature_method':sig_method.name,
          'oauth_consumer_key':consumer.key}
url_https="https://localhost:8075/imagefactory/builders/"
VSPHEREbugFile=configuration["VSPHEREbugFile"]
VSPHEREconfigureFile=configuration["VSPHEREconfigureFile"]
VSPHEREBackupFile=configuration["VSPHEREBackupFile"]

def setupTest():
    print "=============================================="
    print "Setup of the regression test based on bug783590 -mount_options: /dev/vda2 on /boot: mount: unknown filesystem type 'LVM2_member' for f15 build"
    print "See the bug for further information - https://bugzilla.redhat.com/show_bug.cgi?id=783590"
    print "Checking if you have enough permission..."
    if os.geteuid() != ROOTID:
        print "You must have root permissions to run this script, I'm sorry buddy"
        return False #exit the test
    #run the cleanup configuration
    print "Cleanup configuration...." 
    if os.system("aeolus-cleanup") != SUCCESS:
        print "Some error raised in aeolus-cleanup !"
        
    #first backup old rhvm file
    print "Backup old vsphere configuration file"
    if os.path.isfile(VSPHEREconfigureFile):
        shutil.copyfile(VSPHEREconfigureFile, VSPHEREBackupFile)
    #then copy the conf. file
    print "Copy vsphere configuration file to /etc/aeolus-configure/nodes/vsphere_configure"
    if os.path.isfile(VSPHEREbugFile):
        shutil.copyfile(VSPHEREbugFile, VSPHEREconfigureFile)
    else:
        print VSPHEREbugFile + " didn't find!"
        return False          
    #now run aeolus-configure -p rhevm and uses the values from /etc/aeolus-configure/nodes/rhevm
    print "running aeolus-configure -p vsphere"
    if os.system("aeolus-configure -p vsphere") != SUCCESS:
        print "Some error raised in aeolus-configure with parameter -p vsphere !"
        return False
    print "Clearing log file for Image Factory"
    os.system("> " + LogFileIF)
    print "Clearing log file for Image Warehouse"
    os.system("> " + LogFileIWH)
    return True

#this functions suppose to be as a help function to do not write one code multiple times
def helpTest(imageTest):
    url = url_https + imageTest
    req = oauth.Request(method='GET', url=url, parameters=params)
    sig = sig_method.sign(req, consumer, None)
    req['oauth_signature'] = sig
    r, c = httplib2.Http().request(url, 'GET', None, headers=req.to_header())
    response = 'Response headers: %s\nContent: %s' % (r,c)
    print response
    return c

#body
def bodyTest():
    print "=============================================="
    print "test being started"
    target_image = list()
    for command in CrazyCommand:
        try:
            print command
            retcode = os.popen(command).read()
            print "output is :"
            print retcode
            tempvar = re.search(r'.*\n.*\n([a-zA-Z0-9\-]*).*',retcode,re.I)
            if  tempvar == None:
                print "An unknown error occurred. I'm not able to get target image ID. Check the log file out:"
                print "======================================================"
                outputtmp = os.popen("cat " + LogFileIF).read()
                print outputtmp
                print "See the template templates/bug783590.tdl"
                print "======================================================"
                outputtmp = os.popen("cat templates/bug783590.tdl").read()
                print outputtmp
                return False
            else:
                target_image.append(tempvar.group(1))                
            #target_image.append(re.search(r'.*Target Image: ([a-zA-Z0-9\-]*).*:Status.*',retcode,re.I).group(1))
        except subprocess.CalledProcessError, e:
            print >>sys.stderr, "Execution failed:", e
            return False
        time.sleep(10) #sleep for 10 seconds        
    print "wait until build process is done"
    #setup counter to do not wait longer then 1 hour
    Counter=0
    
    for timage in target_image:
        print "Let\'s check this image: " + timage
        data = json.loads(helpTest(timage))
        print "Data Status: " + data['status']
        #while os.system("aeolus-cli status --targetimage " + timage + "|grep -i building") == SUCCESS:
        while data['status'] == "BUILDING":
            Counter=Counter+1
            #wait a minute
            time.sleep(MINUTE)
            data = json.loads(helpTest(timage))
            print "Data Status: " + data['status']
            #after an hour break the 
            if Counter > TIMEOUT:
                print "Error: timeout over "+str(TIMEOUT)+" minutes !"
                return False
        
    print "Checking if there is any error in erro log of image factory"
    if os.system("grep -i \"FAILED\\|Error\" " + LogFileIF) == SUCCESS:
        print "Found FAILED or error message in log file:"
        outputtmp = os.popen("grep -i \"FAILED\\|Error\" " + LogFileIF).read()
        print outputtmp
        print "See the output from log file " + LogFileIF + ":"
        print "======================================================"
        outputtmp = os.popen("cat " + LogFileIF).read()
        print outputtmp
        print "See the output from log file " + LogFileIWH + ":"
        print "======================================================"
        outputtmp = os.popen("cat " + LogFileIWH).read()
        print outputtmp        
        return False
#check if status is either complete or building
    for timage in target_image:
        print "Let\'s check this image: " + timage
        data = json.loads(helpTest(timage))
        print "Data Status for image "+timage+": " + data['status']
        if data['status'] != "COMPLETED":
            print "Build "+timage+" is not completed for some reason! It looks it stuck in the NEW status."
            print "Perhaps you can find something in the log file " + LogFileIF + ":"
            print "======================================================"
            outputtmp = os.popen("cat " + LogFileIF).read()
            print outputtmp
            print "See the output from log file " + LogFileIWH + " too:"
            print "======================================================"
            outputtmp = os.popen("cat " + LogFileIWH).read()
            print outputtmp        
            print "See the template templates/bug768945.tdl"
            print "======================================================"
            outputtmp = os.popen("cat templates/bug768945.tdl").read()
            print outputtmp
            return False    
    return True
 
#cleanup after test
def cleanTest():
    print "=============================================="
    print "Cleaning the mess after test"
    if os.path.isfile(VSPHEREBackupFile):
        #copy file back
        shutil.copyfile(VSPHEREBackupFile, VSPHEREconfigureFile)
    #future TODO: maybe delete all iso's and images beneath directories /var/lib/imagefactory/images/ and /var/lib/oz/isos/
    return True
 
#execute the tests and return value (can be saved as a draft for future tests)
if setupTest(): 
    if bodyTest():
        if cleanTest():
            print "=============================================="
            print "Test PASSED entirely !"
            sys.exit(SUCCESS)
        else:
            print "=============================================="
            print "Although Test was successful, cleaning after test wasn't successful !"
            sys.exit(RET_CLEANTEST)
    else:
        print "=============================================="
        print "Test Failed !"
        cleanTest()
        sys.exit(RET_BODYTEST)
else:
    print "=============================================="
    print "Test setup wasn't successful ! Test didn't even proceed !"
    cleanTest()
    sys.exit(RET_SETUPTEST)

