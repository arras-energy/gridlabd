[[/Tools/Resource]] -- Online resource accessor

Syntax: `gridlabd resource [OPTIONS ...]`

Options:

* `--content=RESOURCE,INDEX`: download RESOURCE located at INDEX

* `--debug`: enable traceback on exceptions

* `-h|--help|help`: get this help

* `--format=[raw|csv|json]`: output format

* `--index=RESOURCE`: get index for RESOURCE

* `--list[=FORMAT[,OPTIONS[,...]]`: list the available resources

* `--quiet`: suppress error output

* `--properties=RESOURCE`: get a list of resource properties

* `--silent`: suppress all output exception results

* `--test[=PATTERN]`: test resources matching pattern (default is '.*')

* `--verbose`: enable verbose output

* `--warning`: disable warning output

Description:

The online resource accessor delivers online resources to GridLAB-D applications.

Valid formats include `json` and `csv` (the default is 'raw').

Examples:

The following command list the properties on the online weather resources

    gridlabd resource --properties=weather

The following command lists the online weather resource index

    gridlabd resource --index=weather

The following command retrieves the online weather data for the specified location

    gridlabd resource --content=weather,WA-Seattle_Seattletacoma_Intl_A.tmy3



# Classes

## Annotated

Add context specific metadata to a type.

Example: Annotated[int, runtime_check.Unsigned] indicates to the
hypothetical runtime_check module that this type is an unsigned int.
Every other consumer of this type can ignore this metadata and treat
this type as int.

The first argument to Annotated must be a valid type.

Details:

- It's an error to call `Annotated` with less than two arguments.
- Nested Annotated are flattened::

Annotated[Annotated[T, Ann1, Ann2], Ann3] == Annotated[T, Ann1, Ann2, Ann3]

- Instantiating an annotated type is equivalent to instantiating the
underlying type::

Annotated[C, Ann1](5) == C(5)

- Annotated can be used as a generic type alias::

Optimized = Annotated[T, runtime.Optimize()]
Optimized[int] == Annotated[int, runtime.Optimize()]

OptimizedList = Annotated[List[T], runtime.Optimize()]
OptimizedList[int] == Annotated[List[int], runtime.Optimize()]


---

## BinaryIO

Typed version of the return of open() in binary mode.

---

## ForwardRef

Internal wrapper to hold a forward reference.

---

## Generic

Abstract base class for generic types.

A generic type is typically declared by inheriting from
this class parameterized with one or more type variables.
For example, a generic mapping type might be defined as::

class Mapping(Generic[KT, VT]):
def __getitem__(self, key: KT) -> VT:
...
# Etc.

This class can then be used as follows::

def lookup_name(mapping: Mapping[KT, VT], key: KT, default: VT) -> VT:
try:
return mapping[key]
except KeyError:
return default


---

## IO

Generic base class for TextIO and BinaryIO.

This is an abstract, generic version of the return of open().

NOTE: This does not distinguish between the different possible
classes (text vs. binary, read vs. write vs. read/write,
append-only, unbuffered).  The TextIO and BinaryIO subclasses
below capture the distinctions between text vs. binary, which is
pervasive in the interface; however we currently do not offer a
way to track the other distinctions in the type system.


---

## NewType

NewType creates simple unique types with almost zero
runtime overhead. NewType(name, tp) is considered a subtype of tp
by static type checkers. At runtime, NewType(name, tp) returns
a dummy callable that simply returns its argument. Usage::

UserId = NewType('UserId', int)

def name_by_id(user_id: UserId) -> str:
...

UserId('user')          # Fails type check

name_by_id(42)          # Fails type check
name_by_id(UserId(42))  # OK

num = UserId(5) + 1     # type: int


---

## ParamSpec

Parameter specification variable.

Usage::

P = ParamSpec('P')

Parameter specification variables exist primarily for the benefit of static
type checkers.  They are used to forward the parameter types of one
callable to another callable, a pattern commonly found in higher order
functions and decorators.  They are only valid when used in ``Concatenate``,
or as the first argument to ``Callable``, or as parameters for user-defined
Generics.  See class Generic for more information on generic types.  An
example for annotating a decorator::

T = TypeVar('T')
P = ParamSpec('P')

def add_logging(f: Callable[P, T]) -> Callable[P, T]:
'''A type-safe decorator to add logging to a function.'''
def inner(*args: P.args, **kwargs: P.kwargs) -> T:
logging.info(f'{f.__name__} was called')
return f(*args, **kwargs)
return inner

@add_logging
def add_two(x: float, y: float) -> float:
'''Add two numbers together.'''
return x + y

Parameter specification variables defined with covariant=True or
contravariant=True can be used to declare covariant or contravariant
generic types.  These keyword arguments are valid, but their actual semantics
are yet to be decided.  See PEP 612 for details.

Parameter specification variables can be introspected. e.g.:

P.__name__ == 'P'
P.__bound__ == None
P.__covariant__ == False
P.__contravariant__ == False

Note that only parameter specification variables defined in global scope can
be pickled.


---

## ParamSpecArgs

The args for a ParamSpec object.

Given a ParamSpec object P, P.args is an instance of ParamSpecArgs.

ParamSpecArgs objects have a reference back to their ParamSpec:

P.args.__origin__ is P

This type is meant for runtime introspection and has no special meaning to
static type checkers.


---

## ParamSpecKwargs

The kwargs for a ParamSpec object.

Given a ParamSpec object P, P.kwargs is an instance of ParamSpecKwargs.

ParamSpecKwargs objects have a reference back to their ParamSpec:

P.kwargs.__origin__ is P

This type is meant for runtime introspection and has no special meaning to
static type checkers.


---

## Protocol

Base class for protocol classes.

Protocol classes are defined as::

class Proto(Protocol):
def meth(self) -> int:
...

Such classes are primarily used with static type checkers that recognize
structural subtyping (static duck-typing), for example::

class C:
def meth(self) -> int:
return 0

def func(x: Proto) -> int:
return x.meth()

func(C())  # Passes static type check

See PEP 544 for details. Protocol classes decorated with
@typing.runtime_checkable act as simple-minded runtime protocols that check
only the presence of given attributes, ignoring their type signatures.
Protocol classes can be generic, they are defined as::

class GenProto(Protocol[T]):
def meth(self) -> T:
...


---

## Resource

Resource class

### `Resource()`

Construct resource object

Arguments:

* `file`: resource file (default is $GLD_ETC/resource.csv)


### `Resource.content(kwargs:dict) -> str`

Get resource content

Arguments:

* `**kwargs`: options (see `properties()`)

Returns:

* Resource contents


### `Resource.headers(kwargs:dict) -> Union`

Get resource header



### `Resource.index(kwargs:dict) -> Union`

Get resource index (if any)



### `Resource.list(pattern:str) -> list`

Get a list of available resources

Argument


### `Resource.properties(passthru:str, kwargs:dict) -> dict`

Get resource properties



---

## ResourceError

Resource exception

---

## SupportsAbs

An ABC with one abstract method __abs__ that is covariant in its return type.

---

## SupportsBytes

An ABC with one abstract method __bytes__.

---

## SupportsComplex

An ABC with one abstract method __complex__.

---

## SupportsFloat

An ABC with one abstract method __float__.

---

## SupportsIndex

An ABC with one abstract method __index__.

---

## SupportsInt

An ABC with one abstract method __int__.

---

## SupportsRound

An ABC with one abstract method __round__ that is covariant in its return type.

---

## str

str(object='') -> str
str(bytes_or_buffer[, encoding[, errors]]) -> str

Create a new string object from the given object. If encoding or
errors is specified, then the object must expose a data buffer
that will be decoded using the given encoding and error handler.
Otherwise, returns the result of object.__str__() (if defined)
or repr(object).
encoding defaults to sys.getdefaultencoding().
errors defaults to 'strict'.

---

## TextIO

Typed version of the return of open() in text mode.

# Functions

## `NamedTuple() -> None`

Typed version of namedtuple.

Usage in Python versions >= 3.6::

class Employee(NamedTuple):
name: str
id: int

This is equivalent to::

Employee = collections.namedtuple('Employee', ['name', 'id'])

The resulting class has an extra __annotations__ attribute, giving a
dict that maps field names to types.  (The field names are also in
the _fields attribute, which is part of the namedtuple API.)
Alternative equivalent keyword syntax is also accepted::

Employee = NamedTuple('Employee', name=str, id=int)

In Python versions <= 3.5 use::

Employee = NamedTuple('Employee', [('name', str), ('id', int)])


---

## `TypedDict() -> None`

A simple typed namespace. At runtime it is equivalent to a plain dict.

TypedDict creates a dictionary type that expects all of its
instances to have a certain set of keys, where each key is
associated with a value of a consistent type. This expectation
is not checked at runtime but is only enforced by type checkers.
Usage::

class Point2D(TypedDict):
x: int
y: int
label: str

a: Point2D = {'x': 1, 'y': 2, 'label': 'good'}  # OK
b: Point2D = {'z': 3, 'label': 'bad'}           # Fails type check

assert Point2D(x=1, y=2, label='first') == dict(x=1, y=2, label='first')

The type info can be accessed via the Point2D.__annotations__ dict, and
the Point2D.__required_keys__ and Point2D.__optional_keys__ frozensets.
TypedDict supports two additional equivalent forms::

Point2D = TypedDict('Point2D', x=int, y=int, label=str)
Point2D = TypedDict('Point2D', {'x': int, 'y': int, 'label': str})

By default, all keys must be present in a TypedDict. It is possible
to override this by specifying totality.
Usage::

class point2D(TypedDict, total=False):
x: int
y: int

This means that a point2D TypedDict can have any of the keys omitted.A type
checker is only expected to support a literal False or True as the value of
the total argument. True is the default, and makes all items defined in the
class body be required.

The class syntax is only supported in Python 3.6+, while two other
syntax forms work for Python 2.7 and 3.2+


---

## `cast() -> None`

Cast a value to a type.

This returns the value unchanged.  To the type checker this
signals that the return value has the designated type, but at
runtime we intentionally don't check anything (we want this
to be as fast as possible).


---

## `final() -> None`

A decorator to indicate final methods and final classes.

Use this decorator to indicate to type checkers that the decorated
method cannot be overridden, and decorated class cannot be subclassed.
For example:

class Base:
@final
def done(self) -> None:
...
class Sub(Base):
def done(self) -> None:  # Error reported by type checker
...

@final
class Leaf:
...
class Other(Leaf):  # Error reported by type checker
...

There is no runtime checking of these properties.


---

## `get_args() -> None`

Get type arguments with all substitutions performed.

For unions, basic simplifications used by Union constructor are performed.
Examples::
get_args(Dict[str, int]) == (str, int)
get_args(int) == ()
get_args(Union[int, Union[T, int], str][int]) == (int, str)
get_args(Union[int, Tuple[T, int]][str]) == (int, Tuple[str, int])
get_args(Callable[[], T][int]) == ([], int)


---

## `get_origin() -> None`

Get the unsubscripted version of a type.

This supports generic types, Callable, Tuple, Union, Literal, Final, ClassVar
and Annotated. Return None for unsupported types. Examples::

get_origin(Literal[42]) is Literal
get_origin(int) is None
get_origin(ClassVar[int]) is ClassVar
get_origin(Generic) is Generic
get_origin(Generic[T]) is Generic
get_origin(Union[T, int]) is Union
get_origin(List[Tuple[T, T]][int]) == list
get_origin(P.args) is P


---

## `get_type_hints() -> None`

Return type hints for an object.

This is often the same as obj.__annotations__, but it handles
forward references encoded as string literals, adds Optional[t] if a
default value equal to None is set and recursively replaces all
'Annotated[T, ...]' with 'T' (unless 'include_extras=True').

The argument may be a module, class, method, or function. The annotations
are returned as a dictionary. For classes, annotations include also
inherited members.

TypeError is raised if the argument is not of a type that can contain
annotations, and an empty dictionary is returned if no annotations are
present.

BEWARE -- the behavior of globalns and localns is counterintuitive
(unless you are familiar with how eval() and exec() work).  The
search order is locals first, then globals.

- If no dict arguments are passed, an attempt is made to use the
globals from obj (or the respective module's globals for classes),
and these are also used as the locals.  If the object does not appear
to have globals, an empty dictionary is used.  For classes, the search
order is globals first then locals.

- If one dict argument is passed, it is used for both globals and
locals.

- If two dict arguments are passed, they specify globals and
locals, respectively.


---

## `is_typeddict() -> None`

Check if an annotation is a TypedDict class

For example::
class Film(TypedDict):
title: str
year: int

is_typeddict(Film)  # => True
is_typeddict(Union[list, str])  # => False


---

## `no_type_check() -> None`

Decorator to indicate that annotations are not type hints.

The argument must be a class or function; if it is a class, it
applies recursively to all methods and classes defined in that class
(but not to methods defined in its superclasses or subclasses).

This mutates the function(s) or class(es) in place.


---

## `no_type_check_decorator() -> None`

Decorator to give another decorator the @no_type_check effect.

This wraps the decorator with something that wraps the decorated
function in @no_type_check.


---

## `overload() -> None`

Decorator for overloaded functions/methods.

In a stub file, place two or more stub definitions for the same
function in a row, each decorated with @overload.  For example:

@overload
def utf8(value: None) -> None: ...
@overload
def utf8(value: bytes) -> bytes: ...
@overload
def utf8(value: str) -> bytes: ...

In a non-stub file (i.e. a regular .py file), do the same but
follow it with an implementation.  The implementation should *not*
be decorated with @overload.  For example:

@overload
def utf8(value: None) -> None: ...
@overload
def utf8(value: bytes) -> bytes: ...
@overload
def utf8(value: str) -> bytes: ...
def utf8(value):
# implementation goes here


---

## `runtime_checkable() -> None`

Mark a protocol class as a runtime protocol.

Such protocol can be used with isinstance() and issubclass().
Raise TypeError if applied to a non-protocol class.
This allows a simple-minded structural check very similar to
one trick ponies in collections.abc such as Iterable.
For example::

@runtime_checkable
class Closable(Protocol):
def close(self): ...

assert isinstance(open('/some/file'), Closable)

Warning: this will check only the presence of the required methods,
not their type signatures!

