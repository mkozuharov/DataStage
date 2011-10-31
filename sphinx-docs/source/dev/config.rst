.. py:module:: datastage.config

``datastage.config``
====================

This is currently a stub module awaiting support for setting this stuff in
:py:mod:`datastage.admin`. Currently this configuration is hard-coded.


.. py:data:: config

   This object is a singleton containing the following attributes:

    .. py:attribute:: DATA_DIRECTORY

       The root of the directory to serve to research group members. In Admiral,
       this would have been /home/data/
   
    .. py:attribute:: SITE_NAME
    
       The name of the DataStage instance (e.g. ``'DataStage'``)
    
    .. py:attribute:: GROUP_NAME
    
       The name of the group whose DataStage this is.
    
    .. py:attribute:: GROUP_URL
    
       The main URL for the group (not this DataStage instance).

    .. py:attribute:: USER_AGENT
    
       The user-agent to use when making external HTTP requests.
