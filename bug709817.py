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
#        Regression test for Image Factory #bug709817
#        Created by koca (mkoci@redhat.com)
#        Date: 22/11/2011
#        Modified: 09/12/2011
#        Issue: iwhd initscript continues on in the face of failure
# return values:
# 0 - OK: everything OK
# 1 - Fail: setupTest wasn't OK
# 2 - Fail: bodyTest wasn't OK
# 3 - Fail: cleanTest wasn't OK
# 4 - Fail: any other error (reserved value)

#necessary libraries
import os
import sys

#constants 
SUCCESS=0
FAILED=1
RET_SETUPTEST=1
RET_BODYTEST=2
RET_CLEANTEST=3
ROOTID=0
#setup

def setupTest():
    print "=============================================="
    print "Setup of the regression test based on bz709817"
    print "See the test case https://tcms.engineering.redhat.com/case/122800/?from_plan=4953"
    print "Checking if you have enough permission..."
    if os.geteuid() != ROOTID:
        print "You must have root permissions to run this script, I'm sorry buddy"
        return False #exit the test
    print "Checking if iwhd is running..."
    if os.system("service iwhd status") == SUCCESS:
        print "Trying to stop iwhd"
        if os.system("service iwhd stop") != SUCCESS:
            print "Ergh, I couldn't stop iwhd.."
            return False   
    return True

#body
def bodyTest():
    print "=============================================="
    print "test being started"
    if os.system("service mongod status") == SUCCESS:
        print "stopping the mongod service"
        os.system("service mongod stop")
    if os.system("service iwhd start") > SUCCESS and os.system("service mongod status") > SUCCESS:
        print "Test PASSED. Now starting the iwhd with mongod started"
        if os.system("service mongod start") == SUCCESS and os.system("service iwhd start") == SUCCESS:
            return True
        else:
            return False
    else:
        print "Test FAILED."
        return False #test fails

#cleanup after test
def cleanTest():
    print "=============================================="
    print "Cleaning the mess after test"
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
             



