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
#        Regression test for Image Factory #bug755830 
#        Created by koca (mkoci@redhat.com)
#        Date: 06/02/2012
#        Issue: https://bugzilla.redhat.com/show_bug.cgi?id=755830 - oz fails to install an image with a backtrace generated
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
TIMEOUT=360
MINUTE=60
#setup variables, constants
TmpFile="deleteme_bug755830"
CrazyCommand="oz-install -d 4 templates/bug755830.tdl |& tee " + TmpFile

def setupTest():
    print "=============================================="
    print "Setup of the regression test based on Bug 755830 - oz fails to install an image with a backtrace generated"
    print "See the bug for further information - https://bugzilla.redhat.com/show_bug.cgi?id=755830"
    print "Checking if you have enough permission..."
    if os.geteuid() != ROOTID:
        print "You must have root permissions to run this script, I'm sorry buddy"
        return False #exit the test
    #run the cleanup configuration
    print "Cleanup configuration...." 
    if os.system("aeolus-cleanup") != SUCCESS:
        print "Some error raised in aeolus-cleanup !"
    print "Restart libvirtd daemon..."
    os.system("service libvirtd restart")
    return True


#body
def bodyTest():
    print "=============================================="
    print "test being started"
    print "Running command " + CrazyCommand
    os.system(CrazyCommand)
    print "Checking if there is any error or failed message in the log..."
    if os.system("grep -i \"error\\|failed\\|oz.OzException.OzException\" " +  TmpFile) == SUCCESS:
        print "See the output from log file " + TmpFile + ":"
        print "======================================================"
        outputtmp = os.popen("cat " + TmpFile).read()
        print outputtmp   
        return False
    return True
#cleanup after test
def cleanTest():
    print "=============================================="
    print "Cleaning the mess after test"
    if os.path.isfile(TmpFile):    
        os.remove(TmpFile)
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

