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
#        Regression test for Image Factory #bug740592
#        Created by koca (mkoci@redhat.com)
#        Date: 28/11/2011
#        Issue: aeolus-configure creates a /etc/rhevm.json file which imagefactory uses to push
#               images to rhevm.  The latest version of imagefactory now expects this in
#               /etc/imagefactory directory.
# return values:
# 0 - OK: everything OK
# 1 - Fail: setupTest wasn't OK
# 2 - Fail: bodyTest wasn't OK
# 3 - Fail: cleanTest wasn't OK
# 4 - Fail: any other error (reserved value)

#necessary libraries
import os
import sys
import shutil
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
#setup
ExpectedFile01="/etc/imagefactory/vsphere.json"
ExpectedFile02="/etc/imagefactory/rhevm.json"
RHEVMbugFile=configuration["RHEVMbugFile"]
RHEVMconfigureFile=configuration["RHEVMconfigureFile"]
RHEVMBackupFile=configuration["RHEVMBackupFile"]

def setupTest():
    print "=============================================="
    print "Setup of the regression test based on bug740592"
    print "Checking if you have enough permission..."
    if os.geteuid() != ROOTID:
        print "You must have root permissions to run this script, I'm sorry buddy"
        return False #exit the test
    
    #run the cleanup configuration
    print "Cleanup configuration...." 
    if os.system("aeolus-cleanup") != SUCCESS:
        print "Some error raised in aeolus-cleanup !"
        
    #first backup old rhvm file
    print "Backup old rhevm configuration file"
    if os.path.isfile(RHEVMconfigureFile):
        shutil.copyfile(RHEVMconfigureFile, RHEVMBackupFile)
    #then copy the conf. file
    print "Copy rhevm configuration file to /etc/aeolus-configure/nodes/rhevm_configure"
    if os.path.isfile(RHEVMbugFile):
        shutil.copyfile(RHEVMbugFile, RHEVMconfigureFile)
    else:
        print RHEVMbugFile + " didn't find!"
        return False
    
    #rename rhevm.json file if exists
    if os.path.isfile(ExpectedFile02):
        os.remove(ExpectedFile02)
        
    #now run aeolus-configure -p rhevm and uses the values from /etc/aeolus-configure/nodes/rhevm
    print "running aeolus-configure -p rhevm"
    if os.system("aeolus-configure -p rhevm") != SUCCESS:
        print "Some error raised in aeolus-configure with parameter -p rhevm !"
        return False
    return True
   
#body
def bodyTest():
#check if aeolus-cleanup removes directory. /var/tmp and /var/lib/iwhd/images
    print "=============================================="
    print "test being started"
    if os.path.isfile(ExpectedFile02):
        return True
    else:
        return False
 
#cleanup after test
def cleanTest():
    print "=============================================="
    print "Cleaning the mess after test"
    if os.path.isfile(RHEVMBackupFile):
        #copy file back
        shutil.copyfile(RHEVMBackupFile, RHEVMconfigureFile)
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
