The JSON output of the ooc compiler (proposal)
==============================================

JSON output of the ooc compiler is useful for automated bindings generation for foreign programming languages and
for API documentation generation.

Example ooc code
----------------

.. code-block:: ooc

    Something: class {
	value: String
	init: func (a: Int, b: String)
	fiddle: static func (value: Bool) -> Bool
	doNothing: func ~withSomething <T> (something: T) -> Int
	doNothing: func -> Int
    }
    SomethingSpecial: class extends Something {
	doSomethingSpecial: func (yay: String)
    }
    CoolFloat: cover from Float {
	sqrt: func -> Float
    }
    five := 5
    ohYeah: func (no: Something)
    killCoolFloat: func (fl: CoolFloat@)
    killInteger: func (integer: Integer*)
    

The JSON format
---------------

The root structure is an objects that connects symbol names to objects; let's call them
entities.

It only contains the "root" entities which are part of the global namespaces (no class members)

.. code-block:: javascript

    {
	"Something": { ... },
	"SomethingSpecial": { ... },
	"CoolFloat": { ... },
	"ohYeah": { ... },
	"five": { ... },
	"killCoolFloat": { ... },
	"killInteger": { ... }
    }

Now, each entity has some essential keys:

``type``
    describes the type of the entity. Possible values are:
     * ``"function"``
     * ``"memberFunction"``
     * ``"globalVariable"``
     * ``"field"``
     * ``"class"``
     * ``"cover"``
``tag``
    defines an unique name for the entity.

Tags
~~~~

A tag defines an unique name for an entity. It is a mini description language:

.. productionlist:: 
    tag: modifier "(" parameters ")" 
       : identifier
    parameters: tag { "," tag }
    identifier: [a-zA-Z0-9_ ]+
    modifier: [a-zA-Z0-9_]+

Some examples for valid tags::

    test
    pointer(test)
    array(Int, 10)
    memberFunction(MyClass, yeaahh)

Tags for ordinary functions (i.e. not member functions), classes, covers and global variables are just the name of the symbol:

.. code-block:: javascript

    {
	"Something": {
	    "type": "class",
	    "tag": "Something"
	},
	"SomethingSpecial": {
	    "type": "class",
	    "tag": "SomethingSpecial"
	},
	"CoolFloat": {
	    "type": "cover",
	    "tag": "CoolFloat"
	},
	"five": {
	    "type": "variable",
	    "tag". "five"
	},
	"ohYeah": {
	    "type": "function",
	    "tag": "ohYeah"
	},
	"killCoolFloat": {
	    "type": "function",
	    "tag": "killCoolFloat"
	},
	"killInteger": {
	    "type": "function",
	    "tag": "killInteger"
	}
    }

Tags for members are consisting of a describing modifier and the class tag and the member name as parameters:

.. function:: memberFunction(class, name)
.. function:: field(class, name)

Tags for pointer and reference types just consist of the ``pointer``/``reference`` modifier and the type tag as parameter:

.. function:: pointer(type)
.. function:: reference(type)

Entities
--------

.. _json-function-entity:

``function``
~~~~~~~~~~~~

A function entity has the following attributes:

``name``
    Although the name is identical to the tag, it contains the name of the function. Wow.
``modifiers``
    A list of function modifiers. Possible modifiers are:

     * ``const``
     * ``static``
     * ``final``
     * ``inline``
     * ``proto`` (TODO: what's that?)
``genericTypes``
    The names of generic parameter types as a list.
``extern``
    Either ``true`` (if it's an extern function, but not aliased) or a string containing the original name of
    the function (if it's an aliased extern function).
``returnType``
    Either ``null`` if the function has no return value or the tag of the return type.
``arguments``
    A list of 2-element lists ``[name, argument tag, modifiers or null]``.
    Example::
	
	test: func (name: const String, age, foobar: Int*)

    generates

    .. code-block:: javascript

	[
	    ["name", "String", ["const"]],
	    ["age", "pointer(Int)", null],
	    ["foobar", "pointer(Int)", null]
	]

``memberFunction``
~~~~~~~~~~~~~~~~~~

A member function entity has the same attributes as the :ref:`function entity <json-function-entity>`.

.. note:: The convenient ``This`` type has to be resolved by the compiler.
	
.. _json-globalVariable-entity:

``globalVariable``
~~~~~~~~~~~~~~~~~~

``name``	
    Guess what!
``modifiers``
    A list of modifiers. Possible modifiers:

    * ``const``
    * ``static``
``value``
    The value of the variable as string, if it's known (i.e. for const variables), otherwise ``null``.
``varType``
    The tag of the type of the variable.

    .. note:: The compiler has to resolve the type of the variable for implicit assignments (``:=``).

``field``
~~~~~~~~~

A field entity has the same attributes as the :ref:`globalVariable entity <json-globalVariable-entity>`, but some
additional attributes:

``extern``
    Either ``true`` (if it's an extern field, but not aliased) or a string containing the original name of
    the field (if it's an aliased extern field).

.. _json-class-entity:

``class``
~~~~~~~~~

``name``
    Ha-Ha.
``genericTypes``
    A list of all generic type names or an empty list.
``extends``
    The tag of the class this class extends, or ``null``.
``members``
    A list of 2-element lists ``[name, entity]``.

``cover``
~~~~~~~~~

Same attributes as :ref:`class <json-class-entity>`, but additionally:

``from``
    The tag of the type we're covering.

Result
------

In the end, we have:

.. todo:: Incomplete

.. code-block:: javascript

     {
	"Something": {
	    "type": "class",
	    "tag": "Something",
	    "name": "Something",
	    "genericTypes": [],
	    "extends": null,
	    "members": [
		["value", {
		    "type": "field",
		    "tag": "field(value)",
		    "name": "value",
		    "value": null,
		    "varType": "Int",
		    "extern": false
		},
		]
	    ]
	},
	"SomethingSpecial": {
	    "type": "class",
	    "tag": "SomethingSpecial"
	},
	"CoolFloat": {
	    "type": "cover",
	    "tag": "CoolFloat"
	},
	"five": {
	    "type": "variable",
	    "tag". "five"
	},
	"ohYeah": {
	    "type": "function",
	    "tag": "ohYeah"
	},
	"killCoolFloat": {
	    "type": "function",
	    "tag": "killCoolFloat"
	},
	"killInteger": {
	    "type": "function",
	    "tag": "killInteger"
	}
    }