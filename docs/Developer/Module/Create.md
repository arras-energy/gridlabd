This page describes the elements required to create a new module and its class implementations

# Module C++ Main

You should use the [module template](https://github.com/arras-energy/module_template) to create a new module. This will provide you with a `main.cpp` and template `.cpp` and `.h` files needed to start your new module and new class implementations. 

# Module C++ Implementation of Classes

This section describes how to public properties in a class.

## Declaring Properties

The `gl_publish_variable(...)` function uses property offsets in memory. Every object attribute is listed sequentially in memory in the order in which they are declared. This function returns the difference in the memory address of an attribute from the start of the object in memory. It's defined by a macro, `GL_ATOMIC(type, attribute name)` which generates a callable function specific to every attribute it's applied to.

The code looks like this:
    static inline size_t get_##X##_offset(void) { return (char*)&(defaults->X)-(char*)defaults; };

`defaults` is a class attribute, a pointer to an object of the same type as the class it's a part of. Say we are looking at the `pole` class. `defaults` will be a pointer to a pole object. Confusingly, `defaults` is never inititialized to anything beyond NULL. How does this work? Back when this program was written in C, `defaults` pointed to a chunk of memory holding an object with all attributes initilized to default values. In C you could create a new object by simply copying this memory chunk. In C++ you need to declare all the attributes within an object, not just the object itself. The old method of setting defaults stopped working, so it's done differently now. The `defaults` pointer was retained as an attribute in the class declaration. The get offset function uses it for pointer math, finding the differences in memory location between the start of an object and all of it's attributes. Because a class declaration includes the type of all attributes, the compiler can figure out how much space they will take up in memory. (In C++ all types have a fixed size.)  'defaults' never needs to be initialized.

Published properties are declared using the `GL_*` declaration macros:
### `GL_ATOMIC(TYPE,NAME)` defines the following members:
  * `size_t get_NAME_offset(void)` - return the address of the value
  * `TYPE get_NAME()` - get the value
  * `gld_property get_NAME_property()` - get the property of the value
  * `TYPE get_NAME(gld_rlock &lock)` - get the value with a read lock
  * `TYPE get_NAME(gld_wlock &lock)` - get the value with a write lock
  * `void set_NAME(TYPE value)` - set a value
  * `void set_NAME(TYPE value, gld_wlock &lock)` - set a value with a write lock 
  * `gld_string get_NAME_string(void)` - get the value as a string
  * `void set_NAME(const char *text)` - set the value from a string
  * `void init_NAME(void)` - initialize the value to the default
  * `void init_NAME(TYPE value)` - initialize the value
### `GL_STRUCT(TYPE,NAME)` defines the following members:
  * `size_t get_NAME_offset(void)` - return the address of the value
  * `TYPE get_NAME()` - get the value
  * `gld_property get_NAME_property()` - get the property of the value
  * `TYPE get_NAME(gld_rlock &lock)` - get the value with a read lock
  * `TYPE get_NAME(gld_wlock &lock)` - get the value with a write lock
  * `void set_NAME(TYPE value)` - set a value
  * `void set_NAME(TYPE value, gld_wlock &lock)` - set a value with a write lock 
  * `gld_string get_NAME_string(void)` - get the value as a string
  * `void set_NAME(const char *text)` - set the value from a string
  * `void init_NAME(void)` - initialize the value to the default
  * `void init_NAME(TYPE value)` - initialize the value
### `GL_STRING(TYPE,NAME)` defines the following members:
  * `size_t get_NAME_offset(void)` - return the address of the value
  * `TYPE get_NAME()` - get the value
  * `gld_property get_NAME_property()` - get the property of the value
  * `char* get_NAME(gld_rlock &lock)` - get the value with a read lock
  * `char* get_NAME(gld_wlock &lock)` - get the value with a write lock
  * `char get_NAME(size_t index)` - get a character
  * `char get_NAME(size_t index, gld_rlock &lock)` - get a character with a read lock
  * `char get_NAME(size_t index, gld_wlock &lock)` - get a character with a write lock
  * `void set_NAME(TYPE *value)` - set the value
  * `void set_NAME(TYPE *value, gld_wlock &lock)` - set the value with a write lock 
  * `void set_NAME(size_t index, TYPE c)` - set a character
  * `void set_NAME(size_t index, TYPE c, gld_wlock &lock)` - set a character with a write lock
  * `gld_string get_NAME_string(void)` - get the value as a string
  * `void set_NAME(const char *text)` - set the value from a string
  * `void init_NAME(void)` - initialize the value to the default
  * `void init_NAME(TYPE value)` - initialize the value
### `GL_ARRAY(TYPE,NAME,SIZE)` defines the following members:
  * `size_t get_NAME_offset(void)` - returns the memory offset of the property
  * `gld_property get_NAME_property(void)` - returns the property
  * `TYPE* get_NAME(void)` - get values
  * `TYPE* get_NAME(gld_rlock &lock)` - get values using a read lock
  * `TYPE* get_NAME(gld_wlock &lock)` - get values using a write lock
  * `TYPE get_NAME(size_t index)` - get a value
  * `TYPE get_NAME(size_t index, gld_rlock &lock)` - get a value using a read lock
  * `TYPE get_NAME(size_t index, gld_wlock &lock)` - get a value using a write lock
  * `void set_NAME(T* values)` - copy values
  * `void set_NAME(T* values, gld_wlock &lock)` - copy values using a write lock
  * `void set_NAME(size_t index, T value)` - set a value
  * `void set_NAME(size_t index, T value, gld_wlock &lock)` - set a value using a write lock
### `GL_BITFLAGS(TYPE,NAME)` defines the following members:
  * `size_t get_NAME_offset(void)` - returns the memory offset for the property
  * `TYPE get_NAME(TYPE mask=-1)` - returns the bits using the mask
  * `inline gld_property get_NAME_property(void)` - return the property
  * `TYPE get_NAME(gld_rlock &lock)` - return the value using a read lock
  * `TYPE get_NAME(gld_wlock &lock)` - return the value using a write lock
  * `void set_NAME(TYPE p)` - sets the value
  * `void set_NAME_bits(TYPE bits)` - sets bits
  * `void clr_NAME_bits(TYPE bits)` - clears bits
  * `void set_##X(TYPE p, gld_wlock &lock)` - sets bits using a write lock
  * `gld_string get_##X##_string(void)` - returns the value as a string
  * `void set_##X(char *text)` - sets the value from a string
### `GL_METHOD(CLASS,NAME)` defines the following members:
  * `size_t get_##X##_offset(void)` - returns the memory offset for the property
  *	`int get_##X(char *buffer, size_t length)` - gets the output value of the method
  *	`int set_##X(char *buffer)` - sets the input value of the value
### `GL_OBJECT(NAME)` defines the following members:
  * `size_t get_NAME_offset(void)` - returns the memory offset for the property
  * `gld_object* get_NAME(void)` - returns a pointer to underlying object
  * `gld_property* get_NAME_property(void)` - returns a pointer to the property
  * `gld_object *get_NAME(gld_rlock &lock)` - returns a pointer to the underlying object using a read lock
  * `gld_object *get_NAME(gld_wlock &lock)` - returns a pointer to the underlying object using a write lock
  * `void set_NAME(OBJECT *ptr)` - sets the property to a new object pointer
  * `void set_NAME(const char *name)` - sets the property to a new object name
  * `void init_NAME(void)` - initializes the object pointer (sets to NULL)
  * `void init_NAME(OBJECT *ptr)` - initializes the object pointer
  * `OBJECT *get_NAME_object(void)` - get the object pointer

## Publishing properties

You should use the `gl_publish_variable(...)` to publish class properties.

The `PT_` prefix for variable specifications indicates Property Types:
*	`PT_void` - the type has no data
*	`PT_double` - the data is a double-precision float
*	`PT_complex` - the data is a complex value
*	`PT_enumeration` - the data is an enumeration
*	`PT_set` - the data is a set
*	`PT_int16` - the data is a 16-bit integer
*	`PT_int32` - the data is a 32-bit integer
*	`PT_int64` - the data is a 64-bit integer
*	`PT_char8` - the data is \p NULL -terminated string up to 8 characters in length
*	`PT_char32` - the data is \p NULL -terminated string up to 32 characters in length 
*	`PT_char256` - the data is \p NULL -terminated string up to 256 characters in length
*	`PT_char1024` - the data is \p NULL -terminated string up to 1024 characters in length
*	`PT_object` - the data is a pointer to a GridLAB object
*	`PT_delegated` - the data is delegated to a module for implementation (experimental)
*	`PT_bool` - the data is a true/false value, implemented as a C++ bool
*	`PT_timestamp` - timestamp value
*	`PT_double_array` - the data is a fixed length double[] (experimental)
*	`PT_complex_array` - the data is a fixed length complex[] (experimental)
*	`PT_real` - Single or double precision float ~ allows double values to be overriden (experimental)
*	`PT_float` - Single-precision float (experimental)
*	`PT_loadshape` - Loadshapes are state machines driven by schedules
*	`PT_enduse` - Enduse load data
*	`PT_random` - Randomized number
*	`PT_method` - Method entry point
*	`PT_string` - Variable length string (experimental)
*	`PT_python` - Python object (experimental)

*	`PT_AGGREGATE` - internal use only
*	`PT_KEYWORD` - used to add an enum/set keyword definition
*	`PT_ACCESS` - used to specify property access rights
*	`PT_SIZE` - used to setup arrayed properties
*	`PT_FLAGS` - used to indicate property flags next
*	`PT_INHERIT` - used to indicate that properties from a parent class are to be published
*	`PT_UNITS` - used to indicate that property has certain units (which following immediately as a string)
*	`PT_DESCRIPTION` - used to provide helpful description of property
*	`PT_EXTEND` - used to enlarge class size by the size of the current property being mapped
*	`PT_EXTENDBY` - used to enlarge class size by the size provided in the next argument
*	`PT_DEPRECATED` - used to flag a property that is deprecated
*	`PT_HAS_NOTIFY` - used to indicate that a notify function exists for the specified property
*	`PT_HAS_NOTIFY_OVERRIDE` - as `PT_HAS_NOTIFY`, but instructs the core not to set the property to the value being set
*	`PT_DEFAULT` - identifies the default value to use when creating the object property

The `PA_` prefix indicates to property access flags:
*	`PA_N = 0x00` - no access permitted
*	`PA_R = 0x01` - read access--modules can read the property
*	`PA_W = 0x02` - write access--modules can write the property
*	`PA_S = 0x04` - save access--property is saved to output
*	`PA_L = 0x08` - load access--property is loaded from input
*	`PA_H = 0x10` - hidden access--property is not revealed by modhelp
*	`PA_PUBLIC = (PA_R|PA_W|PA_S|PA_L)` - property is public (readable, writable, saved, and loaded)
*	`PA_REFERENCE = (PA_R|PA_S|PA_L)` - property is FYI (readable, saved, and loaded
*	`PA_PROTECTED = (PA_R)` - property is semipublic (readable, but not saved or loaded)
*	`PA_PRIVATE = (PA_S|PA_L)` - property is nonpublic (not accessible, but saved and loaded)
*	`PA_HIDDEN = (PA_PUBLIC|PA_H)` - property is not visible 

## Special properties

* `oclass` refers to the object class.
* `pclass` refers to the parent class (if any).
