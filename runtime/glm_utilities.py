"""GridLAB-D utilities"""

import ast
import io
import tokenize
from datetime import datetime
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any

@dataclass
class MutableData:
    """Class that contains mutable data"""
    def __init__(self, *args, **kwargs):
        """Create a mutable data object

        Arguments
        ---------
        - `*args`: list of keys are initialize as `None`
        - `**wargs`: dict of key values to initialize

        Example
        -------

        The command

            data = MutableData("a","b",c=123,d='abc')
            data.b = 4.56
            print(data)

        outputs

            MutableData(a=None,b=4.56,c=123,d='abc')
        """
        for key in args:
            setattr(self,key,None)
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __repr__(self):
        attributes = ",".join([f"{x}={repr(y)}" for x,y in self.aslist()])
        return f"{self.__class__.__name__}({attributes})"

    def aslist(self) -> list[tuple[str,Any]]:
        """Return data as a list of tuples

        Returns
        -------
        - `list`: list of data item tuples
        """
        return [(x,getattr(self,x)) for x in dir(self) if not x.startswith("_") and not callable(getattr(self,x))]
    
    def asdict(self) -> dict:
        """Return data as a dict

        Returns
        -------
        - `dict`: dict of data item keys and values
        """
        return dict(self.aslist())

def name_unit(s:str) -> tuple[str,str]:
    """Split a string into a name and its units

    Arguments
    ---------
    - `s`: input string

    Returns
    -------
    - `tuple`: [`name`,`unit`] if input is `name[unit]` where `unit` is 
      `None` if no unit is found

    Example
    -------

    The command

        name_unit("time[s]")

    returns

        ["time","s"]
    """
    w = s.strip()
    if "[" in w and w.endswith("]"):
        v,u = w.split("[")
        return [v,u[:-1]]
    return [s,None]

def value_unit(
    s:str,
    autotype=False,
    nofail=False,
    ):
    """Split a string into a value and its units

    For 
    Arguments
    ---------
    - `s`: input string
    - `autotype`: enable automatic conversion to float or complex
    - `nofail`: raise exception on autotype failure instead of returning
      `str`

    Returns
    -------
    - `tuple`: [`value`,`unit`] if input is `value unit` otherwise [`value`,`None`]
      `None` if no unit is found

    Example
    -------

    The command

        value_unit("1.23 MW",autotype=True)

    returns

        (1.23,"MW")

    Caveat
    ------

    If there is error converting the value to complex or float, then the value
    is always returned as a string rather than returned as a float or double
    when `autotype` is `True`. Use `nofail=True` to raise the exception
    instead.
    """
    def _autotype(s):
        try:
            z = complex(s)
            if z.imag == 0:
                return z.real if autotype else f"{z.real:g}"
            return z if autotype else f"{z.real:g}{z.imag:+g}j"
        except ValueError:
            if nofail:
                raise
            return s

    w = s.strip()
    if " " in w:
        v,u = w.split(" ",1)
        return _autotype(v),u
    return _autotype(s),None

def autotype(
    x:str,
    allow=[int,float,complex,datetime,str],
    nodefault:bool=False
    ) -> int|float|complex|datetime|str:
    """Automatically change type of GridLAB-D data

    Arguments
    ---------

    Returns
    -------
    - `int`:
    - `float`:
    - `complex`:
    - `datetime`:
    - `str`:
    """
    if int in allow:
        try:
            return int(x)
        except ValueError:
            pass

    if float in allow:
        try:
            return float(x)
        except ValueError:
            pass

    if complex in allow:
        try:
            return complex(x)
        except ValueError:
            pass

    if datetime in allow:
        try:
            return datetime.fromisoformat(x)
        except ValueError:
            return x

    if nodefault:
        raise ValueError(f"autotype({repr(x)}) failed")

    return str(x)

class ExpressionError(Exception):
    """Raised when the boolean expression is invalid or uses disallowed syntax."""


# Keyword-like tokens that must keep their normal Python meaning rather than
# being treated as a dictionary field name.
_OPERATOR_WORDS = {"and", "or", "not", "in", "is", "True", "False", "None", "if", "else"}

_ALLOWED_NODES = (
    ast.Expression,
    ast.BoolOp, ast.And, ast.Or,
    ast.UnaryOp, ast.Not, ast.USub, ast.UAdd,
    ast.BinOp, ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod,
    ast.Compare, ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
    ast.In, ast.NotIn, ast.Is, ast.IsNot,
    ast.IfExp,
    ast.Name, ast.Load,
    ast.Constant,
    ast.List, ast.Tuple, ast.Set,
    ast.Subscript, ast.Slice,
)


def _rewrite_fields(expression: str, dict_var: str) -> str:
    """
    Rewrite bare field names in `expression` into `dict_var['field']` lookups,
    so that even reserved words like 'class' or 'for' can be used as plain
    identifiers in the input syntax (e.g. "class == 'warrior'").

    This works at the *token* level rather than the AST level: Python's
    tokenizer treats keywords and identifiers identically (both are NAME
    tokens) -- keyword-ness is only enforced later, by the parser. So we can
    freely relabel any NAME token that isn't one of our boolean/comparison
    operator words, before the string is ever parsed as Python syntax.
    """
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(expression).readline))
    except tokenize.TokenError as e:
        raise ExpressionError(f"Invalid expression syntax: {e}") from e

    out = []
    for tok in tokens:
        if tok.type == tokenize.NAME and tok.string not in _OPERATOR_WORDS:
            out.extend([
                (tokenize.NAME, dict_var),
                (tokenize.OP, "["),
                (tokenize.STRING, repr(tok.string)),
                (tokenize.OP, "]"),
            ])
        else:
            out.append((tok.type, tok.string))

    return tokenize.untokenize(out)


def _validate(tree: ast.AST, dict_var: str) -> None:
    for node in ast.walk(tree):
        if not isinstance(node, _ALLOWED_NODES):
            raise ExpressionError(f"Disallowed expression element: {type(node).__name__}")

        if isinstance(node, ast.Name) and node.id != dict_var:
            # Should not normally happen since _rewrite_fields converts every
            # field reference to a subscript first, but guard against it.
            raise ExpressionError(f"Unexpected bare identifier '{node.id}'")


def _matches(data: dict, expression: str, dict_var: str = "d") -> bool:
    """Test whether expression matches data

    Arguments
    ---------
    - `data`: dict of key/value pairs
    - `expression`: Python boolean expression on data

    Returns
    -------
    - `bool`: Result of boolean test of expression on data

    Description
    -----------

    Test whether `data` satisfies a boolean `expression` written in a
    Python-like syntax, using plain field names -- including reserved words:

        matches({"class": "warrior", "level": 12}, "class == 'warrior' and level > 10")
        # -> True

    Because Python identifiers can't be reserved words, "class == ..." isn't
    normally valid Python at all. This function works around that by
    rewriting each bare field name into a dict subscript (`d['class']`, etc.)
    at the token level -- before the string is parsed as Python -- since
    Python's tokenizer doesn't distinguish keywords from identifiers; only
    its parser does. The rewritten expression is then parsed and evaluated
    in a restricted sandbox that only allows boolean/comparison/arithmetic
    operators, literals, and subscripts -- no function calls, attribute
    access, or other arbitrary code.
    """
    rewritten = _rewrite_fields(expression, dict_var)

    try:
        tree = ast.parse(rewritten, mode="eval")
    except SyntaxError as e:
        raise ExpressionError(f"Invalid expression syntax: {e}") from e

    _validate(tree, dict_var)

    code = compile(tree, filename="<expression>", mode="eval")
    result = eval(code, {"__builtins__": {}}, {dict_var: data})
    return bool(result)

def find_objects(criteria:str,objects:dict) -> list[str]:
    """Find objects that match the search criteria

    Arguments
    ---------
    - `criteria`: Python boolean expression on data
    - `objects`: dict of object data on which criteria is evaluated

    Returns
    -------
    - `list`: list of objects that match the criteria
    """
    return [x for x,y in objects.items() if _matches(y,criteria)]
