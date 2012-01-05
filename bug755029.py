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
import re
import subprocess
import time

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
CrazyCommand="aeolus-cli build --target vsphere --template templates/bug755029.tdl;"
LogFile="/var/log/imagefactory.log"
target_image=""

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
    os.system("> " + LogFile)
    return True
   
#body
def bodyTest():
#check if aeolus-cleanup removes directory. /var/tmp and /var/lib/iwhd/images
    print "=============================================="
    print "test being started"
    try:
        print CrazyCommand
        retcode = os.popen(CrazyCommand).read()
        print "output is :"
        print retcode
        target_image = (re.search(r'.*Target Image: ([a-zA-Z0-9\-]*).*:Status.*',retcode,re.I).group(1))

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
            
    print "Checking if there is any visible password "+password_yaml["vsphere_password"]+" in error log of image factory"
    if os.system("grep -i \""+password_yaml["vsphere_password"]+"\" " + LogFile) == SUCCESS:
        print "Found "+password_yaml["vsphere_password"]+":"
        outputtmp = os.popen("grep -i \""+password_yaml["vsphere_password"]+"\" " + LogFile).read()
        print outputtmp
        print "See the output from log file " + LogFile + ":"
        print "======================================================"
        outputtmp = os.popen("cat " + LogFile).read()
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
