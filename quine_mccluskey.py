import itertools

from utils import BooleanFunction, Parser, PrimeImplicantTable


class QM:
    def __init__(self, expr_string):
        self.expr_string = expr_string
        self.bool_fn = BooleanFunction(Parser(expr_string).syntax_tree)

    def prime_implicants(self):
        return QM.combine_minterms(self.bool_fn.minterm_bitstrings)

    @staticmethod
    def combine_minterms(minterms):
        combined = set()
        left_overs = set(minterms)
        sorted_minterms = sorted(minterms,
                                 key=lambda minterm: minterm.count("1"))
        # group the minterms based on the number of 1s in their binary representation.
        grouped_minterms = [list(group) for key, group in itertools.groupby(sorted_minterms,
                                                                            key=lambda minterm: minterm.count("1"))]
        for group, next_group in zip(grouped_minterms, grouped_minterms[1:]):
            for minterm in group:
                for next_minterm in next_group:
                    if QM.differs_by_one_char(minterm, next_minterm):
                        left_overs.discard(minterm)
                        left_overs.discard(next_minterm)
                        combined.add(QM.first_diff_replaced_with_dash(minterm, next_minterm))
        if combined:
            # keep combining until there is nothing left to combine.
            return left_overs.union(QM.combine_minterms(combined))
        else:
            return left_overs

    def essential_prime_implicants(self, verbose):
        essential_prime_implicants = set()

        pit = PrimeImplicantTable(self.bool_fn.minterm_bitstrings, self.prime_implicants())

        for i in range(10000):
            try:
                if verbose:
                    print()
                    print("iteration", i)
                    print(pit)
                new_essential_prime_implicants = QM.elim_essential_cols(pit)
                dominating_row_removals = QM.elim_dominating_rows(pit)
                dominated_col_removals = QM.elim_dominated_cols(pit)
                if new_essential_prime_implicants.union(dominating_row_removals).union(dominated_col_removals):
                    essential_prime_implicants.update(new_essential_prime_implicants)
                else:
                    # Arbitrary designate one of the prime implicants as essential.
                    new_essential_prime_implicants.update(pit.prime_implicants[0])
                    pit.remove_rows([0])
                essential_prime_implicants.update(QM.elim_essential_cols(pit))
                if verbose:
                    print("essential prime implicants:", essential_prime_implicants)
                    print("dominating row removals:", QM.elim_dominating_rows(pit))
                    print("dominated col removals:", QM.elim_dominated_cols(pit))
                if pit.n_rows == 0 or pit.n_cols == 0:
                    break
            except IndexError:  # Because the prime implicant table is empty.
                break
        return essential_prime_implicants

    def simplify(self, verbose=False):
        if verbose:
            print("minterms:", self.bool_fn.minterm_bitstrings)
            print("prime implicants:", self.prime_implicants())
        if self.bool_fn.arity > 0:
            essential_prime_implicants = self.essential_prime_implicants(verbose)
            if essential_prime_implicants:
                return " + ".join(
                    self.bool_fn.bitstring_as_product(implicant) for implicant in essential_prime_implicants)
            return "0"
        return self.bool_fn.evaluate(var_values="")

    @staticmethod
    def elim_essential_cols(pit):
        """Remove and return the essential columns.
        (i.e. the prime implicants that cover minterms no other prime implicant covers."""
        essential_pis = set()
        row_removals = set()
        col_removals = set()
        for row_index in range(pit.n_rows):
            row = pit.row(row_index)
            if row.count(True) == 1:
                col_index = row.index(True)
                essential_pis.add(pit.prime_implicants[col_index])
                col_removals.add(col_index)
        for row_index in range(pit.n_rows):
            row = pit.row(row_index)
            for col_index in col_removals:
                if row[col_index]:
                    row_removals.add(row_index)
                    break
        pit.remove_rows(row_removals)
        pit.remove_cols(col_removals)
        return essential_pis

    @staticmethod
    def elim_dominating_rows(pit):
        """Remove the dominating rows.
        (i.e. the minterms that are covered by more prime implicants than necessary."""
        row_removals = set()
        for row_index in range(pit.n_rows):
            for other_row_index in range(row_index + 1, pit.n_rows):
                dominance_rel = QM.order_by_dominance(pit.row(row_index), pit.row(other_row_index))
                if dominance_rel is not None:
                    dominating_row, dominated_row = dominance_rel
                    if dominating_row == pit.row(row_index):
                        row_removals.add(row_index)
                    else:
                        row_removals.add(other_row_index)
        pit.remove_rows(row_removals)
        return row_removals

    @staticmethod
    def elim_dominated_cols(pit):
        """Remove the dominated columns.
        (i.e. the prime implicants that are already covered by a more general prime implicant."""
        col_removals = set()
        for col_index in range(pit.n_cols):
            for other_col_index in range(col_index + 1, pit.n_cols):
                dominance_rel = QM.order_by_dominance(pit.col(col_index), pit.col(other_col_index))
                if dominance_rel is not None:
                    dominating_col, dominated_col = dominance_rel
                    if dominated_col == pit.col(col_index):
                        col_removals.add(col_index)
                    else:
                        col_removals.add(other_col_index)
        pit.remove_cols(col_removals)
        return col_removals

    @staticmethod
    def differs_by_one_char(x, y):
        """Returns True if strings x and y are different in exactly one char position."""
        if len(x) != len(y):
            return False
        n_differences = 0
        for char_x, char_y in zip(x, y):
            if char_x != char_y:
                n_differences += 1
        return n_differences == 1

    @staticmethod
    def first_diff_replaced_with_dash(x, y):
        """Return the result of replacing the first difference between strings x and y with '-'."""
        for i in range(len(x)):
            if x[i] != y[i]:
                x_chars = list(x)
                x_chars[i] = "-"
                return "".join(x_chars)

    @staticmethod
    def order_by_dominance(x, y):
        """
        Return bool lists x and y as (dominating, dominated) if there is a dominance relationship.
        Otherwise return None. x is said to dominate y iff x is True for at least
        all the corresponding elements in y. If x and y dominate each other, x and y
        will be returned in an arbitrary order."""
        if all((not y_element) or x_element for x_element, y_element in zip(x, y)):
            return x, y
        elif all((not x_element) or y_element for x_element, y_element in zip(x, y)):
            return y, x


def main():
#    quine_mccluskey = QM("~(~(A.~(A.B)).~(B.~(A.B)))")
    quine_mccluskey = QM("~(~(A+B).~(B+C))")
    print(quine_mccluskey.simplify(verbose=True))


if __name__ == "__main__":
    main()
