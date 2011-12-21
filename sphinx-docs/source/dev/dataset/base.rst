.. py:module:: datastage.dataset.base

``datastage.dataset.base``
==========================

This module contains the base class for all types of dataset packaging formats.

It contains the following class, which is effectively abstract, and defines the
API for performing dataset submissions:

.. py:class:: Dataset 

   A :py:class:`Dataset` is responsible for collecting metadata for a dataset,
   packaging it ready for submission, and submitting it to a remote repository.
   
   Submission takes place in two stages:
   
   1. :py:meth:`preflight_submission` is run synchronously to make sure that
      the dataset will be accepted by the remote repository. If it seems
      unlikely (e.g. because of incorrect credentials, or missing metadata)
      the appropriate exception should be raised.
   2. If the preflight was successful, :py:meth:`complete_submission` is run
      asynchronously. This allows the submission to take as long as is needed
      without having to worry about HTTP time-outs for the user that initiates
      the submission.
      

   .. py:method:: __init__(path, title=None, description=None, identifier=None)
   
      Constructor. path is the root of the directory tree to be submitted.
      ``title``, ``description`` and ``identifier`` needn't be
      supplied here, but must otherwise be set as attributes before submitting.
   
   .. py:method:: update_manifest
   
      Causes the dataset to collect metadata to update the manifest.
   
   .. py:method:: save
   
      Saves the manifest to disk in a well-known location.
   
   .. py:method:: preflight_submission
   
      :param opener: a :py:class:`urllib2.OpenerDirector` instance
      :param repository: a :py:class:`datastage.web.dataset.models.Repository` instance
      :raises: :py:exc:`Dataset.IncompleteMetadataException`
      :raises: :py:exc:`Dataset.DatasetIdentifierRejected`
   
      As explained above, this method should carry out the necessary checks to
      ensure that the submission will be successful.
      
      The ``opener`` should have the necessary authentication-handling for the
      remote repository.
      
   
   .. py:method:: complete_submission
   
      :param opener: a :py:class:`urllib2.OpenerDirector` instance
      :param repository: a :py:class:`datastage.web.dataset.models.Repository` instance
      :param update_status: a function that can be called to report the status of the submission
   
      This method complete the dataset submission.
      
      The ``opener`` and ``repository`` arguments have the same requirements
      as for :py:meth:`preflight_submission`.
      
      At appropriate points in time it should call ``update_status`` with an appropriate
      status from the following list:
      
      * ``"started"``
      * ``"transfer"``
      * ``"submitted"``


Concrete subclasses of :py:class:`Dataset`
------------------------------------------

The following implementations exist:

:py:class:`datastage.dataset.oxds.OXDSDataset`
   For submitting datasets to DataBank instances.


Exceptions
----------

.. py:exception :: Dataset.IncompleteMetadataException
   
   Raised when there is missing metadata that would be required when
   submitting this dataset.
   
.. py:exception:: Dataset.DatasetIdentifierRejected

   Raised if the remote repository takes objection to a dataset's desired
   identifier.
   
.. py:exception:: Dataset.DatasetIdentifierAlreadyExists
   
   :extends: :py:exc:`Dataset.DatasetIdentifierRejected`
      
   Raised if the remote repository already has a dataset by the desired
   identifier.
   
Both :py:exc:`DatasetIdentifierRejected` and :py:exc:`DatasetIdentifierRejected`
have human-readable :py:func:`unicode` return values.
      