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
#        Regression test for Image Factory #bug759988 
#        Created by koca (mkoci@redhat.com)
#        Date: 02/12/2011
#        Issue: https://bugzilla.redhat.com/show_bug.cgi?id=759988 - checking aeolus-check-services 
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
RET_UNEXPECTED_ERROR=4
ROOTID=0
#setup
TmpFile="deleteme_bug759988"
CrazyCommand="aeolus-check-services |& tee " + TmpFile


def setupTest():
    print "=============================================="
    print "Setup of the regression test based on bug754982"
    print "See the test case https://tcms.engineering.redhat.com/case/122800/?from_plan=4953"
    print "Checking if you have enough permission..."
    if os.geteuid() != ROOTID:
        print "You must have root permissions to run this script, I'm sorry buddy"
        return False #exit the test
    print "Cleanup configuration...."
    if os.system("aeolus-cleanup") != SUCCESS:
        print "Some error raised in aeolus-cleanup !"
    print "running aeolus-configure -p ec2"
    if os.system("aeolus-configure -p ec2") != SUCCESS:
        print "Some error raised in aeolus-configure !"
        return False
    return True
   
#body
def bodyTest():
#check if aeolus-cleanup removes directory. /var/tmp and /var/lib/iwhd/images
    print "=============================================="
    print "test being started"
    os.system(CrazyCommand)
    if os.system("grep -4 -i fail " + TmpFile) == SUCCESS:
        print "Fail has been found ! See error logs."
        return False    
    return True
 
#cleanup after test
def cleanTest():
    print "=============================================="
    print "Cleaning the mess after test"
    if os.path.isfile(TmpFile):
        os.remove(TmpFile)    
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
