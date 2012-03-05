#!/usr/bin/env python
''' encoding: utf-8
   Copyright 2011 Red Hat, Inc.

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
        Test that building images w/ the various parameters and templates using aeolus-cli tool
        Created by koca (mkoci@redhat.com)
        Date: 09/12/2011
        Issue: https://tcms.engineering.redhat.com/case/122786/?from_plan=4953 
 return values:
 0 - OK: everything OK
 1 - Fail: setupTest wasn't OK
 2 - Fail: bodyTest wasn't OK
 3 - Fail: cleanTest wasn't OK
 4 - Fail: any other error (reserved value)
'''
#necessary libraries
import os
import sys
import subprocess
import oauth2 as oauth
import httplib2
import json
import re
import time
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
TIMEOUT=180
MINUTE=60
#setup
LogFileIF=configuration["LogFileIF"]
LogFileIWH=configuration["LogFileIWH"]
# Define a list to collect all tests
alltests = list()
results = list()
#dirty information setup
consumer = oauth.Consumer(key='key', secret='secret')
#method
sig_method = oauth.SignatureMethod_HMAC_SHA1()
'''mandatory information'''
params = {'oauth_version':"0.4.4",
          'oauth_nonce':oauth.generate_nonce(),
          'oauth_timestamp':oauth.generate_timestamp(),
          'oauth_signature_method':sig_method.name,
          'oauth_consumer_key':consumer.key}
url_https="https://localhost:8075/imagefactory/builders/"
temporaryfile = "deleteme_build_image"
tmplogfileIF = "deletemeBuildImage.log"
templatesetupvar = ["""<packages>
        <package name='httpd'/>
        <package name='php'/>
      </packages>
""", """<files>
        <file name='/var/www/html/index.html' type='raw'>
          Aeolus Cloud Test page on Build Created
        </file>
      </files>""", """"""]
architectures=configuration['architectures']    
#["i386", "x86_64"]
installtypes=configuration["installtypes"]      
#["url", "iso"]
targetimages=configuration["targetimages"]      
#["ec2", "rhevm", "mock", "vsphere"]

VSPHEREbugFile=configuration["VSPHEREbugFile"]
VSPHEREconfigureFile=configuration["VSPHEREconfigureFile"]
VSPHEREBackupFile=configuration["VSPHEREBackupFile"]
RHEVMbugFile=configuration["RHEVMbugFile"]
RHEVMconfigureFile=configuration["RHEVMconfigureFile"]
RHEVMBackupFile=configuration["RHEVMBackupFile"]
#distribution to build in imagefactory and aeolus-image
distros={"RHEL-6":{"2":["http://download.englab.brq.redhat.com/released/RHEL-6/6.2/Server/", "/iso/RHEL6.2-20111117.0-Server-", "-DVD1.iso"],
                  "1":["http://download.englab.brq.redhat.com/released/RHEL-6/6.1/Server/", "/iso/RHEL6.1-20110510.1-Server-", "-DVD1.iso"]},
         "Fedora":{"15":["http://download.englab.brq.redhat.com/released/F-15/GOLD/Fedora/", "/iso/Fedora-15-", "-DVD.iso"],
                   "16":["http://download.englab.brq.redhat.com/released/F-16/GOLD/Fedora/", "/iso/Fedora-16-", "-DVD.iso"]}}

# Define an object to record test results
class TestResult(object):
    
    def __init__(self, *args, **kwargs):
        if len(args) == 7:
            (self.distro, self.version, self.arch, self.installtype, self.isourlstr, self.targetim, self.templatesetup) = args
        for k,v in kwargs.items():
            setattr(self, k, v)

    def __repr__(self):
        '''String representation of object'''
        return "test-{0}-{1}-{2}-{3}-{5}-{4}-additional template:{6}".format(*self.test_args())

    @property
    def name(self):
        '''Convenience property for test name'''
        return self.__repr__()

    def test_args(self):
        return (self.distro, self.version, self.arch, self.installtype, self.isourlstr, self.targetim, self.templatesetup)
#main function to execute the test
    def execute(self):
        if self.expect_pass:
            if self.methodCLI:
                return (self.name, self.__runTestAeolusCLI(self.test_args()), "#aeolus-cli")
            else:
                return (self.name, self.__runTestImageFactory(self.test_args()), "#imagefactory")
        else:
            if self.methodCLI:
                return (self.name, self.handle_exception(self.test_args()), "#aeolus-cli")
            else:
                return (self.name, self.__runTestImageFactory(self.test_args()), "#imagefactory")
        
    def __getTemplate(self, *args):
        (distro, version, arch, installtype, isourlstr, targetim, templatesetup) = args
        if installtype == "url":  
            repositorystr = isourlstr
        else:
            repositorystr = isourlstr + "/../../os/"  
        print "Testing %s-%s-%s-%s-%s-%s..." % (distro, version, arch, installtype, targetim, isourlstr),      
        tdlxml = """
    <template>
      <name>tester</name>
      <os>
        <name>%s</name>
        <version>%s</version>
        <arch>%s</arch>
        <install type='%s'>
          <%s>%s</%s>
        </install>
        <rootpw>redhat</rootpw>
      </os>
      <repositories>
        <repository name='koca-repository'>
            <url>%s</url>
        </repository>
     </repositories>
      %s
    </template>  
    """ % (distro, version, arch, installtype, installtype, isourlstr, installtype, repositorystr, templatesetup)
        return tdlxml
        
    def __runTestImageFactory(self, args):
        global temporaryfile
        global tmplogfileIF
        (distro, version, arch, installtype, isourlstr, targetim, templatesetup) = args
    #lets clean the logs so there is no obsolete records in it.     
        print "Clearing log file for Image Factory"
        os.system("> " + LogFileIF)
        print "Clearing log file for Image Warehouse"
        os.system("> " + LogFileIWH)
        tdlxml = self.__getTemplate(distro, version, arch, installtype, isourlstr, targetim, templatesetup)
        os.system("echo \""+tdlxml+"\" > "+temporaryfile)
        print "See the testing template"
        print "======================================================"
        outputtmp = os.popen("cat "+temporaryfile).read()
        print outputtmp        
        CrazyCommand = "imagefactory --debug --target %s --template " % targetim + temporaryfile + " |& tee " + tmplogfileIF
        try:
            print CrazyCommand
            retcode = os.popen(CrazyCommand).read()
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
            
    def __runTestAeolusCLI(self, args):
        global temporaryfile
        (distro, version, arch, installtype, isourlstr, targetim, templatesetup) = args
    #lets clean the logs so there is no obsolete records in it.     
        print "Clearing log file for Image Factory"
        os.system("> " + LogFileIF)
        print "Clearing log file for Image Warehouse"
        os.system("> " + LogFileIWH)
        tdlxml = self.__getTemplate(distro, version, arch, installtype, isourlstr, targetim, templatesetup)
        os.system("echo \""+tdlxml+"\" > "+temporaryfile)
        print "See the testing template"
        print "======================================================"
        outputtmp = os.popen("cat "+temporaryfile).read()
        print outputtmp        
        CrazyCommand = "aeolus-image build --environment default --target %s --template " % targetim + temporaryfile
        target_image = ""
        try:
            print CrazyCommand
            retcode = os.popen(CrazyCommand).read()
            print "output is :"
            print retcode
            #get target image BEGIN
            tempvar = re.search(r'.*\n.*\n([a-zA-Z0-9\-]*).*',retcode,re.I)
            if tempvar == None:
                print "An unknown error occurred. I'm not able to get target image ID. Check the log file out:"
                print "======================================================"
                outputtmp = os.popen("cat " + LogFileIF).read()
                print outputtmp
                print "Test FAILED =============================================================="
                return False
            else:
                target_image = tempvar.group(1)
            #get target image END
        except subprocess.CalledProcessError, e:
            print >>sys.stderr, "Execution failed:", e
            return False
        
        #setup counter to do not wait longer then 1 hour        
        print "Wait until build process is done"
        Counter=0                
        print "Let\'s check this image: " + target_image
        data = json.loads(self.__helpTest(target_image))
        print "Data Status: " + data['status']
        #while os.system("aeolus-cli status --targetimage " + timage + "|grep -i building") == SUCCESS:
        while data['status'] == "BUILDING":
            Counter=Counter+1
            #wait a minute
            time.sleep(MINUTE)
            data = json.loads(self.__helpTest(target_image))
            print "Data Status: " + data['status']
            #after an hour break the 
            if Counter > TIMEOUT:
                print "Error: timeout over "+str(TIMEOUT)+" minutes !"
                print "Test FAILED =============================================================="
                return False
            
        print "Checking if there is any error in the log of image factory"
        if os.system("grep -i \"FAILED\\|Error\" " + LogFileIF) == SUCCESS:
            print "Found FAILED or error message in log file:"
            outputtmp = os.popen("grep -i \"FAILED\\|Error\" " + LogFileIF).read()
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
        
    #check if status is either complete or building
        print "Let\'s check this image: " + target_image
        data = json.loads(self.__helpTest(target_image))
        print "Data Status for image "+target_image+": " + data['status']
        if data['status'] == "FAILED":
            print "Build "+target_image+" is not completed for some reason! It looks it stuck in the NEW status."
            print "Perhaps you can find something in the log file " + LogFileIF + ":"
            print "======================================================"
            outputtmp = os.popen("cat " + LogFileIF).read()
            print outputtmp
            print "See the output from log file " + LogFileIWH + " too:"
            print "======================================================"
            outputtmp = os.popen("cat " + LogFileIWH).read()
            print outputtmp  
            print "Test FAILED =============================================================="      
            return False 
        
        Counter=0
        while data['status'] in ("BUILDING", "New"):
            Counter=Counter+1
            #wait a minute
            time.sleep(MINUTE)
            data = json.loads(self.__helpTest(target_image))
            print "Data Status: " + data['status']
            if data['status'] == "New":
                #let's speed up a little bit process as New state looks like stuck
                Counter = Counter+12
            #after an hour break the 
            if Counter > TIMEOUT:
                print "Error: timeout over "+str(TIMEOUT)+" minutes !"
                print "Test FAILED =============================================================="
                return False           
        return True
    
    def handle_exception(self, args):
        try:
            self.getTemplateRunTest(args)
        except:
            print "(Un)expected error:", sys.exc_info()[0]
            raise
    
#this functions suppose to be as a help function to do not write one code multiple times
    def __helpTest(self, imageTest):
        url = url_https + imageTest
        req = oauth.Request(method='GET', url=url, parameters=params)
        sig = sig_method.sign(req, consumer, None)
        req['oauth_signature'] = sig
        r, c = httplib2.Http().request(url, 'GET', None, headers=req.to_header())
        response = 'Response headers: %s\nContent: %s' % (r,c)
        print response
        return c



def expectSuccess(*args):
    '''Create a TestResult object using provided arguments.  Append result to global 'alltests' list.'''
    global alltests
    '''Run build via imagefactory command''' 
    alltests.append(TestResult(*args, expect_pass=True, methodCLI=False))
    '''Run build via aeolus-cli command'''
    #alltests.append(TestResult(*args, expect_pass=True, methodCLI=True))
    
def expectFail(*args):
    '''Create a TestResult object using provided arguments.  Append result to
    global 'alltests' list.'''
    global alltests
    alltests.append(TestResult(*args, expect_pass=False, methodCLI=True))
    
def setupTest():
    print "=============================================="
    print "Setup of the sanity test based on 122786 test case from Image Factory test plan"
    print "See test plan: https://tcms.engineering.redhat.com/case/122786/?from_plan=4953"
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
    
    print "running aeolus-configure -p ec2,vsphere,rhevm,mock"
    if os.system("aeolus-configure -p ec2,vsphere,rhevm,mock") != SUCCESS:
        print "Some error raised in aeolus-configure !"
        return False
    
    print "Clearing log file for Image Factory"
    os.system("> " + LogFileIF)
    print "Clearing log file for Image Warehouse"
    os.system("> " + LogFileIWH)
    
    return True    


#body of the test
def bodyTest():
    global templatesetupvar
    print "=============================================="
    print "test being started"
    for templatesetup in templatesetupvar:
        for targetimage in targetimages:
            for arch in architectures:
                for installtype in installtypes:
                    for distro_p, distro in distros.iteritems():
                        for os_distro_p, os_distro in distro.iteritems():    
                            if installtype == "url":
                                isourlstrvar = "%s%s/os/" % (os_distro[0], arch)
                            else:
                                isourlstrvar = "%s%s%s%s%s" % (os_distro[0], arch, os_distro[1], arch, os_distro[2])
                            expectSuccess(distro_p, os_distro_p, arch, installtype, isourlstrvar , targetimage, templatesetup)                    
    
    for onetest in alltests:
        results.append(onetest.execute())
    print "==================================================================================================================================="
    returnvalue = True
    for result in results:
        if result[1] == False:
            returnvalue = False
            print "FAILED ...."+result[2]+": "+result[0]
        else:
            print "Passed ...."+result[2]+": "+result[0]       
    print "==================================================================================================================================="
    return returnvalue
 
#cleanup after test
def cleanTest():
    global temporaryfile
    global tmplogfileIF
    print "============================================== Cleaning the mess after test =============================================="   
    print "Removing temporary files"
    if os.path.isfile(temporaryfile):
        os.remove(temporaryfile)
    if os.path.isfile(tmplogfileIF):
        os.remove(tmplogfileIF)
    if os.path.isfile(RHEVMBackupFile):
        #copy file back rhevm
        shutil.copyfile(RHEVMBackupFile, RHEVMconfigureFile) 
    if os.path.isfile(VSPHEREBackupFile):
        #copy file back VSPHERE
        shutil.copyfile(VSPHEREBackupFile, VSPHEREconfigureFile)   
    return True    
#future TODO: maybe delete all iso's and images beneath directories /var/lib/imagefactory/images/ and /var/lib/oz/isos/
#TODO: need to create correct cleanup 
 
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
