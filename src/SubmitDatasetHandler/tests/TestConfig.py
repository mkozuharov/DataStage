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
# See http://pyunit.sourceforge.net/pyunit.html
#
import cgi, SubmitDatasetUtils, os, re
from rdflib import URIRef
  
def setDatasetsBaseDir(base):
    global DatasetsBaseDir
    DatasetsBaseDir  =  base
    
    #global HostName         = "zoo-admiral-behav.zoo.ox.ac.uk"
    #global HostName         = "zoo-admiral-silk.zoo.ox.ac.uk"
    #global HostName         = "zoo-admiral-devel.zoo.ox.ac.uk"
    #global HostName         = "zoo-admiral-ibrg.zoo.ox.ac.uk"
    #global hostname         = "zakynthos.zoo.ox.ac.uk"
    global HostName, SiloName, Username, Password, FileName
    global FilePath, FileMimeType, ZipMimeType
    global DirName, DirPath 
    global DatasetsEmptyDirName, DatasetsEmptyDirPath
    global UpdatedTitle, UpdatedDescription, TestPat
    
    #HostName                 =  "localhost"
    HostName                 =  "zoo-admiral-ibrg.zoo.ox.ac.uk"
    SiloName                 =  "admiral"
    Username                 =  "admiral"
    Password                 =  "admiral"
    FileName                 =  "file1.txt"
    FilePath                 =  DatasetsBaseDir + os.path.sep + FileName
    FileMimeType             =  "text/plain"
    ZipMimeType              =  "application/zip"
    DirName                  =  "DatasetsTopDir"
    DirPath                  =  DatasetsBaseDir + os.path.sep + DirName
    DatasetsEmptyDirName     =  "DatasetsEmptySubDir"
    DatasetsEmptyDirPath     =  DatasetsBaseDir + os.path.sep + DirName + os.path.sep + DatasetsEmptyDirName
    UpdatedTitle             =  "Updated Title"
    UpdatedDescription       =  "Updated Description"
    TestPat                  =  re.compile("^.*$(?<!\.zip)")
    

    global ManifestName, ManifestFilePath
    ManifestName             = "manifest.rdf"
    ManifestFilePath         =  DatasetsBaseDir + os.path.sep + DirName + os.path.sep + ManifestName
    
    global formdata, updatedformdata

    formdata                 =  \
                                {  'datDir'      :  cgi.MiniFieldStorage('datDir'      ,   DirPath)
                                 , 'datId'       :  cgi.MiniFieldStorage('datId'       ,  "SubmissionToolTest")
                                 , 'title'       :  cgi.MiniFieldStorage('title'       ,  "Submission tool test title")
                                 , 'description' :  cgi.MiniFieldStorage('description' ,  "Submission tool test description")
                                 , 'user'        :  cgi.MiniFieldStorage('user'        ,  Username)
                                 , 'pass'        :  cgi.MiniFieldStorage('pass'        ,  Password)
                                 , 'endpointhost':  cgi.MiniFieldStorage('endpointhost',  HostName)
                                 , 'basepath'    :  cgi.MiniFieldStorage('basepath'    ,  "/"+SiloName+"/")                             
                                 , 'submit'      :  cgi.MiniFieldStorage('submit'      ,  "Submit")
                                 , 'directory'   :  cgi.MiniFieldStorage('directory'   ,   DirPath)
                                }
    updatedformdata          =   \
                                {  'datDir'      :  cgi.MiniFieldStorage('datDir'      ,   DirPath)
                                 , 'datId'       :  cgi.MiniFieldStorage('datId'       ,  "SubmissionToolTest")
                                 , 'title'       :  cgi.MiniFieldStorage('title'       ,  "Submission tool updated test title")
                                 , 'description' :  cgi.MiniFieldStorage('description' ,  "Submission tool updated test description")
                                 , 'user'        :  cgi.MiniFieldStorage('user'        ,  Username)
                                 , 'pass'        :  cgi.MiniFieldStorage('pass'        ,  Password)
                                 , 'endpointhost':  cgi.MiniFieldStorage('endpointhost',  HostName)
                                 , 'basepath'    :  cgi.MiniFieldStorage('basepath'    ,  "/"+SiloName+"/")       
                                 , 'submit'      :  cgi.MiniFieldStorage('submit'      ,  "Submit")      
                                }
    
    global DatasetId, DatasetDir, Title, Description, User, ElementValueList, ElementValueUpdatedList
    DatasetId                =  SubmitDatasetUtils.getFormParam('datId', formdata)
    DatasetDir               =  SubmitDatasetUtils.getFormParam('datDir', formdata)
    Title                    =  SubmitDatasetUtils.getFormParam('title', formdata)
    Description              =  SubmitDatasetUtils.getFormParam('description', formdata)
    User                     =  SubmitDatasetUtils.getFormParam('user', formdata)
    ElementValueList         =  [User, DatasetId, Title, Description]
    ElementValueUpdatedList  =  [User, DatasetId, UpdatedTitle, UpdatedDescription]
    
    global dcterms, oxds
    dcterms                  =  URIRef("http://purl.org/dc/terms/")
    oxds                     =  URIRef("http://vocab.ox.ac.uk/dataset/schema#") 
    
    global NamespaceDictionary
    NamespaceDictionary      =  {
                                   "dcterms"   : dcterms ,
                                   "oxds"      : oxds                    
                                 }
    global ElementCreatorUri,ElementIdentifierUri,ElementTitleUri,ElementDescriptionUri,ElementUriList 
    ElementCreatorUri        =  URIRef(dcterms + "creator")
    ElementIdentifierUri     =  URIRef(dcterms + "identifier")
    ElementTitleUri          =  URIRef(dcterms + "title")
    ElementDescriptionUri    =  URIRef(dcterms + "description")
    ElementUriList           =  [ElementCreatorUri, ElementIdentifierUri, ElementTitleUri, ElementDescriptionUri]
    return

