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
#        Regression test for Image Factory #bug737099
#        Created by bcrochet (brad@redhat.com)
#        Date: 17/01/2012
#        Issue: RFE: screen shots could default to /var/www/html, include link in logs
#
# return values:
# 0 - OK: everything OK
# 1 - Fail: setupTest wasn't OK
# 2 - Fail: bodyTest wasn't OK
# 3 - Fail: cleanTest wasn't OK
# 4 - Fail: any other error (reserved value)

#necessary libraries
import os
import glob
import sys
import shlex
import shutil
from subprocess import Popen
from syck import *
import time
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
ozBugFile=configuration["ozBugFile"]
ozConfigFile=configuration["ozConfigFile"]
ozBackupFile=configuration["ozBackupFile"]
ozScreenshotDir=configuration["ozScreenshotDir"]

def setupTest():
    print "=============================================="
    print "Setup of the regression test based on bug740592"
    print "Checking if you have enough permission..."
    if os.geteuid() != ROOTID:
        print "You must have root permissions to run this script, I'm sorry buddy"
        return False #exit the test
    
    # backup old oz.cfg 
    print "Backup old oz configuration file"
    if os.path.isfile(ozConfigFile):
        shutil.copyfile(ozConfigFile, ozBackupFile)
    #then copy the conf. file
    print "Copy oz configuration file to /etc/oz/oz.cfg"
    if os.path.isfile(ozBugFile):
        shutil.copyfile(ozBugFile, ozConfigFile)
    else:
        print ozBugFile + " didn't find!"
        return False

    # clean the screenshot dir if it exists
    if os.path.isdir(ozScreenshotDir):
        shutil.rmtree(ozScreenshotDir)
    else:
        print ozScreenshotDir + " doesn't exist. That's ok"
  
    print "Create the screenshot dir. Bug filed for this (https://bugzilla.redhat.com/show_bug.cgi?id=782542)" 
    os.mkdir(ozScreenshotDir) 
  
    return True
 
#body
def bodyTest():
    print "=============================================="
    print "test being started"
    
    #now run imagefactory
    cmdline = "imagefactory --warehouse  http://localhost:9090/ --image_bucket images --build_bucket builds --target_bucket target_images --template_bucket templates --icicle_bucket icicles --provider_bucket provider_images --imgdir /var/lib/imagefactory/images --template templates/bug737099.tdl --target rhevm"
    print "running " + cmdline
    args = shlex.split(cmdline)
    proc = Popen(args)
   
    # Sleep a few seconds to let the build get started, then shut down the network
    time.sleep(5)
 
    # shut down the default network on libvirt
    print "Shutting down default network"
    if os.system("virsh net-destroy default") != SUCCESS:
        print "Network already down. That's ok"

    # now wait for the process to exit
    print "Wait for process to exit..."
    proc.wait()

    #    print "Some error raised in imagefactory with parameter imagefactory --warehouse  http://localhost:9090/ --image_bucket images --build_bucket builds --target_bucket target_images --template_bucket templates --icicle_bucket icicles --provider_bucket provider_images --imgdir /var/lib/imagefactory/images --template templates/bug737099.tdl --target rhevm"
    #    return False

    # TODO: Check output for actual screenshot taken and verify that is what we found. Then we can probabaly
    # stop removing and creating the screenshot dir
    #
    # Check to see if screenshot was written to ozScreenshotDir
    if not glob.glob(ozScreenshotDir+"/*.png"):
        return False

    return True
 
#cleanup after test
def cleanTest():
    print "=============================================="
    print "Cleaning the mess after test"
    if os.path.isfile(ozBackupFile):
        #copy file back
        shutil.copyfile(ozBackupFile, ozConfigFile)

    # clean the screenshot dir if it exists
    if os.path.isdir(ozScreenshotDir):
        shutil.rmtree(ozScreenshotDir)
    else:
        print ozScreenshotDir + " doesn't exist. That's ok"

    # restart default network
    if os.system("virsh net-start default") != SUCCESS:
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
