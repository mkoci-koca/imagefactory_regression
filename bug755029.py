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
#        Regression test for Image Factory Bug 755029 
#        Created by koca (mkoci@redhat.com)
#        Date: 04/01/2011
#        Issue: aeolus-cli push displays provider account passwd 
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

#constants 
SUCCESS=0
FAILED=1
RET_SETUPTEST=1
RET_BODYTEST=2
RET_CLEANTEST=3
RET_UNEXPECTED_ERROR=4
ROOTID=0
TIMEOUT=180
#setup
configuration = load(file("configuration.yaml", 'r').read())

#load configuration from a file
VSPHEREbug755029File=configuration["VSPHEREbug755029File"]
password_yaml = load(file(VSPHEREbug755029File, 'r').read())
VSPHEREconfigureFile=configuration["VSPHEREconfigureFile"]
VSPHEREBackupFile=configuration["VSPHEREBackupFile"]

TmpFile="deleteme_bug755029"
CrazyCommand="imagefactory --debug --target vsphere --template templates/bug755029.tdl |& tee " + TmpFile

#CrazyCommand="aeolus-image build --target vsphere --template templates/bug755029.tdl --environment default;"
LogFileIF=configuration["LogFileIF"]
LogFileIWH=configuration["LogFileIWH"]
target_image=""

def setupTest():
    print "=============================================="
    print "Setup of the regression test based on bug755029"
    print "Checking if you have enough permission..."
    if os.geteuid() != ROOTID:
        print "You must have root permissions to run this script, I'm sorry buddy"
        return False #exit the test
    
    #run the cleanup configuration
    print "Cleanup configuration...." 
    if os.system("aeolus-cleanup") != SUCCESS:
        print "Some error raised in aeolus-cleanup !"
        
    #first backup old vsphere file
    print "Backup old vsphere configuration file"
    if os.path.isfile(VSPHEREconfigureFile):
        shutil.copyfile(VSPHEREconfigureFile, VSPHEREBackupFile)
    #then copy the conf. file
    print "Copy rhevm configuration file to /etc/aeolus-configure/nodes/vsphere_configure"
    if os.path.isfile(VSPHEREbug755029File):
        shutil.copyfile(VSPHEREbug755029File, VSPHEREconfigureFile)
    else:
        print VSPHEREbug755029File + " didn't find!"
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
   
#body
def bodyTest():
#check if aeolus-cleanup removes directory. /var/tmp and /var/lib/iwhd/images
    print "=============================================="
    print "test being started"
    print "Running command " + CrazyCommand
    retcode = os.popen(CrazyCommand).read()
    print retcode
    print "Checking if there is any error or failed message in the log..."
    if os.system("grep -i \"error\\|failed\" " +  TmpFile + "| grep -v \"failed to create directory: File exists\"") == SUCCESS:
        print "See the output from log file " + LogFileIF + ":"
        print "======================================================"
        outputtmp = os.popen("cat " + LogFileIF).read()
        print outputtmp
        print "See the output from log file " + LogFileIWH + ":"
        print "======================================================"
        outputtmp = os.popen("cat " + LogFileIWH).read()
        print outputtmp     
        return False     
    print "Checking if there is any visible password "+password_yaml['classes']['default']["vsphere_password"]+" in error log of image factory"
    if os.system("grep -i \""+password_yaml['classes']['default']["vsphere_password"]+"\" " + LogFileIF) == SUCCESS:
        print "Found "+password_yaml['classes']['default']["vsphere_password"]+":"
        outputtmp = os.popen("grep -i \""+password_yaml['classes']['default']["vsphere_password"]+"\" " + LogFileIF).read()
        print outputtmp
        print "See the output from log file " + LogFileIF + ":"
        print "======================================================"
        outputtmp = os.popen("cat " + LogFileIF).read()
        print outputtmp
        return False
    return True
 
#cleanup after test
def cleanTest():
    print "=============================================="
    print "Cleaning the mess after test"
    if os.path.isfile(VSPHEREBackupFile):
        #copy file back VSPHERE
        shutil.copyfile(VSPHEREBackupFile, VSPHEREconfigureFile) 
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
