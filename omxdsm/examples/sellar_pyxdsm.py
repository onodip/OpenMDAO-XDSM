"""
Creates on output of the Sellar problem using pyXDSM.
"""
import numpy as np
import openmdao.api as om
from openmdao.test_suite.components.sellar import SellarNoDerivatives

from omxdsm import write_xdsm

if __name__ == '__main__':
    prob = om.Problem()
    prob.model = model = SellarNoDerivatives()
    model.add_design_var('z', lower=np.array([-10.0, 0.0]),
                         upper=np.array([10.0, 10.0]), indices=np.arange(2, dtype=int))
    model.add_design_var('x', lower=0.0, upper=10.0)
    model.add_objective('obj')
    model.add_constraint('con1', equals=np.zeros(1))
    model.add_constraint('con2', upper=0.0)

    prob.setup()
    prob.final_setup()

    # Write output. PDF will only be created, if pdflatex is installed
    write_xdsm(prob, filename='sellar_pyxdsm', out_format='pdf', show_browser=True,
               quiet=False, output_side='left', include_indepvarcomps=False, class_names=False)
