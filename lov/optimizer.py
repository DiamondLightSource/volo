import at
import numpy
from scipy.optimize import least_squares


class Variables(object):
    def __init__(self, fields, indices, values, lower_bounds=None,
                 upper_bounds=None):
        """Variable fields should either be a field name as a string e.g.
        'Length', a field name(string) and a cell(int) e.g. ['PolynomB', 2],
        or a callable to be called in the format func(lattice, index, value)
        to make a custom change to the lattice. To change mutiple fields on
        the same element, multiple field index pairs must be passed.
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
    def __init__(self, lattice, constraints):
        """Constraints is a dictionary with format:
            {field: [[refpts], [desired_values], [weights]]}
        where refpts is an ordered ascending list of integers, desired_values
        is a list of the corresponding goal values for that field at refpts,
        and weights is a list of the corresponding weightings to be applied for
        that field at refpts.
        N.B. field may be a valid field for convert_lindata or a callable, if
        it is a callable it will be used as a custom difference function,
        i.e., instead of difference = alpha_x1 - alpha_x0 the function would
        be called as difference = func(lattice, constraint).
        N.B. for global fields refpts should not be given as they are ignored.
        N.B. if you are using a custom difference function that only returns a
        single value or a global field, then weights should be a length 1 list.
        """
        self.lattice = lattice
        self.refpts = set()
        for key in constraints.keys():
            refpts, desired_values, weights = constraints[key]
            if key in ['tune_x', 'tune_y', 'chrom_x', 'chrom_y']:
                if len(weights) > 1:
                    raise IndexError("Global fields ({0}) may only have one "
                                     "weighting value per field.".format(key))
            elif callable(key):
                pass
            else:
                if (len(weights)>1) and (len(refpts) != len(weights)):
                    raise IndexError("Field {0}: List of weights must be of "
                                     "length 1 or the same length as refpts."
                                     .format(key))
                elif len(refpts) != len(desired_values):
                    raise IndexError("Field {0}: List of desired_values must "
                                     "be the same length as refpts."
                                     .format(key))
            self.refpts.update(refpts)
        self.refpts = list(self.refpts)
        self.refpts.sort()
        self.desired_constraints = constraints

    def calc_lindata(self):
        self.lattice.radiation_off()
        return at.linopt(self.lattice, refpts=self.refpts, get_chrom=True,
                         coupled=False)

    def convert_lindata(self, lindata):
        """Fields : ['tune_x', 'tune_y', 'chrom_x', 'chrom_y', 'beta_x',
                     'beta_y', 'mu_x', 'mu_y', 'eta_x', 'eta_px', 'eta_y',
                     'eta_py', 'dispersion', 'gamma' 'alpha_x', 'alpha_y',
                     'x', 'px', 'y', 'py']
        Emittance could possibly be added, though it would increase the
        calculation time dramatically.
        """
        data_map = {
            'tune_x': lindata[1][0], 'tune_y': lindata[1][1],
            'chrom_x': lindata[2][0], 'chrom_y': lindata[2][1],
            'beta_x': lindata[3].beta[:, 0], 'beta_y': lindata[3].beta[:, 1],
            'mu_x': lindata[3].mu[:, 0], 'mu_y': lindata[3].mu[:, 1],
            'eta_x': lindata[3].dispersion, 'eta_px': lindata[3].dispersion,
            'eta_y': lindata[3].dispersion, 'eta_py': lindata[3].dispersion,
            'dispersion': lindata[3].dispersion, 'gamma': lindata[3].gamma,
            'alpha_x': lindata[3].alpha[:, 0],
            'alpha_y': lindata[3].alpha[:, 1],
            'x': lindata[3].closed_orbit[:, 0],
            'px': lindata[3].closed_orbit[:, 1],
            'y': lindata[3].closed_orbit[:, 2],
            'py': lindata[3].closed_orbit[:, 3]
        }
        data = {}
        for key in self.desired_constraints.keys():
            if callable(key):
                pass
            elif key in ['tune_x', 'tune_y', 'chrom_x', 'chrom_y']:
                data[key] = numpy.array([data_map[key]])  # global fields
            else:
                data[key] = numpy.array([data_map[key][self.refpts.index(ref)]
                                         for ref in
                                         self.desired_constraints[key][0]])
        return data

    def make_changes(self, values, variables):
        """Apply a change to an element. The values come from the optimizer,
        and the fields and element indexes come from the variables object. If
        the field is callable it will be called as func(lattice, index, value).
        """
        for v, f, i in zip(values, variables.fields, variables.indices):
            if callable(f):
                f(self.lattice, i, v)
            elif isinstance(f, str):
                vars(self.lattice[i])[f] = v
            else:
                field = f[0]
                cell = f[1]
                vars(self.lattice[i])[field][cell] = v

    def merit_function(self, values, variables, **kwargs):
        """Determine the difference between the constraints' current and goal
        values and then apply the weightings. If a custom difference function
        is used it will be called as func(lattice, constraint, kwargs), where
        lattice is the current version of the lattice, and constraint is the
        constraint for which the callable was passed as a field.
        """
        self.make_changes(values, variables)
        if not all([callable(key) for key in self.desired_constraints.keys()]):
            constraints = self.convert_lindata(self.calc_lindata())
        residuals = []
        for key in self.desired_constraints.keys():
            if callable(key):
                diff = key(self.lattice, self.desired_constraints[key],
                           **kwargs)
            else:
                diff = constraints[key] - self.desired_constraints[key][1]
            try:  # array
                residuals.extend(diff * self.desired_constraints[key][2])
            except TypeError:  # scalar
                residuals.append(diff * self.desired_constraints[key][2])
        return residuals


class Optimizer(object):
    def __init__(self, c, v):
        # create variables and constraints objects
        self.cons = c
        self.vars = v
        print("Number of variables: {0}\nNumber of constraints: {1}"
              .format(len(self.vars.initial_values),
                      len(list(self.cons.desired_constraints.values())[0])))

    def run(self, return_values=False, max_iters=None, verbosity=0, ftol=1e-8,
            xtol=1e-8, gtol=1e-8, **kwargs):
        # add return type option (lattice) or list of variable values
        ls = least_squares(self.cons.merit_function, self.vars.initial_values,
                           bounds=self.vars.bounds, ftol=ftol, xtol=xtol,
                           gtol=gtol, max_nfev=max_iters, verbose=verbosity,
                           args=([self.vars]), kwargs=kwargs)
        if verbosity > 0:
            data = self.cons.convert_lindata(self.cons.calc_lindata())
            for con, val in self.cons.desired_constraints.items():
                print("Constraint '{0}', goal: {1}, result {2}"
                      .format(con, val[1], data[con]))
        if return_values is True:
            return ls.x
        else:
            return self.cons.lattice
