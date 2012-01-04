#!/usr/bin/env python
'''
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
#        Target Specific Packages and Repos
#        Created by koca (mkoci@redhat.com)
#        Date: 03/01/2012
#        Issue: Starting with commit 057e66 we have introduced initial support for 
#               specifying target-specific packages and repositories outside of the TDL passed in to 
#               the build command. For now, you must specify this information in a local config file 
#               on your Factory host. This file must be /etc/imagefactory/target_content.xml
# return values:
# 0 - OK: everything OK
# 1 - Fail: setupTest wasn't OK
# 2 - Fail: bodyTest wasn't OK
# 3 - Fail: cleanTest wasn't OK
# 4 - Fail: any other error (reserved value)
'''
#necessary libraries
import os
import sys
import subprocess
#setup
target_content_file="/etc/imagefactory/target_content.xml"
target_template="""<template_includes>
  <include target='ec2' os='Fedora' version='14' arch='x86_64'>
    <packages>
      <package name='oz'/>
    </packages>
    <repositories>
      <repository name='oz-repository'>
        <url>http://repos.fedorapeople.org/repos/aeolus/oz/0.6.0/packages/fedora-14/x86_64/</url>
      </repository>
    </repositories>
  </include>
  <include target='rhevm' os='RHEL'>
    <packages>
      <package name='rhev-fedora-generic-package'/>
    </packages>
    <repositories>
      <repository name='rhev-repo'>
        <url>http://rhev.repo.com/</url>
      </repository>
    </repositories>
  </include>
</template_includes>"""
tmplogfileIF = "deletemeBuildImage.log"
crazyCommand_list=list()
templateEC2="templates/tspar_ec2.tdl"
templateEC2long="templates/tspar_ec2_long.tdl"
templateRHEVM="templates/tspar_rhevm.tdl"
templateRHEVMlong="templates/tspar_rhevm_long.tdl"
targets_list=["ec2", "rhevm"]
templates=[{"ec2" : templateEC2, "rhevm" : templateRHEVM},{"ec2" : templateEC2long, "rhevm" : templateRHEVMlong}]
for template_item in templates:
    for target in targets_list:
        crazyCommand_list.append("imagefactory --debug --target %s --template %s" % (target, template_item[target]) + " |& tee " + tmplogfileIF) 
LogFileIF="/var/log/imagefactory.log"
LogFileIWH="/var/log/iwhd.log"
#constants 
SUCCESS=0
FAILED=1
RET_SETUPTEST=1
RET_BODYTEST=2
RET_CLEANTEST=3
RET_UNEXPECTED_ERROR=4
ROOTID=0


def setupTest():
    print "=============================================="
    print "Checking if you have enough permission..."
    if os.geteuid() != ROOTID:
        print "You must have root permissions to run this script, I'm sorry buddy"
        return False #exit the test
    print "Cleanup configuration...."
    if os.system("aeolus-cleanup") != SUCCESS:
        print "Some error raised in aeolus-cleanup !"
    print "Running aeolus-configure....."
    if os.system("aeolus-configure -p ec2,mock,vsphere,rhevm") != SUCCESS:
        print "Some error raised in aeolus-configure !"
        return False
    print "Creating the " + target_content_file + " file"
    os.system("echo \"" + target_template + "\" > " + target_content_file)
    if not os.path.isfile(target_content_file):
        return False
    print "Clearing log file for Image Factory"
    os.system("> " + LogFileIF)
    print "Clearing log file for Image Warehouse"
    os.system("> " + LogFileIWH)   
    return True    


#body of the test
def bodyTest():      
    for item in crazyCommand_list:  
        try:
            print "\n============== " + item + " =============================================================================\n"
            retcode = os.popen(item).read()
            print "output is :"
            print retcode
        except subprocess.CalledProcessError, e:
            print >>sys.stderr, "Execution failed:", e
            return False   
        
    print "Checking if there is any error in the log of image factory"
    if os.system("grep -i \"FAILED\\|Error\" " + tmplogfileIF) == SUCCESS:
        print "Found FAILED or error message in log file:"
        outputtmp = os.popen("grep -i \"FAILED\\|Error\" " + tmplogfileIF).read()
        print outputtmp
        print "See the output from log file " + LogFileIF + ":"
        print "======================================================"
        outputtmp = os.popen("cat " + LogFileIF).read()
        print outputtmp
        print "See the output from log file " + LogFileIWH + ":"
        print "======================================================"
        outputtmp = os.popen("cat " + LogFileIWH).read()
        print outputtmp 
        print "Test FAILED =============================================================="       
        return False

    if os.system("grep -i \"COMPLETE\" " + tmplogfileIF) != SUCCESS:
        print "Build is not completed for some reason! It looks it stuck in the NEW status."
        print "Perhaps you can find something in the log file " + tmplogfileIF + ":"
        print "======================================================"
        outputtmp = os.popen("cat " + tmplogfileIF).read()
        print outputtmp
        print "See the output from log file " + LogFileIF + " too:"
        print "======================================================"
        outputtmp = os.popen("cat " + LogFileIF).read()
        print outputtmp    
        print "Test FAILED =============================================================="    
        return False    
    return True
 
#cleanup after test
def cleanTest():
    print "============================================== Cleaning the mess after test =============================================="   
    if os.path.isfile(target_content_file):
        os.remove(target_content_file)
    if os.path.isfile(tmplogfileIF):
        os.remove(tmplogfileIF)
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
        if not cleanTest():
            print "Even cleaning after body test wasn't sort of successful !"
        sys.exit(RET_BODYTEST)
else:
    print "=============================================="
    print "Test setup wasn't successful ! Test didn't even proceed !"
    cleanTest()
    sys.exit(RET_SETUPTEST)