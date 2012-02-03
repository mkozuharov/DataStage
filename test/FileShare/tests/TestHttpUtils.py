# ---------------------------------------------------------------------
#
# Copyright (c) 2012 University of Oxford
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, --INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
# 
# ---------------------------------------------------------------------

# $Id: $
#
# Utility functions for testing HTTP
#

import os
import sys
import httplib
import urllib2
import logging

from TestConfig import TestConfig

logger = logging.getLogger('TestSHttpUtils')

# Execute a specified HTTP method using a supplied urllib2 opener object,
# following a single HTTP 301 redirection response

def do_HTTP_redirect(opener, method, uri, data, content_type):
    req=urllib2.Request(uri, data=data)
    if content_type: req.add_header('Content-Type', content_type)
    req.get_method = lambda: method
    message = (0,"Success")
    try:    
        url=opener.open(req)
    except urllib2.HTTPError as e:
        if e.code == 301:                # Follow redirection
            req=urllib2.Request( e.headers['Location'], data=data)
            if content_type: req.add_header('Content-Type', content_type)
            req.get_method = lambda: method
            try:            
                url=opener.open(req)            
            except urllib2.HTTPError as e:
                # HTTPError from redirected request
                message = (e.code,str(e))  
        else:
            # Original request error other than 301
            message = (e.code,str(e))  
    return message

def do_httpAuthenticationHandler(userName, userPass):
    passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
    passman.add_password(None, TestConfig.webdavbaseurl, userName, userPass)
    authhandler = urllib2.HTTPBasicAuthHandler(passman)
    return authhandler

def do_httpCreateFile(areaName, userName, userPass, fileName, createFileContent):
    authhandler = do_httpAuthenticationHandler(userName, userPass)
    opener = urllib2.build_opener(authhandler)
    urllib2.install_opener(opener)      
    # Write data to server
    createMessage = do_HTTP_redirect(opener, "PUT",
        TestConfig.webdavbaseurl + '/' + areaName + '/' + fileName, 
        createFileContent, 'text/plain')
    return createMessage

def do_httpReadFile(areaName, userName, userPass, fileName):
    logger.debug("do_httpReadFile %s %s %s %s"%(areaName, userName, userPass, fileName))
    authhandler = do_httpAuthenticationHandler(userName, userPass)
    opener = urllib2.build_opener(authhandler)
    urllib2.install_opener(opener)       
    phan=urllib2.urlopen(TestConfig.webdavbaseurl+'/'+ areaName +'/' + fileName)
    readFileContent = phan.read()
    return readFileContent

def do_httpUpdateFile(areaName, userName, userPass,fileName, updateFileContent):
    authhandler = do_httpAuthenticationHandler(userName, userPass)
    opener = urllib2.build_opener(authhandler)
    urllib2.install_opener(opener)      
    # Write/update data to server
    updateMessage = do_HTTP_redirect(opener, "PUT",
        TestConfig.webdavbaseurl+'/'+ areaName +'/' + fileName, 
        updateFileContent, 'text/plain')
    return updateMessage

def do_httpDeleteFile(areaName, userName, userPass,fileName):
    authhandler = do_httpAuthenticationHandler(userName, userPass)
    opener = urllib2.build_opener(authhandler)
    deleteMessage = do_HTTP_redirect(opener, "DELETE", 
        TestConfig.webdavbaseurl+'/'+ areaName +'/' + fileName,
        None, None)
    return deleteMessage
    

