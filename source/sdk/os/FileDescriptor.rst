os/FileDescriptor
=================

.. module:: os/FileDescriptor

.. function:: open (:cover:`~lang/types String` , :cover:`~lang/types Int` ) -> :cover:`~lang/types Int` 
    
.. function:: write (:cover:`~os/FileDescriptor FileDescriptor` , :cover:`~lang/types Pointer` , :cover:`~lang/types Int` ) -> :cover:`~lang/types Int` 
    
.. function:: read (:cover:`~os/FileDescriptor FileDescriptor` , :cover:`~lang/types Pointer` , :cover:`~lang/types Int` ) -> :cover:`~lang/types Int` 
    
.. function:: close (:cover:`~os/FileDescriptor FileDescriptor` ) -> :cover:`~lang/types Int` 
    
.. cover:: FileDescriptor
    
    :from: ``Int``
    .. method:: write (data: :cover:`~lang/types Pointer` , len: :cover:`~lang/types Int` ) -> :cover:`~lang/types Int` 
        
    .. method:: write~string (str: :cover:`~lang/types String` ) -> :cover:`~lang/types Int` 
        
    .. method:: read~toBuf (buf: :cover:`~lang/types Pointer` , len: :cover:`~lang/types Int` ) -> :cover:`~lang/types Int` 
        
    .. method:: read~evilAlloc (len: :cover:`~lang/types Int` ) -> :cover:`~lang/types Pointer` 
        
    .. method:: close -> :cover:`~lang/types Int` 
        
    .. method:: _errMsg (var: :cover:`~lang/types Int` , funcName: :cover:`~lang/types String` )
        
.. var:: STDIN_FILENO -> :cover:`~os/FileDescriptor FileDescriptor` 

.. var:: STDOUT_FILENO -> :cover:`~os/FileDescriptor FileDescriptor` 

.. var:: STDERR_FILENO -> :cover:`~os/FileDescriptor FileDescriptor` 

