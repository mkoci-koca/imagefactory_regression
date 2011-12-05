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
#        Regression test for Image Factory #bug693514
#        Created by koca (mkoci@redhat.com)
#        Date: 22/11/2011
#        Modified: 23/11/2011
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
dirname1 = "/var/lib/iwhd/"
dirname2 = "/var/lib/iwhd/images/"
filename = "bug693514"

def setupTest():
    print "=============================================="
    print "Setup of the regression test based on bz709817"
    print "Checking if you have enough permission..."
    #if os.geteuid() != ROOTID:
    #    print "You must have root permissions to run this script, I'm sorry buddy"
    #    return False #exit the test
    print "Create directories /var/lib/iwhd and /var/lib/iwhd/images"
    if not os.path.isdir(dirname1):
        os.mkdir(dirname1)
    if not os.path.isdir(dirname2):
        os.mkdir(dirname2)
    if os.system("> " + dirname2 + filename) == SUCCESS:
        return True
    else:
        return True
    

#body
def bodyTest():
#check if aeolus-cleanup removes directory. /var/tmp and /var/lib/iwhd/images
    print "=============================================="
    print "test being started"
    print "Before aeolus-cleanup:"
    os.system("ls -la " + dirname1 + " " + dirname2)
    print "Running aeolus-cleanup"
    if os.system("aeolus-cleanup") != SUCCESS:
        sys.exit(RET_UNEXPECTED_ERROR)
    if os.system("ls -la " + dirname2) != SUCCESS and os.system("ls -la " + dirname1) != SUCCESS:
        return True
    else:
        return False
    

#cleanup after test
def cleanTest():
    print "=============================================="
    print "Cleaning the mess after test"
    print "Deleting file " + dirname2 + filename + " if exists"
    if os.path.isfile(dirname2 + filename):
        if not os.remove(dirname2 + filename):
            return False
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
