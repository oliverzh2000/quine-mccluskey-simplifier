import itertools
from random import Random

from utils import BooleanFunction, Parser


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

        # # debuggin.
        # minterms.remove("0011")
        # minterms.remove("0100")
        # prime_implicants = ["0--0", "-1-0", "001-", "010-", "-011", "1-11", "111-"]

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
                    print("penisasdlkfja;lsdkjf;alskdjfa;lsdkjfa;lskdjflksdj")
                    new_essential_prime_implicants.update(pit.prime_implicants[0])
                    pit.remove_rows([0])
                essential_prime_implicants.update(QM.elim_essential_cols(pit))
                print("essential prime implicants:", essential_prime_implicants)
                # print(pit)
                print("dominating row removals:", QM.elim_dominating_rows(pit))
                # print(pit)
                print("dominated col removals:", QM.elim_dominated_cols(pit))
                # print(pit)
                if pit.n_rows == 0 or pit.n_cols == 0:
                    break
            except IndexError:
                break
        return essential_prime_implicants

    def simplify(self, verbose=False):
        if verbose:
            print("minterms:", self.bool_fn.minterm_bitstrings)
            print("prime implicants:", self.prime_implicants())
        if self.bool_fn.arity > 0:
            essential_prime_implicants = self.essential_prime_implicants(verbose)
            if essential_prime_implicants:
                return " + ".join(self.bool_fn.implicant_as_product(implicant) for implicant in essential_prime_implicants)
            return "0"
        return self.bool_fn.evaluate(var_values="")

    @staticmethod
    def elim_essential_cols(pit):
        # essential prime implicants.
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
        """Returns True if strings x and y are different in only one char position"""
        if len(x) != len(y):
            return False
        n_differences = 0
        for char_x, char_y in zip(x, y):
            if char_x != char_y:
                n_differences += 1
            if n_differences > 1:
                return False
        return n_differences == 1

    @staticmethod
    def first_diff_replaced_with_dash(x, y):
        """Return the result of replacing the first differnece between x and y with '-'"""
        for i in range(len(x)):
            if x[i] != y[i]:
                x_char_list = list(x)
                x_char_list[i] = "-"
                return "".join(x_char_list)

    @staticmethod
    def order_by_dominance(x, y):
        """
        Return bool lists x and y as (dominating, dominated) if there is a dominance relationship.
        Otherwise return None. A list of bool is said to dominate another iff it is True for at least
        all the corresponding elements in the other list. If x and y dominate each other, x and y
        will be returned in an arbitrary order."""
        if all((not y_element) or x_element for x_element, y_element in zip(x, y)):
            return x, y
        elif all((not x_element) or y_element for x_element, y_element in zip(x, y)):
            return y, x


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

    def col(self, col):
        # return self.prime_implicants[col], [row[col] for row in self.prime_implicant_table]
        return [row[col] for row in self.prime_implicant_table]

    def row(self, row):
        # return self.minterms[row], self.prime_implicant_table[row]
        return self.prime_implicant_table[row]

    def remove_cols(self, cols):
        for col in reversed(sorted(cols)):
            for row in self.prime_implicant_table:
                row.pop(col)
            self.prime_implicants.pop(col)

    def remove_rows(self, rows):
        for row in reversed(sorted(rows)):
            self.prime_implicant_table.pop(row)
            self.minterms.pop(row)

    def __str__(self):
        col_width = len(self.prime_implicants[0]) + 1
        rows = []
        rows.append("".join(prime_implicant.ljust(col_width) for prime_implicant in ["", ""] + self.prime_implicants))
        for i in range(self.n_rows):
            minterm = self.minterms[i]
            bool_values = self.row(i)
            rows.append(str(int(minterm, 2)).ljust(col_width) +
                        minterm.ljust(col_width) + "".join("|" +
                                                           ("1" if val else "").ljust(col_width - 1, "_") for val in
                                                           bool_values))
        return "\n".join(rows)
        # for row in self.prime_implicant_table:
        #     row_copy = [str(x) for x in row]
        #     row_copy = ["1" if x == "True" else x for x in row_copy]
        #     row_copy = ["" if x == "False" else x for x in row_copy]
        #     rows.append("".join((x.ljust(7) for x in row_copy)))
        # return "\n".join(rows)

    @staticmethod
    def matches(x, y):
        """Returns True if all non '-' chars in x and y are equal."""
        for char_x, char_y in zip(x, y):
            if not "-" in (char_x, char_y):
                if char_x != char_y:
                    return False
        return True


def main():
    # quine_mccluskey = QM("(b.~d)+(~a.b.~c)+(~a.~b.c)+(a.c.d)")
    quine_mccluskey = QM("~((~A.~B) + (~A.~C))")
    print("simplified:", quine_mccluskey.simplify(verbose=True))
    # pit = PrimeImplicantTable(minterms=['0010', '0101', '0110', '1011', '1100', '1110', '1111'],
    #                           prime_implicants=["0--0", "-1-0", "001-", "010-", "-011", "1-11", "111-"])
    # print(pit)


if __name__ == "__main__":
    main()
