from collections import namedtuple
from enum import Enum
import string

CONST = ("1", "0")
BINARY_OP = ("+", ".")
UNARY_OP = ("~",)
PAREN = ("(", ")")

class Parser:
    def __init__(self, input_string):
        Parser.validate(input_string)
        self.tokens = input_string
        self.token_index = 0
        self.syntax_tree = self.parse_expr()

    @staticmethod
    def validate(input_string):
        # valid_tokens = CONST + BINARY_OP + UNARY_OP + PAREN
        # for char in input_string:
        #     if char not in valid_tokens:
        #         raise ValueError("Illegal token: " + char)
        pass

    def next(self):
        self.token_index += 1
        try:
            return self.tokens[self.token_index - 1]
        except IndexError:
            return None

    def peek(self):
        try:
            return self.tokens[self.token_index]
        except IndexError:
            return None

    def parse_expr(self):
        current_expr = self.parse_term()
        while self.peek() in BINARY_OP:
            current_expr = current_expr.binary_combine(operator=self.next(), other=self.parse_term())
        return current_expr

    def parse_term(self):
        if self.peek() in CONST or self.peek().isalpha():
            return Node(self.next())
        elif self.peek() in PAREN:
            self.next()  # (.
            expr = self.parse_expr()
            self.next()  # ).
            return expr
        elif self.peek() in UNARY_OP:
            unary_op = self.next()
            next_term = self.parse_term()
            return next_term.unary_combine(unary_op)


class Node:
    def __init__(self, value=None, children=None):
        self.value = value
        if children is not None:
            if all(isinstance(child, Node) for child in children):
                self.children = children
            else:
                raise TypeError("All children must be type Node")
        else:
            self.children = []


    def get_children_values(self):
        return [child.value for child in self.children]

    def is_terminal(self):
        return len(self.children) == 0

    def binary_combine(self, other, operator):
        return Node(operator, children=[self, other])

    def unary_combine(self, operator):
        return Node(operator, children=[self])

    def __eq__(self, other):
        return self.value == other.value

    def __str__(self):
        return Node.__str__helper(self, indent=0).strip("\n")

    def __str__helper(self, indent):
        output = "  " * indent + str(self.value) + "\n"
        if self.is_terminal():
            return output
        for child in self.children:
            output += Node.__str__helper(child, indent+1)
        return output


def main():
    parser = Parser("~A.(B+A)+(~(C+A))")
    print(parser.syntax_tree)

if __name__ == "__main__":
    main()

