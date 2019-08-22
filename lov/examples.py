import at
import numpy
import atip.ease as e
import optimizer as o


# Matching tunes using two quadrupole families:
def example1():
    lattice = at.load_tracy('../atip/atip/rings/for_Tobyn.lat')
    for index, elem in enumerate(lattice):
        elem.Index = index
    qf1s = lattice.get_elements('qf1')
    qd2s = lattice.get_elements('qd2')
    indices = [qf1s[0].Index, qd2s[0].Index]
    vals = [qf1s[0].PolynomB[1], qd2s[0].PolynomB[1]]

    def edit_qf1s(ring, index, value):
        for elem in ring.get_elements('qf1'):
            elem.PolynomB[1] = value

    def edit_qd2s(ring, index, value):
        for elem in ring.get_elements('qd2'):
            elem.PolynomB[1] = value

    # Initial tunes are [0.44751328688229897, 0.5254100397314794]
    variables = o.Variables([edit_qf1s, edit_qd2s], indices, vals)
    constraints = o.Constraints(lattice, {'tune_x': [[], [0.36], [2]],
                                          'tune_y': [[], [0.64], [1]]})
    opt = o.Optimizer(constraints, variables)
    lat = opt.run(verbosity=1, gtol=None)

    # N.B. we can also be clever; beacuse index is not used by our custom
    # family editing function we can do the following:
    def edit_family_b1(ring, family, value):
        for elem in ring.get_elements(family):
            elem.PolynomB[1] = value

    variables = o.Variables([edit_family_b1, edit_family_b1],
                            ['qf1', 'qd2'], vals)
    constraints = o.Constraints(lattice, {'tune_x': [[], [0.36], [2]],
                                          'tune_y': [[], [0.64], [1]]})
    optimizer = o.Optimizer(constraints, variables)
    return opt.run(verbosity=1, gtol=None)

# Minimising the beta function at two given points:
def example2():
    lattice = at.load_tracy('../atip/atip/rings/for_Tobyn.lat')
    qd2s = lattice.get_elements('qd2')
    qd5s = lattice.get_elements('qd5')
    qd3s = lattice.get_elements('qd3')
    qf1s = lattice.get_elements('qf1')
    qf6s = lattice.get_elements('qf6')
    vals = [qd2s[0].PolynomB[1], qd5s[0].PolynomB[1], qd3s[0].PolynomB[1],
            qf1s[0].PolynomB[1], qf6s[0].PolynomB[1]]

    # The generalisation from exapmle1 could be taken further e.g. using:
    def edit_family(ring, ffc, value):
        family, field, cell = ffc
        for elem in ring.get_elements(family):
            vars(elem)[field][cell] = value

    variables = o.Variables(
        [edit_family, edit_family, edit_family, edit_family, edit_family],
        [('qd2', 'PolynomB', 1), ('qd5', 'PolynomB', 1), ('qd3', 'PolynomB', 1),
         ('qf1', 'PolynomB', 1), ('qf6', 'PolynomB', 1)],
        vals
    )
    constraints = o.Constraints(lattice,
                                {'beta_x': [[141, 250], [0.4, 0.4], [1, 1]]})
    optimizer = o.Optimizer(constraints, variables)
    return optimizer.run(verbosity=1)

example1()
example2()
