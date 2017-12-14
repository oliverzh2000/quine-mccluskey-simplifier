import copy
import itertools
import numpy as np

CONST = ("1", "0")
OP = ("+", ".")
UNARY_OP = ("~",)
PAREN = ("(", ")")


class Algebra:
    @staticmethod
    def reduce_not(node):
        if not node.is_terminal():
            if node.value == "~" and node.child.value == "~":
                node.replace_with(node.child.child)
            else:
                for child in node.children:
                    Algebra.reduce_not(child)

    @staticmethod
    def reduce_distributive(node):
        if node.value in OP and node.children_values() == [Algebra.other_op(node.value)] * len(node.children):
            left_child = node.children[0]
            right_child = node.children[1]
            if len(left_child.children) == len(right_child.children):
                try:
                    common_node = left_child.children[
                        left_child.children_hashes().index(set(left_child.children_hashes()).
                                                           intersection(right_child.children_hashes()).pop())]
                    node.replace_with(Node(Algebra.other_op(node.value),
                                       children=[common_node, Node(node.value,
                                                                   children=[node for node in
                                                                             left_child.children + right_child.children
                                                                             if node != common_node])]))
                except IndexError:
                    pass
                # left_child.children.sort(key=lambda node: node._preorder_traversal())
                # right_child.children.sort(key=lambda node: node._preorder_traversal())
                #
                # for i in range(len(left_child.children)):
                #     # Optimization: == uses has which is expensive. save the hash from before.
                #     if left_child.children[i] == right_child.children[i]:
                #         common_node = copy.deepcopy(left_child.children[i])
                #         node.replace_with(Node(Algebra.other_op(node.value),
                #                                children=[common_node, Node(node.value,
                #                                                            children=[node for node in left_child.children + right_child.children
                #                                                                      if node != common_node])]))
        else:
            for child in node.children:
                Algebra.reduce_distributive(child)

    @staticmethod
    def reduce_de_morgan(node):
        if node.value == "~" and node.child.value in OP:
            node.replace_with(Node(Algebra.other_op(node.child.value),
                                   children=[node.unary_combined("~") for node in node.child.children]))
        else:
            for child in node.children:
                Algebra.reduce_de_morgan(child)

    @staticmethod
    def other_op(op):
        """Returns "." if given "+". Returns "+" if given "."."""
        return OP[OP.index(op) - 1]


class Parser:
    def __init__(self, string):
        Parser.is_valid_token_seq(string)
        self.tokens = string
        self.token_index = 0
        self.syntax_tree = self.parse_expr()

    @staticmethod
    def is_valid_token_seq(string):
        valid_tokens = CONST + OP + UNARY_OP + PAREN
        for index, char in enumerate(string):
            if char not in valid_tokens and not char.isalpha():
                raise ValueError("Illegal token: {} at index {}".format(char, index))

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
        while self.peek() in OP:
            current_expr = current_expr.binary_combined(operator=self.next(), other=self.parse_term())
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
            return self.parse_term().unary_combined(unary_op)

    def __str__(self):
        return self.__str__helper(self.syntax_tree)[1:-1]

    def __str__helper(self, node):
        children_strings = []
        if not node.is_terminal():
            for child in node.children:
                children_strings.append(self.__str__helper(child))
        else:
            return node.value
        if len(children_strings) == 1:  # unary op.
            return "(" + node.value + children_strings[0] + ")"
        elif len(children_strings) > 1:
            return "(" + node.value.join(children_strings) + ")"

    @staticmethod
    def print_infix(node):
        parser = Parser("0")
        parser.syntax_tree = copy.deepcopy(node)
        print(str(parser))



class Node:
    def __init__(self, value=None, children=None):
        self.value = value
        self.children = children

    @property
    def children(self):
        return self._children

    @children.setter
    def children(self, value):
        if value is None or value is []:
            self._children = []
        elif isinstance(value, Node):
            self._children = [value]
        elif isinstance(value, list) and all(isinstance(child, Node) for child in value):
            self._children = value
        else:
            raise ValueError("invalid value: " + str(value))

    @property
    def child(self):
        if len(self.children) == 1:
            return self.children[0]
        else:
            raise ValueError("self does not have exactly 1 child")

    @child.setter
    def child(self, value):
        if isinstance(value, Node) or (isinstance(value, list) and len(value) == 1 and isinstance(value[0], Node)):
            self.children = value
        else:
            raise ValueError("value is not a Node or value is not a list that contains exactly one Node")

    def is_terminal(self):
        return len(self.children) == 0

    def binary_combined(self, operator, other):
        # self.value, self.children = operator, [copy.deepcopy(self), other]
        return Node(operator, children=[self, other])

    def unary_combined(self, operator):
        # self.value, self.children = operator, copy.deepcopy(self)
        return Node(operator, children=self)

    def replace_with(self, other):
        self.value, self.children = other.value, copy.deepcopy(other.children)

    def children_values(self):
        return [child.value for child in self.children]

    def children_hashes(self):
        return [hash(child) for child in self.children]

    # def __eq__(self, other):
    #     self.canonicalize()
    #     other.canonicalize()
    #     return self._preorder_traversal() == other._preorder_traversal()

    def __eq__(self, other):
        return hash(self) == hash(other)

    def canonicalize(self):
        """Recursively reorder the children in the node such that all other nodes
        which are equivalent to it will have the same canonical representation after reordering."""
        if not self.is_terminal():
            if all(child.is_terminal() for child in self.children):
                self.children.sort(key=lambda child: child.value)
            else:
                for child in self.children:
                    child.canonicalize()
            self.children.sort(key=lambda child: child.value + "".join(child.children_values()))

    def __str__(self):
        return self.__str__helper(indent=0).strip("\n")
        # vertical_str = Node.__str__helper(self, indent=0)
        # longest_line_len = max(len(line) for line in vertical_str.splitlines())
        # vertical_str = [line.ljust(longest_line_len) for line in vertical_str.splitlines()]
        # horizontal_lines = zip(*[list(line) for line in vertical_str])
        # print("\n".join("   ".join(line).strip("\n") for line in horizontal_lines))
        # exit()
        # return "\n".join(itertools.chain(*zip(*[list(line) for line in vertical_str])))

    def __str__helper(self, indent):
        output = "  " * indent + str(self.value) + "\n"
        if self.is_terminal():
            return output
        for child in self.children:
            output += Node.__str__helper(child, indent + 1)
        return output
        # output = ""
        # if len(self.children) >= 1:
        #     output += self.children[0].__str__helper(indent + 1)
        # output += " " * indent + str(self.value) + "\n"
        # for child in self.children[1:]:
        #     output += child.__str__helper(indent + 1)
        # return output

    def __hash__(self):
        self.canonicalize()
        return hash(self.preorder_traversal())

    def preorder_traversal(self):
        if self.is_terminal():
            return self.value
        else:
            return self.value + "".join(child.preorder_traversal() for child in self.children)


def main():
    pass


if __name__ == "__main__":
    main()
