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
#        Frontend for tests. Returns nice-looking output for given list of tests
#        Created by koca (mkoci@redhat.com)
#        Date: 20/12/2011

import sys
import os
#setup variables and constants
SUCCESS=0
FAILED=1
SUCCESS_FAILED=2
INIT_VALUE=3
#error/fail in setup of the tests
RET_SETUPTEST=1
#error/fail in body of the tests
RET_BODYTEST=2 
#error/fail in clean of the tests
RET_CLEANTEST=3
#unexpected error occour
RET_UNEXPECTED_ERROR=4
#welcome message
WELCOME_MESSAGE=str(os.system("date")) + " - Tests are running...Please wait"
UNEXPECTED_ERROR_MESSAGE="An unexpected error - test FAILED !!"
SUCCESS_MESSAGE="PASSED"
SETUPTEST_MESSAGE="Setup of the test FAILED !!"
BODYTEST_MESSAGE="Body FAILED !!"
CLEANTEST_MESSAGE="Clean of the test FAILED !!"
ERROR_MESSAGE="Error message"
workspace="http://hudson.rhq.lab.eng.bos.redhat.com:8080/hudson/view/DEV-CloudForms/job/ImageFactory-KocaTesting2/ws/"
return_value=INIT_VALUE

if len(sys.argv) > 1:
    print WELCOME_MESSAGE
    for arg in sys.argv[1:]:
        print "Test " + arg + "is being started. For further info see the log: " + workspace+arg.strip()+ ".log" 
        rettmpvalue=os.system("python "+ arg + " >& " + arg.strip() + ".log")
        rettmpvalue=rettmpvalue >> 8 #necessary conversion to Unix readable return values
        if rettmpvalue == SUCCESS:
            print arg + ".........."+SUCCESS_MESSAGE
            if return_value == INIT_VALUE:
                return_value = rettmpvalue
            elif return_value == FAILED:
                return_value = SUCCESS_FAILED
                
        elif rettmpvalue == RET_SETUPTEST:
            print arg + ".........."+SETUPTEST_MESSAGE+" - See log file: "+workspace+arg.strip()+".log"
            if return_value == SUCCESS:
                return_value = SUCCESS_FAILED
            elif return_value == INIT_VALUE:
                return_value = FAILED
                
        elif rettmpvalue == RET_BODYTEST:
            print arg + ".........."+BODYTEST_MESSAGE+" - See log file: "+workspace+arg.strip()+".log"
            if return_value == SUCCESS:
                return_value = SUCCESS_FAILED
            elif return_value == INIT_VALUE:
                return_value = FAILED
                
        elif rettmpvalue == RET_CLEANTEST:
            print arg + ".........."+CLEANTEST_MESSAGE+" - See log file: "+workspace+arg.strip()+".log"
            if return_value == SUCCESS:
                return_value = SUCCESS_FAILED
            elif return_value == INIT_VALUE:
                return_value = FAILED
                
        elif rettmpvalue == RET_UNEXPECTED_ERROR:
            print arg + ".........."+UNEXPECTED_ERROR_MESSAGE+" - See log file: "+workspace+arg.strip()+".log"
            if return_value == SUCCESS:
                return_value = SUCCESS_FAILED
            elif return_value == INIT_VALUE:
                return_value = FAILED
                
        else:
            print arg + ".........."+ERROR_MESSAGE+" - See log file: "+workspace+arg.strip()+".log"
            if return_value == SUCCESS:
                return_value = SUCCESS_FAILED
            elif return_value == INIT_VALUE:
                return_value = FAILED
else:
    print "Please, provide at least one argument buddy !"
    sys.exit(return_value)
    
sys.exit(return_value)

