native/win32/types
==================

.. module:: native/win32/types

.. function:: toLLong~twoPartsLargeInteger (lowPart, highPart: :cover:`~lang/types Long` ) -> :cover:`~lang/types LLong` 
    
.. function:: toULLong~twoPartsLargeInteger (lowPart, highPart: :cover:`~lang/types Long` ) -> :cover:`~lang/types ULLong` 
    
.. function:: toTimestamp~fromFiletime (fileTime: :cover:`~native/win32/types FileTime` ) -> :cover:`~lang/types Long` 
    
.. cover:: Handle
    
    :from: ``HANDLE``
.. cover:: LargeInteger
    
    :from: ``LARGE_INTEGER``
.. cover:: ULargeInteger
    
    :from: ``ULARGE_INTEGER``
.. cover:: FileTime
    
    :from: ``FILETIME``
.. var:: INVALID_HANDLE_VALUE -> :cover:`~native/win32/types Handle` 

