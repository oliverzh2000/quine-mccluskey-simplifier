import copy

CONST = ("1", "0")
OP = ("+", ".")
UNARY_OP = ("~",)
PAREN = ("(", ")")


class BooleanFunction:
    def __init__(self, tree):
        self.tree = tree
        self.ordered_unique_vars = self.ordered_unique_vars()
        self.arity = len(self.ordered_unique_vars)
        # Minterms are the product terms from the sum of products (SoP) representation of the boolean function.
        # Each minterm dictates exactly one possible combination of arguments to the function that result in True.
        self.minterms = self.minterms()

    @property
    def minterm_bitstrings(self):
        return [self.product_as_bitstring(minterm) for minterm in self.minterms]

    def evaluate(self, var_values):
        return self._evaluate_helper(self.tree, dict(zip(self.ordered_unique_vars,
                                                         [True if value == "1" else False for value in var_values])))

    @staticmethod
    def _evaluate_helper(node, var_values_mapping):
        if node.is_terminal():
            if node.value in CONST:
                return node.value == "1"
            elif node.value in var_values_mapping:
                return var_values_mapping[node.value]
            else:
                raise ValueError("Invalid terminal value: " + str(node.value))
        elif node.value == "+":
            return any(BooleanFunction._evaluate_helper(child, var_values_mapping) for child in node.children)
        elif node.value == ".":
            return all(BooleanFunction._evaluate_helper(child, var_values_mapping) for child in node.children)
        elif node.value == "~":
            return not BooleanFunction._evaluate_helper(node.child, var_values_mapping)
        else:
            raise ValueError("Invalid node value: " + str(node.value))

    def minterms(self):
        minterms = []
        if self.arity == 0:
            return []
        for i in range(2 ** self.arity):
            if self.evaluate(self.product_as_bitstring(i)):
                minterms.append(i)
        return minterms

    def product_as_bitstring(self, minterm):
        """example: "A.~B.C" -> "101"."""
        return bin(minterm)[2:].rjust(self.arity, "0")

    def bitstring_as_product(self, implicant):
        """example: "0110" -> "~A.B.C.~D."""
        var_states = []
        if self.arity == implicant.count("-"):
            return "1"
        for state, var in zip(implicant, self.ordered_unique_vars):
            if state == "0":
                var_states.append("~" + var)
            elif state == "1":
                var_states.append(var)
        return ".".join(var_states)

    def ordered_unique_vars(self):
        return sorted(filter(lambda char: char.isalpha(), set(self.tree.preorder_traversal())))


# Reduction of boolean function using some algebraic properties.
# Does not work well, because there is far too much variation in all the
# possible boolean functions for a simplistic recursive tree pattern matching
# algorithm to handle.
class Algebra:
    @staticmethod
    def reduce_not(node):
        """Reduce double negatives of the form "~~A" -> "A"."""
        if not node.is_terminal():
            if node.value == "~" and node.child.value == "~":
                node.replace_with(node.child.child)
            else:
                for child in node.children:
                    Algebra.reduce_not(child)

    @staticmethod
    def reduce_distributive(node):
        """Changes trees of the form "(A+B).C" to "(A.C)+(B.C)" and "(A.B)+C" to "(A+C).(B+C)"
        and vice versa."""
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
        """Changes trees of the form "~(A+B)" to "~A.~B" and "~(A.B)" to "~A+~B""
        and vice versa."""
        if node.value == "~" and node.child.value in OP:
            node.replace_with(Node(Algebra.other_op(node.child.value),
                                   children=[node.unary_combined("~") for node in node.child.children]))
        else:
            for child in node.children:
                Algebra.reduce_de_morgan(child)

    @staticmethod
    def other_op(op):
        """Return "." if given "+". Otherwise return "+" if given "."."""
        return OP[OP.index(op) - 1]


class Parser:
    def __init__(self, string):
        string = string.replace(" ", "")
        Parser.validate(string)
        self.tokens = string
        self.token_index = 0
        self.syntax_tree = self.parse_expr()

    @staticmethod
    def validate(string):
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
        """expr := term (op term)*."""
        current_expr = self.parse_term()
        while self.peek() in OP:
            current_expr = current_expr.binary_combined(operator=self.next(), other=self.parse_term())
        return current_expr

    def parse_term(self):
        """term := '1' | '0' | [a-zA-Z] | '(' expr ')' | unary_op term."""
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
        elif len(children_strings) > 1:  # binary op.
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
        return Node(operator, children=[self, other])

    def unary_combined(self, operator):
        return Node(operator, children=self)

    def replace_with(self, other):
        self.value, self.children = other.value, copy.deepcopy(other.children)

    def children_values(self):
        return [child.value for child in self.children]

    def children_hashes(self):
        return [hash(child) for child in self.children]

    def __eq__(self, other):
        """Return True if self and other have the same value and represent the
        same tree structure (order of children is ignored)."""
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

    def __str__helper(self, indent):
        output = "  " * indent + str(self.value) + "\n"
        if self.is_terminal():
            return output
        for child in self.children:
            output += Node.__str__helper(child, indent + 1)
        return output

    def __hash__(self):
        self.canonicalize()
        return hash(self.preorder_traversal())

    def preorder_traversal(self):
        if self.is_terminal():
            return self.value
        else:
            return self.value + "".join(child.preorder_traversal() for child in self.children)


class PrimeImplicantTable:
    def __init__(self, minterms, prime_implicants):
        self.minterms = list(minterms)
        self.prime_implicants = list(prime_implicants)
        self.prime_implicant_table = [
            [self.matches(minterm, prime_implicant) for prime_implicant in self.prime_implicants]
            for minterm in minterms]

    @property
    def n_rows(self):
        return len(self.minterms)

    @property
    def n_cols(self):
        return len(self.prime_implicants)

    def col(self, index):
        return [row[index] for row in self.prime_implicant_table]

    def row(self, index):
        return self.prime_implicant_table[index]

    def remove_cols(self, indices):
        """Remove the columns and corresponding prime implicants at the indices specified by indices."""
        for col in reversed(sorted(indices)):
            for row in self.prime_implicant_table:
                row.pop(col)
            self.prime_implicants.pop(col)

    def remove_rows(self, indices):
        """Remove the rows and corresponding minterms at the indices specified by indices."""
        for row in reversed(sorted(indices)):
            self.prime_implicant_table.pop(row)
            self.minterms.pop(row)

    def __str__(self):
        col_width = len(self.prime_implicants[0]) + 1
        rows = ["".join(prime_implicant.ljust(col_width) for prime_implicant in ["", ""] + self.prime_implicants)]
        for i in range(self.n_rows):
            minterm = self.minterms[i]
            bool_values = self.row(i)
            rows.append(str(int(minterm, 2)).ljust(col_width) +
                        minterm.ljust(col_width) + "".join("|" +
                                                           ("1" if val else "").ljust(col_width - 1, "_") for val in
                                                           bool_values))
        return "\n".join(rows)

    @staticmethod
    def matches(x, y):
        """Returns True if all non '-' chars in x and y are equal."""
        for char_x, char_y in zip(x, y):
            if not "-" in (char_x, char_y) and char_x != char_y:
                return False
        return True