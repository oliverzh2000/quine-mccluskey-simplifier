from unittest import TestCase

from quine_mccluskey import *
from utils import *


class TestParser(TestCase):
    def test_syntax_tree(self):
        self.assertEqual(Parser("A+A").syntax_tree, Node("+", [Node("A"), Node("A")]))
        self.assertEqual(Parser("~~A").syntax_tree, Node("~", [Node("~", [Node("A")])]))

class TestNode(TestCase):
    def test_is_terminal(self):
        self.assertFalse(Node("+", [Node(1), Node(0)]).is_terminal())
        self.assertTrue(Node(0).is_terminal())

    def test_binary_combined(self):
        node = Node("A").binary_combined("+", Node("B"))
        self.assertEqual(node.value, "+")
        self.assertEqual(node.children_values(), ["A", "B"])

    def test_unary_combined(self):
        node = Node("A").unary_combined("+")
        self.assertEqual(node.value, "+")
        self.assertEqual(node.child.value, "A")

    def test_replace_with(self):
        node = Node("D")
        node.replace_with(Node("A", [Node("B"), Node("C")]))
        self.assertEqual(node.value, "A")
        self.assertEqual(node.children_values(), ["B", "C"])

    def test___eq__basic(self):
        self.assertEqual(Node("A"), Node("A"))
        self.assertEqual(Node("A", [Node("B"), Node("C")]), Node("A", [Node("C"), Node("B")]))
        self.assertNotEqual(Node("A"), Node("B"))
        self.assertNotEqual(Node("A", [Node("B"), Node("C")]), Node("A", [Node("C"), Node("C")]))

    def test___eq__advanced(self):
        tree1 = Parser("((((0.A)+C).1)+A).(C+(E.D))").syntax_tree
        tree2 = Parser("(C+(D.E)).(A+((C+(A.0)).1))").syntax_tree
        self.assertEqual(tree1, tree2)

        tree1 = Parser("((((0.A)+C).1)+A).(C+(E.D))").syntax_tree
        tree2 = Parser("(C+(D.E)).(A+((C+(A.0)).0))").syntax_tree
        self.assertNotEqual(tree1, tree2)

    def test__hash__does_not_modify(self):
        node = Parser("(~B+(C.D)).(A+B)").syntax_tree
        node_copy = copy.deepcopy(node)
        node_copy.children_hashes()
        self.assertEqual(node, node_copy)

    def test__str__(self):
        pass


class TestAlgebra(TestCase):
    def test_reduce_not(self):
        node = Parser("~~A").syntax_tree
        Algebra.reduce_not(node)

        self.assertEqual(node, Parser("A").syntax_tree)
        node = Parser("B+(~~A.(C.~~1)").syntax_tree
        Algebra.reduce_not(node)
        self.assertEqual(node, Parser("B+(A.(C.1))").syntax_tree)

    def test_reduce_distributive(self):
        node = Parser("(A+B).(A+C)").syntax_tree
        Algebra.reduce_distributive(node)
        self.assertEqual(node, Parser("A+(B.C)").syntax_tree)

    #
    # def test_evaluate(self):
    #     node = Parser("A+((~B).C.1)").syntax_tree
    #     self.assertTrue(Algebra.evaluate(node, {"A": True, "B": False, "C": False}))
    #     self.assertFalse(Algebra.evaluate(node, {"A": False, "B": True, "C": False}))
    #
    # def test_truth_table(self):
    #     node = Parser("A+B+C+D").syntax_tree
    #     ordered_vars, truth_values = Algebra.truth_table(node)
    #     self.assertEqual(ordered_vars, ["A", "B", "C", "D"])
    #     self.assertEqual(truth_values, [True] * )

class TestBooleanFunction(TestCase):
    def test_minterms(self):
        boolean_function = BooleanFunction(Parser("A+B+C+D").syntax_tree)
        self.assertEqual(boolean_function.minterms, list(range(1, 16)))

        boolean_function = BooleanFunction(Parser("(A.~B)+(~A.B)").syntax_tree)
        self.assertEqual(boolean_function.minterms, [1, 2])

    def test_implicant_to_product(self):
        boolean_function = BooleanFunction(Parser("A+B+C+D").syntax_tree)
        self.assertEqual(boolean_function.implicant_as_product("0110"), "~A.B.C.~D")


class TestQM(TestCase):
    def test_prime_implicants(self):
        quine_mccluskey = QM("(b.~d)+(~a.b.~c)+(~a.~b.c)+(a.c.d)")
        quine_mccluskey.bool_fn.minterms.append(0)  # don't care term.
        self.assertEqual(quine_mccluskey.prime_implicants(), {'-1-0', '-011', '0--0', '010-', '1-11', '111-', '001-'})

    def test_first_diff_replaced_by_dash(self):
        self.assertEqual(QM.first_diff_replaced_with_dash("111-", "011-"), "-11-")

    def test_differs_by_one_char(self):
        self.assertTrue(QM.differs_by_one_char("1010", "0010"))
        self.assertFalse(QM.differs_by_one_char("1011", "0010"))
        self.assertFalse(QM.differs_by_one_char("11100", "101001"))

    def test_order_by_dominance(self):
        x = [True, False, True, True, True]
        y = [True, False, False, False, False]
        self.assertEqual(QM.order_by_dominance(x, y), (x, y))

        x = [True, False, True, False, False]
        y = [True, True, True, True, False]
        self.assertEqual(QM.order_by_dominance(x, y), (y, x))

        x = [True, False]
        y = [False, True]
        self.assertEqual(QM.order_by_dominance(x, y), None)

class TestPrimeImplicantTable(TestCase):
    def test_str(self):
        string = """          0--0 -1-0 001- 010- -011 1-11 111- 
2    0010 |1___|____|1___|____|____|____|____
5    0101 |____|____|____|1___|____|____|____
6    0110 |1___|1___|____|____|____|____|____
11   1011 |____|____|____|____|1___|1___|____
12   1100 |____|1___|____|____|____|____|____
14   1110 |____|1___|____|____|____|____|1___
15   1111 |____|____|____|____|____|1___|1___"""
        self.assertEqual(str(PrimeImplicantTable(['0010', '0101', '0110', '1011', '1100', '1110', '1111'],
                              ["0--0", "-1-0", "001-", "010-", "-011", "1-11", "111-"])), string)
    def test_rows_cols(self):
        pit = PrimeImplicantTable(['0010', '0101', '0110', '1011', '1100', '1110', '1111'],
                            ["0--0", "-1-0", "001-", "010-", "-011", "1-11", "111-"])
        self.assertEqual(pit.row(2), [True, True, False, False, False, False, False])
        self.assertEqual(pit.col(0), [True, False, True, False, False, False, False])

        pit.remove_cols([5, 0, 3])
        pit.remove_rows([5, 0, 3])
        self.assertEqual(str(pit), """          -1-0 001- -011 111- 
5    0101 |____|____|____|____
6    0110 |1___|____|____|____
12   1100 |1___|____|____|____
15   1111 |____|____|____|1___""")


    def test_matches(self):
        self.assertTrue(PrimeImplicantTable.matches("1001", "1--1"))
        self.assertTrue(PrimeImplicantTable.matches("1100", "1-00"))
        self.assertTrue(PrimeImplicantTable.matches("1000", "1-00"))
        self.assertTrue(PrimeImplicantTable.matches("1110", "1--0"))

        self.assertFalse(PrimeImplicantTable.matches("1000", "0-00"))
        self.assertFalse(PrimeImplicantTable.matches("1000", "0--1"))
