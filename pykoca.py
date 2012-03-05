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
#
#load libraries
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

UNEXPECTED_ERROR_MESSAGE="An unexpected error - test FAILED !!"
SUCCESS_MESSAGE="PASSED"
SETUPTEST_MESSAGE="Setup of the test FAILED or an exception raised !!"
BODYTEST_MESSAGE="Body FAILED !!"
CLEANTEST_MESSAGE="Clean of the test FAILED !!"
ERROR_MESSAGE="Error message"
FAILED_MESSAGE="FAILED"
workspace="http://hudson.rhq.lab.eng.bos.redhat.com:8080/hudson/job/ImageFactory-KocaTesting2/ws/"
return_value=INIT_VALUE
final_message="\n================================================================ REPORT ================================================================\n"
summary_message_line="\n================================================================ SUMMARY ================================================================\n"
summary_message="\n"
Failed_counter=0 #how many tests failed
Success_counter=0 #how many tests succeed
html_header_refresh=""#"<html><head><meta http-equiv=\"refresh\" content=\"5\"></head><body><pre>"
html_footer=""#"</pre></body></html>"
argument_counter=0

os.system("date")
if len(sys.argv) > 1:
    os.system("echo \"We have " + str(len(sys.argv)) + " tests to do. So let's go ahead and start with the first one...\"")
    for arg in sys.argv[1:]:
        argument_counter = argument_counter + 1
        os.system("echo \"Test #" + str(argument_counter) +" ("+ arg + ") is being started. For further info see the log: " + workspace+arg.strip()+ ".log\"")
        os.system("echo \"" + html_header_refresh + "\" > " + arg.strip() + ".log") 
        rettmpvalue=os.system("python "+ arg + " &>> " + arg.strip() + ".log")
        os.system("echo \"" + html_footer + "\" >> " + arg.strip() + ".log")
        rettmpvalue=rettmpvalue >> 8 #necessary conversion to Unix readable return values
        if rettmpvalue == SUCCESS:
            final_message =  final_message + "\n" + arg + ".........." + SUCCESS_MESSAGE + " (" + workspace+arg.strip()+ ".log)\n"
            summary_message = summary_message + arg + ".........." + SUCCESS_MESSAGE + "\n"
            Success_counter = Success_counter + 1
            if return_value == INIT_VALUE:
                return_value = rettmpvalue
            elif return_value == FAILED:
                return_value = SUCCESS_FAILED
                
        elif rettmpvalue == RET_SETUPTEST:
            final_message =  final_message + "\n" + arg + ".........."+SETUPTEST_MESSAGE+" - See log file: "+workspace+arg.strip()+".log\n"
            final_message =  final_message + "The output of the error log is: \n"
            summary_message = summary_message + arg + ".........."+SETUPTEST_MESSAGE + "\n"
            Failed_counter = Failed_counter + 1
            retcode = os.popen("cat " + arg.strip() + ".log").read()
            final_message =  final_message + retcode
            if return_value == SUCCESS:
                return_value = SUCCESS_FAILED
            elif return_value == INIT_VALUE:
                return_value = FAILED
                
        elif rettmpvalue == RET_BODYTEST:
            final_message =  final_message + "\n" + arg + ".........."+BODYTEST_MESSAGE+" - See log file: "+workspace+arg.strip()+".log\n"
            final_message =  final_message + "The output of the error log is: \n"
            summary_message = summary_message + arg + ".........."+BODYTEST_MESSAGE + "\n"
            Failed_counter = Failed_counter + 1
            retcode = os.popen("cat " + arg.strip() + ".log").read()
            final_message =  final_message + retcode
            if return_value == SUCCESS:
                return_value = SUCCESS_FAILED
            elif return_value == INIT_VALUE:
                return_value = FAILED
                
        elif rettmpvalue == RET_CLEANTEST:
            final_message =  final_message + "\n" + arg + ".........." + CLEANTEST_MESSAGE + " - See log file: "+workspace+arg.strip()+".log\n"
            final_message =  final_message + "The output of the error log is: \n"
            summary_message = summary_message + arg + ".........." + CLEANTEST_MESSAGE + "\n"
            Failed_counter = Failed_counter + 1
            retcode = os.popen("cat " + arg.strip() + ".log").read()
            final_message =  final_message + retcode
            if return_value == SUCCESS:
                return_value = SUCCESS_FAILED
            elif return_value == INIT_VALUE:
                return_value = FAILED
                
        elif rettmpvalue == RET_UNEXPECTED_ERROR:
            final_message =  final_message + "\n" + arg + ".........."+UNEXPECTED_ERROR_MESSAGE+" - See log file: "+workspace+arg.strip()+".log\n"
            final_message =  final_message + "The output of the error log is: \n"
            summary_message = summary_message + arg + ".........." + UNEXPECTED_ERROR_MESSAGE + "\n"
            Failed_counter = Failed_counter + 1
            retcode = os.popen("cat " + arg.strip() + ".log").read()
            final_message =  final_message + retcode
            if return_value == SUCCESS:
                return_value = SUCCESS_FAILED
            elif return_value == INIT_VALUE:
                return_value = FAILED
                
        else:
            final_message =  final_message + "\n" + arg + ".........."+ERROR_MESSAGE+" - See log file: "+workspace+arg.strip()+".log\n"
            final_message =  final_message + "The output of the error log is: \n"
            summary_message = summary_message + arg + ".........." + ERROR_MESSAGE + "\n"
            Failed_counter = Failed_counter + 1
            retcode = os.popen("cat " + arg.strip() + ".log").read()
            final_message =  final_message + retcode
            if return_value == SUCCESS:
                return_value = SUCCESS_FAILED
            elif return_value == INIT_VALUE:
                return_value = FAILED
else:
    print "Please, provide at least one argument buddy !"
    sys.exit(return_value)
    
#now create final nice looking output message. 
print final_message
print summary_message_line + str(Failed_counter) + " tests FAILED\n" + str(Success_counter) + " tests Passed\n" + summary_message + summary_message_line
#exit with right return_value
sys.exit(return_value)

