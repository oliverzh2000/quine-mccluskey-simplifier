from unittest import TestCase

import copy

from algebra import Node, Parser, Algebra


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