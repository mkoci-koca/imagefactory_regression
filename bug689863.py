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
#        Regression test for Image Factory #bug689863
#        Created by koca (mkoci@redhat.com)
#        Date: 28/11/2011
#        Modified: 28/11/2011
#        Issue: aeolus-configure deploys /etc/init.d/iwhd and /etc/iwhd/conf.js, however this
#               is no longer required, as the latest iwhd RPM contains those files.
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
#TMPFILE="bug689863.tmp"
file01="/etc/init.d/iwhd"
file02="/etc/iwhd/conf.js"
#Output1="5S.T..... /etc/iwhd/conf.js"
Output=""

def setupTest():
    print "=============================================="
    print "Setup of the regression test based on bug689863"
    print "Checking if you have enough permission..."
    if os.geteuid() != ROOTID:
        print "You must have root permissions to run this script, I'm sorry buddy"
        return False #exit the test
    print "running aeolus-configure"
    # if os.system("aeolus-configure") != SUCCESS:
    #     print "Some error raised in aeolus-configure !"
    #     return False
    return True
   
#body
def bodyTest():
#check if aeolus-cleanup removes directory. /var/tmp and /var/lib/iwhd/images
    print "=============================================="
    print "test being started"
    #/etc/init.d/iwhd and /etc/iwhd/conf.js should not be touched by running aeolus-configure
    stdout_handle = os.popen("rpm -V iwhd", "r")
    #Output = stdout_handle.read
    #  return_code = stdout_handle.returncode
    #return_code = 0
    for Output in stdout_handle.readlines():
        print "myresult:",Output,
        if Output.find(file01) != -1 or Output.find(file02) != -1:
            return False
    return True
 
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
