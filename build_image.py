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
FullLogFile=configuration["FullLogFile"]
# Define a list to collect all tests
alltests = list()
results = list()
#dirty information setup
ingoreThisMessages=""
ingoredmessages=configuration["ignored_error_messages"]
for i in ingoredmessages:
    if ingoreThisMessages == "":
        ingoreThisMessages="\"" + i 
    else:
        ingoreThisMessages = ingoreThisMessages + "\\|" + i
ingoreThisMessages = ingoreThisMessages + "\"" 
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
#distribution to build in imagefactory and aeolus-image
distros={"RHEL-6":{"2":["http://download.englab.brq.redhat.com/released/RHEL-6/6.2/Server/", "/iso/RHEL6.2-20111117.0-Server-", "-DVD1.iso"],
                  "1":["http://download.englab.brq.redhat.com/released/RHEL-6/6.1/Server/", "/iso/RHEL6.1-20110510.1-Server-", "-DVD1.iso"]},
         "Fedora":{"15":["http://download.englab.brq.redhat.com/released/F-15/GOLD/Fedora/", "/iso/Fedora-15-", "-DVD.iso"],
                   "16":["http://download.englab.brq.redhat.com/released/F-16/GOLD/Fedora/", "/iso/Fedora-16-", "-DVD.iso"]}}

# Define an object to record test results
class TestResult(object):
    _iCounter = 0    
    def __init__(self, *args, **kwargs):
        if len(args) == 7:
            (self.distro, self.version, self.arch, self.installtype, self.isourlstr, self.targetim, self.templatesetup) = args
        for k,v in kwargs.items():
            setattr(self, k, v)
        TestResult._iCounter = TestResult._iCounter + 1
        self._iCounter = TestResult._iCounter

    def __repr__(self):
        '''String representation of object'''
        return "test-{0}-{1}-{2}-{3}-{5}-{4}-additional template:\n{6}".format(*self.test_args())
    
    def getTestNumber(self):
        return getattr(self, "_iCounter") 

    @property
    def name(self):
        '''Convenience property for test name'''
        return self.__repr__()

    def test_args(self):
        return (self.distro, self.version, self.arch, self.installtype, self.isourlstr, self.targetim, self.__getTemplate(self.distro, self.version, self.arch, self.installtype, self.isourlstr, self.targetim, self.templatesetup))
#main function to execute the test
    def execute(self):
        if self.expect_pass:
            return (self.name, self.__runTestImageFactory(self.test_args()), self.getTestNumber())
        else:
            return (self.name, self.__runTestImageFactory(self.test_args()), self.getTestNumber())
        
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
        global FullLogFile
        (distro, version, arch, installtype, isourlstr, targetim, templatesetup) = args
        '''Clear images from previous build'''
        os.system("rm -f /var/lib/oz/isos/*")
        os.system("rm -f /var/lib/oz/isocontent/*")
        os.system("rm -fr /var/lib/imagefactory/images/*")
        os.system("rm -f /var/lib/libvirt/images/*")
        '''Lets copy log file into full log file'''          
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
            print retcode
        except subprocess.CalledProcessError, e:
            print >>sys.stderr, "Execution failed:", e
            return False   
        
        print "Copy ImageFactory log file into Full log file of the ImageFactory before we clear this ImageFactory log file"
        os.system("cat "+tmplogfileIF+" >> "+FullLogFile)   
    
        print "Checking if there is any error in the log of image factory"
        if os.system("grep -i \"error\\|failed\" " +  tmplogfileIF + "| grep -v "+ingoreThisMessages) == SUCCESS:
            print "Found FAILED or error message in log file:"
            outputtmp = os.popen("grep -i \"FAILED\\|Error\" " + tmplogfileIF + "| grep -v "+ingoreThisMessages).read()
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
    
    def handle_exception(self, args):
        try:
            self.getTemplateRunTest(args)
        except:
            print "(Un)expected error:", sys.exc_info()[0]
            raise

def expectSuccess(*args):
    '''Create a TestResult object using provided arguments.  Append result to global 'alltests' list.'''
    global alltests
    '''Run build via imagefactory command''' 
    alltests.append(TestResult(*args, expect_pass=True))
    
def expectFail(*args):
    '''Create a TestResult object using provided arguments.  Append result to
    global 'alltests' list.'''
    global alltests
    alltests.append(TestResult(*args, expect_pass=False))
    
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
    
    print "running aeolus-configure -p mock"
    if os.system("aeolus-configure -p mock") != SUCCESS:
        print "Some error raised in aeolus-configure -p mock !"
        return False
    
    print "Clearing log file for ImageFactory"
    os.system("> " + LogFileIF)
    print "Clearing log file for Image Warehouse"
    os.system("> " + LogFileIWH)
    print "Clearing Full Log file for ImageFactory"
    os.system("> " + FullLogFile)
    
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
    numberOfTests = str(len(results))
    print "============================= Final results of "+ numberOfTests + " tests ========================================================================="
    returnvalue = True
    for result in results:
        if result[1] == False:
            returnvalue = False
            print "Image " + str(result[2]) + "/" + numberOfTests + " FAILED ....: " + result[0]
        else:
            print "Image " + str(result[2]) + "/" + numberOfTests + " Passed ....: " + result[0]       
    print "============================== For full log see /var/log/"+FullLogFile+"====================================================================================================="
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
