import re
from typing import Callable, Iterable
from pyparsing import (
    infixNotation,
    opAssoc,
    Keyword,
    Word,
    QuotedString,
    alphas,
    alphanums,
    ParserElement,
)

ParserElement.enablePackrat()


class FieldMatch:
    def __init__(self, t):
        self.field = t[0]

    def does_match(self, x: dict) -> bool:
        return self.field in x

    def __str__(self) -> str:
        return self.field

    __repr__ = __str__


class StringFullMatch:
    def __init__(self, t):
        self.field = t[0]
        self.value = t[2]

    def does_match(self, x: dict) -> bool:
        return self.field in x and x[self.field] == self.value

    def __str__(self) -> str:
        return f'{self.field}="{self.value}"'

    __repr__ = __str__


class StringWildMatch:
    def __init__(self, t):
        self.field = t[0]
        self.value = t[2]

    def does_match(self, x: dict) -> bool:
        return self.field in x and re.fullmatch(self.value, x[self.field]) is not None

    def __str__(self) -> str:
        return f'{self.field}~"{self.value}"'

    __repr__ = __str__


class BoolNot:
    def __init__(self, t):
        self.arg = t[0][1]

    def does_match(self, x: dict) -> bool:
        return not self.arg.does_match(x)

    def __str__(self) -> str:
        return "!" + str(self.arg)

    __repr__ = __str__


class BoolBinOp:
    repr_symbol: str
    eval_fn: Callable[[Iterable[bool]], bool]

    def __init__(self, t):
        self.args = t[0][0::2]

    def __str__(self) -> str:
        sep = f" {self.repr_symbol} "
        return "(" + sep.join(map(str, self.args)) + ")"

    def does_match(self, x: dict) -> bool:
        return self.eval_fn(arg.does_match(x) for arg in self.args)

    __repr__ = __str__


class BoolAnd(BoolBinOp):
    repr_symbol = "&"
    eval_fn = all


class BoolOr(BoolBinOp):
    repr_symbol = "|"
    eval_fn = any


field_name = Word(alphas + "_", alphanums + "_").set_name("identifier")
field_match = field_name.copy().set_parse_action(FieldMatch)
full_match = (
    field_name + "=" + (Word(alphanums + "_") | QuotedString('"'))
).set_parse_action(StringFullMatch)

wild_match = (
    field_name + "~" + (Word(alphanums + "_.^$*?+[-]|{}") | QuotedString('"'))
).set_parse_action(StringWildMatch)

NOT = Keyword("not")
AND = Keyword("and")
OR = Keyword("or")

bool_operand = full_match | wild_match | field_match

bool_expr = infixNotation(
    bool_operand,
    [
        (NOT, 1, opAssoc.RIGHT, BoolNot),
        (AND, 2, opAssoc.LEFT, BoolAnd),
        (OR, 2, opAssoc.LEFT, BoolOr),
    ],
).set_name("boolean_expression")
