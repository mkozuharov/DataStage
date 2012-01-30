# $Id: $
#
# Test configuration parameters
#

class TestConfig:
    
    hostname         = "dataflow-vm1.oerc.ox.ac.uk"

     
    cifssharename    = "data"
    cifsmountpoint   = "mountdatastage"
    webdavmountpoint = "mountdatastagewebdav"
    webdavbaseurl    = "http://"+hostname+"/data/"
    readmefile       = "DATASTAGE.README"
    readmetext       = "This directory is the root of the DATASTAGE shared file system.\n"
    userAname        = "TestUser1"
    userApass        = "user1"
    userBname        = "TestUser2"
    userBpass        = "user2"
    userDname        = "TestUserD"
    userDpass        = "userd"
    userRGleadername = "TestLeader"
    userRGleaderpass = "leader"
    collabname       = "TestCollab"
    collabpass       = "collab"

# End.


