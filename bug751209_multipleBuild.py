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
#        Regression test for Image Factory #bug751209
#        Created by koca (mkoci@redhat.com)
#        Date: 02/12/2011
#        Issue: concurrent builds causes some builds to fail 
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
from syck import *

#constants 
SUCCESS=0
FAILED=1
RET_SETUPTEST=1
RET_BODYTEST=2
RET_CLEANTEST=3
RET_UNEXPECTED_ERROR=4
ROOTID=0
TIMEOUT=360
#setup variables, constants
CrazyCommand=["aeolus-image build --target rhevm --template templates/bug751209.tdl;",\
              "aeolus-image build --target rhevm --template templates/bug751209.tdl;",\
              "aeolus-image build --target rhevm --template templates/bug751209.tdl;",\
              "aeolus-image build --target rhevm --template templates/bug751209.tdl;",\
              "aeolus-image build --target rhevm --template templates/bug751209.tdl;",\
              "aeolus-image build --target vsphere --template templates/bug751209.tdl;",\
              "aeolus-image build --target vsphere --template templates/bug751209.tdl;"]
configuration = load(file("configuration.yaml", 'r').read())
LogFileIF=configuration["LogFileIF"]
#load configuration from a file
RHEVMbugFile=configuration["RHEVMbugFile"]
RHEVMconfigureFile=configuration["RHEVMconfigureFile"]
RHEVMBackupFile=configuration["RHEVMBackupFile"]
VSPHEREbugFile=configuration["VSPHEREbugFile"]
VSPHEREconfigureFile=configuration["VSPHEREconfigureFile"]
VSPHEREBackupFile=configuration["VSPHEREBackupFile"]

def setupTest():
    print "=============================================="
    print "Setup of the regression test based on bug751209"
    print "See the test case https://tcms.engineering.redhat.com/case/122800/?from_plan=4953"
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
    
    #first backup old vsphere file
    print "Backup old vsphere configuration file"
    if os.path.isfile(VSPHEREconfigureFile):
        shutil.copyfile(VSPHEREconfigureFile, VSPHEREBackupFile)
    #then copy the conf. file
    print "Copy rhevm configuration file to /etc/aeolus-configure/nodes/vsphere_configure"
    if os.path.isfile(VSPHEREbugFile):
        shutil.copyfile(VSPHEREbugFile, VSPHEREconfigureFile)
    else:
        print VSPHEREbugFile + " didn't find!"
        return False
    
    print "running aeolus-configure -p vsphere,rhevm"
    if os.system("aeolus-configure -p vsphere,rhevm") != SUCCESS:
        print "Some error raised in aeolus-configure !"
        return False
    print "Clearing log file for Image Factory"
    os.system("> " + LogFileIF)
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
            target_image.append(re.search(r'.*\n.*\n([a-zA-Z0-9\-]*).*',retcode,re.I).group(1))
        except subprocess.CalledProcessError, e:
            print >>sys.stderr, "Execution failed:", e
            return False
        time.sleep(10) #sleep for 10 seconds        
    print "wait until build process is done"
    #setup counter to do not wait longer then 1 hour
    Counter=0
    
    for timage in target_image:
        print "Let\'s check this image: " + timage
        while os.system("aeolus-image status --targetimage " + timage + "|grep -i building") == SUCCESS:
            Counter=Counter+1
            #wait a minute
            time.sleep(60)
            #after an hour break the 
            if Counter > TIMEOUT:
                print "Error: timeout over "+str(TIMEOUT)+" minutes !"
                print "See the output from log file " + LogFileIF + ":"
                print "======================================================"
                outputtmp = os.popen("cat " + LogFileIF).read()
                print outputtmp
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
        return False
    
    print "The last check of status of each target image..."
    for timage in target_image:
        print "aeolus-image status --targetimage " + timage
        os.system("aeolus-image status --targetimage " + timage + "|grep -i COMPLETE")
    return True
 
#cleanup after test
def cleanTest():
    print "=============================================="
    print "Cleaning the mess after test"
    if os.path.isfile(RHEVMBackupFile):
        #copy file back rhevm
        shutil.copyfile(RHEVMBackupFile, RHEVMconfigureFile) 
    if os.path.isfile(VSPHEREBackupFile):
        #copy file back VSPHERE
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
