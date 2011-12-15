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
#        Regression test for Image Factory #bug761163
#        Created by koca (mkoci@redhat.com)
#        Date: 15/12/2011
#        Modified: 15/12/2011
#        Issue: https://bugzilla.redhat.com/show_bug.cgi?id=761163 - RHEL 5.7 failed to build with <?xml version="1.0" encoding="UTF-8"?> in system template
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


#constants 
SUCCESS=0
FAILED=1
RET_SETUPTEST=1
RET_BODYTEST=2
RET_CLEANTEST=3
RET_UNEXPECTED_ERROR=4
ROOTID=0
TIMEOUT=180
#setup variables, constants
CrazyCommand=["aeolus-cli build --target rhevm --template templates/bug761163.tdl;"]
LogFile="/var/log/imagefactory.log"

def setupTest():
    print "=============================================="
    print "Setup of the regression test based on bug761163 - RHEL 5.7 failed to build with <?xml version=\"1.0\" encoding=\"UTF-8\"?> in system template"
    print "See the bug for further information - https://bugzilla.redhat.com/show_bug.cgi?id=761163"
    print "Checking if you have enough permission..."
    if os.geteuid() != ROOTID:
        print "You must have root permissions to run this script, I'm sorry buddy"
        return False #exit the test
        print "Cleanup configuration...."
    os.system("aeolus-cleanup")
    print "Running aeolus-configure....."
    if os.system("aeolus-configure") != SUCCESS:
        print "Some error raised in aeolus-configure !"
        return False
    print "Clearing log file for Image Factory"
    os.system("> " + LogFile)
    return True
   
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
            target_image.append(re.search(r'.*Target Image: ([a-zA-Z0-9\-]*).*:Status.*',retcode,re.I).group(1))

        except subprocess.CalledProcessError, e:
            print >>sys.stderr, "Execution failed:", e
            return False
        time.sleep(10) #sleep for 10 seconds        
    print "wait until build process is done"
    #setup counter to do not wait longer then 1 hour
    Counter=0
    
    for timage in target_image:
        print "Let\'s check this image: " + timage
        while os.system("aeolus-cli status --targetimage " + timage + "|grep -i building") == SUCCESS:
            Counter=Counter+1
            #wait a minute
            time.sleep(TIMEOUT)
            #after an hour break the 
            if Counter > TIMEOUT:
                print "Error: timeout over "+str(TIMEOUT)+" minutes !"
                return False
        
    print "Checking if there is any error in erro log of image factory"
    if os.system("grep -i \"FAILED\\|Error\" " + LogFile) == SUCCESS:
        print "Found FAILED or error message in log file:"
        outputtmp = os.popen("grep -i \"FAILED\\|Error\" " + LogFile).read()
        print outputtmp
        return False
    return True
 
#cleanup after test
def cleanTest():
    print "=============================================="
    print "Cleaning the mess after test"
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
