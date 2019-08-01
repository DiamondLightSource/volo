import at
import numpy
from scipy.optimize import least_squares


class Variables(object):
    def __init__(self, fields, indices, values, lower_bounds=None,
                 upper_bounds=None):
        """Variable fields should either be a field name as a string e.g.
        'Length' or a field name(string) and a cell(int) e.g. ['PolynomB', 2].
        To change mutiple fields on the same element, multiple field index
        pairs must be passed.
        Values need to be in phys units!
        """
        if (len(fields) != len(indices)) or (len(fields) != len(values)):
            raise IndexError("Length mismatch: Lengths of fields ({0}), "
                             "indices ({1}), and values ({2}) are not equal."
                             .format(len(fields), len(indices), len(values)))
        self.fields = fields
        self.indices = indices
        self.initial_values = values
        if lower_bounds is not None:
            if len(indices) != len(lower_bounds):
                raise IndexError("Length mismatch: List of lower bounds must "
                                 "be the same length as indicies.")
        else:
            lower_bounds = -numpy.inf
        if upper_bounds is not None:
            if len(indices) != len(upper_bounds):
                raise IndexError("Length mismatch: List of upper bounds must "
                                 "be the same length as indicies.")
        else:
            upper_bounds = numpy.inf
        self.bounds = numpy.array([lower_bounds, upper_bounds])


class Constraints(object):
    def __init__(self, lattice, weights, constraints):
        """weights is a dictionary of format:
            {field: weight}
        constraints is a dictionary of format:
            {field: [[refpts], [desired_values]]}
        where refpts is an ordered ascending list of integers, and
        desired_values is a list of the corresponding goal values for that
        field at refpts.
        """
        # add a check that refpts and desired_values are the same length
        self.lattice = lattice
        self.weightings = weights
        self.desired_constraints = constraints
        self.refpts = set()
        for key in constraints.keys():
            self.refpts.update(constraints[key][0])
        self.refpts = list(self.refpts)
        """
        weights.get('tune_x', 0), weights.get('tune_y', 0),
        weights.get('chrom_x', 0), weights.get('chrom_y', 0),
        weights.get('alpha_x', 0), weights.get('alpha_y', 0),
        weights.get('beta_x', 0), weights.get('beta_y', 0),
        weights.get('mu_x', 0), weights.get('mu_y', 0),
        weights.get('x', 0), weights.get('px', 0),
        weights.get('y', 0), weights.get('py', 0),
        weights.get('dispersion', 0), weights.get('gamma', 0)
        self.desired_values = []
        self.desired_values.extend(constraints.get('tune_x', [[],[]])[1])
        self.desired_values.extend(constraints.get('tune_y', [[],[]])[1])
        self.desired_values.extend(constraints.get('chrom_x', [[],[]])[1])
        self.desired_values.extend(constraints.get('chrom_y', [[],[]])[1])
        self.desired_values.extend(constraints.get('alpha_x', [[],[]])[1])
        self.desired_values.extend(constraints.get('alpha_y', [[],[]])[1])
        self.desired_values.extend(constraints.get('beta_x', [[],[]])[1])
        self.desired_values.extend(constraints.get('beta_y', [[],[]])[1])
        self.desired_values.extend(constraints.get('mu_x', [[],[]])[1])
        self.desired_values.extend(constraints.get('mu_y', [[],[]])[1])
        self.desired_values.extend(constraints.get('x', [[],[]])[1])
        self.desired_values.extend(constraints.get('px',[[],[]])[1])
        self.desired_values.extend(constraints.get('y', [[],[]])[1])
        self.desired_values.extend(constraints.get('py',[[],[]])[1])
        self.desired_values.extend(constraints.get('dispersion', [[],[]])[1])
        self.desired_values.extend(constraints.get('gamma', [[],[]])[1])
        """

    def calc_lindata(self):
        return at.linopt(self.lattice, refpts=self.refpts, get_chrom=True,
                         coupled=False)

    def convert_lindata(self, lindata):
        """Order : [tune_x, tune_y, chrom_x, chrom_y, alpha_x, alpha_y, beta_x,
                    beta_y, mu_x, mu_y, x, px, y, py, dispersion, gamma]
        Emittance could possibly be added, though it would increase the
        calculation time dramatically.
        dispersion ?is (4,)?
        """
        data_map = {
            'tune_x':lindata[1][0], 'tune_y':lindata[1][1],
            'chrom_x':lindata[2][0], 'chrom_y':lindata[2][1],
            'alpha_x':lindata[3].alpha[:, 0], 'alpha_y':lindata[3].alpha[:, 1],
            'beta_x':lindata[3].beta[:, 0], 'beta_y':lindata[3].beta[:, 1],
            'mu_x':lindata[3].mu[:, 0], 'mu_y':lindata[3].mu[:, 1],
            'x':lindata[3].closed_orbit[:, 0],
            'px':lindata[3].closed_orbit[:, 1],
            'y':lindata[3].closed_orbit[:, 2],
            'py':lindata[3].closed_orbit[:, 3],
            'dispersion':lindata[3].dispersion, 'gamma':lindata[3].gamma
        }
        data = {}
        for key in self.desired_constraints.keys():
            if key in ['tune_x', 'tune_y', 'chrom_x', 'chrom_y']:
                d = [data_map[key]]
            else:
                d = [data_map[key][self.refpts.index(ref)] for ref
                     in self.desired_constraints[key][0]]
            data[key] = numpy.array(d)
        return data

    def make_changes(self, values, variables):
        for v, f, i in zip(values, variables.fields, variables.indices):
            if isinstance(f, str):
                vars(self.lattice[i])[f] = v
            else:
                field = f[0]
                cell = f[1]
                vars(self.lattice[i])[field][cell] = v

    def merit_function(self, values, variables):
        self.make_changes(values, variables)
        constraints = self.convert_lindata(self.calc_lindata())
        residuals = []
        for key in self.desired_constraints.keys():
            diff = constraints[key] - self.desired_constraints[key][1]
            residuals.extend(diff * self.weightings[key])
        return residuals


class Optimizer(object):
    def __init__(self, c, v):
        # create variables and constraints objects
        self.cons = c
        self.vars = v
        print("Number of variables: {0}\nNumber of constraints: {1}"
              .format(len(self.vars.initial_values),
                      len(list(self.cons.desired_constraints.values())[0])))

    def run(self, max_iters=None, verbosity=0, ftol=1e-8, xtol=1e-8,
            gtol=1e-8):
        # add return type option (lattice) or list of variable values
        ls = least_squares(self.cons.merit_function, self.vars.initial_values,
                           bounds=self.vars.bounds, ftol=ftol, xtol=xtol,
                           gtol=gtol, max_nfev=max_iters, verbose=verbosity,
                           args=([self.vars]))
        #print(ls.x)
        return self.cons.lattice
