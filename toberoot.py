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
#        Dirty script to become root for running the scripts which require root privileges
#        Created by koca (mkoci@redhat.com)
#        Date: 05/12/2011
#        Modified: 05/12/2011
#        Issue: Get root privileges
# return values:


#necessary libraries
import pexpect
import sys

passwd = sys.argv[1]
child = pexpect.spawn('su -')
child.expect('Password:')
child.sendline(passwd)
child.expect('$')
child.interact()

