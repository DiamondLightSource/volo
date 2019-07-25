import numpy
from scipy.optimize import least_squares


class Variables(object):
    def __init__(fields, indices, values):
        if not(len(fields) == len(indices) == len(values)):
            raise IndexError("Length mismatch: Lists of fields({0}), "
                             "indices({1}), and values({2}) must be the same "
                             "length.".format(len(fields), len(indices),
                                              len(values)))
        self.fields = fields
        self.indices = indices
        self.initial_values = values

class Constraints(object):
    def __init__(lattice, weights, refpts, constraints):
        self.lattice = lattice
        self.weightings = [
            weights['tune_x'], weights['tune_y'],
            weights['chrom_x'], weights['chrom_y'],
            weights['alpha_x'], weights['alpha_y'],
            weights['beta_x'], weights['beta_y'],
            weights['mu_x'], weights['mu_y'],
            weights['x'], weights['px'], weights['y'], weights['py'],
            weights['dispersion'], weights['gamma']
        ]
        self.refpts = refpts
        self.desired_constraints = constraints

    def calc_lindata():
        return at.linopt(self.lattice, refpts=self.refpts, get_chrom=True,
                         coupled=False)

    def convert_lindata(lindata):
        """Order : [tune_x, tune_y, chrom_x, chrom_y, alpha_x, alpha_y, beta_x,
                    beta_y, mu_x, mu_y, x, px, y, py, dispersion, gamma]
        """
        d = []  # How do we propgate to refpts, as merit output must be 1d?
        d.extend(lindata[1])  # tune_x and tune_y
        d.extend(lindata[2])  # chrom_x and chrom_y
        d.extend(lindata[3].alpha)  # alpha_x, alpha_y
        d.extend(lindata[3].beta)  # beta_x and beta_y
        d.extend(lindata[3].mu)  # mu_x and mu_y
        d.extend(lindata[3].closed_orbit[:4])  # x, px, y, and py
        d.extend(lindata[3].dispersion)  # dispersion ?is (4,)?
        d.extend(lindata[3].gamma)  # gamma
        return d

    def make_changes(values, variables):
        for v, f, i in zip(value, variables.fields, variables.indices):
            if isinstance(f, str):
                vars(self.lattice[i])[f] = v
            else:
                field = f[0]
                cell = f[1]
                vars(self.lattice[i])[field][cell] = v

    def merit_function(values, variables):
        self.make_changes(values, variables)
        constraints = self.convert_lindata(calc_lindata())
        diff = constraints - self.desired_constraints
        return diff * self.weightings


class Optimizer(object):
    def __init__():
        # create variables and constraints objects
        self.cons = Constraints()
        self.vars = Variables()

    def run(max_iters=None, verbosity=0):
        least_squares(self.cons.merit_function, self.vars.initial_values,
                      max_nfev=max_iters, verbose=verbosity, args=(self.vars))
        return self.cons.lattice
