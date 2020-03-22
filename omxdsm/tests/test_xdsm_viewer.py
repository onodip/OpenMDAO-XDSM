import os
import unittest

import numpy as np
from numpy.distutils.exec_command import find_executable

import openmdao.api as om
from omxdsm import write_xdsm, write_html
from openmdao.test_suite.components.sellar import SellarNoDerivatives, SellarDis1, SellarDis2
from openmdao.test_suite.components.sellar_feature import SellarMDA
from openmdao.test_suite.scripts.circuit import Circuit
from openmdao.utils.assert_utils import assert_warning
from openmdao.utils.shell_proc import check_call
from openmdao.utils.testing_utils import use_tempdirs

try:
    from pyxdsm.XDSM import XDSM
except ImportError:
    XDSM = None

# Set DEBUG to True if you want to view the generated HTML and PDF output files.
DEBUG = False
# Suppress pyXDSM console output. Not suppressed in debug mode.
QUIET = not DEBUG
# If not in debug mode, tests will generate only the TeX files and not the PDFs, except for the
# PDF creation test, which is independent of this setting.
PYXDSM_OUT = 'pdf' if DEBUG else 'tex'
# Show in browser
SHOW = False

if DEBUG:
    use_tempdirs = lambda cls: cls


@unittest.skipUnless(XDSM, "The pyXDSM package is required.")
@use_tempdirs
class TestPyXDSMViewer(unittest.TestCase):

    def test_pyxdsm_output_sides(self):
        """Makes XDSM for the Sellar problem"""
        p = om.Problem()
        p.model = model = SellarNoDerivatives()
        model.add_design_var('z', lower=np.array([-10.0, 0.0]), upper=np.array([10.0, 10.0]),
                             indices=np.arange(2, dtype=int))
        model.add_design_var('x', lower=0.0, upper=10.0)
        model.add_objective('obj')
        model.add_constraint('con1', equals=np.zeros(1))
        model.add_constraint('con2', upper=0.0)

        p.setup()
        p.final_setup()

        # Write output (outputs on the left)
        filename = 'xdsm_outputs_on_the_left'
        write_xdsm(p, filename=filename, out_format=PYXDSM_OUT, show_browser=SHOW, quiet=QUIET, output_side='left')

        # Check if file was created
        self.assertTrue(os.path.isfile(filename + '.' + PYXDSM_OUT))

        filename = 'xdsm_outputs_on_the_right'
        # Write output (all outputs on the right)
        write_xdsm(p, filename=filename, out_format=PYXDSM_OUT, show_browser=SHOW, quiet=QUIET, output_side='right')

        # Check if file was created
        self.assertTrue(os.path.isfile(filename + '.' + PYXDSM_OUT))

        filename = 'xdsm_outputs_side_mixed'
        # Write output (outputs mixed)
        write_xdsm(p, filename=filename, out_format=PYXDSM_OUT, show_browser=SHOW, quiet=QUIET,
                   output_side={'optimization': 'left', 'default': 'right'})

        # Check if file was created
        self.assertTrue(os.path.isfile(filename + '.' + PYXDSM_OUT))

    def test_pyxdsm_case_reading(self):
        """
        Writes a recorder file, and the XDSM writer makes the diagram based on the SQL file
        and not the Problem instance.
        """
        import openmdao.api as om

        filename = 'xdsm_from_sql'
        case_recording_filename = filename + '.sql'

        p = om.Problem()
        p.model = model = SellarNoDerivatives()
        model.add_design_var('z', lower=np.array([-10.0, 0.0]),
                             upper=np.array([10.0, 10.0]), indices=np.arange(2, dtype=int))
        model.add_design_var('x', lower=0.0, upper=10.0)
        model.add_objective('obj')
        model.add_constraint('con1', equals=np.zeros(1))
        model.add_constraint('con2', upper=0.0)

        recorder = om.SqliteRecorder(case_recording_filename)
        p.driver.add_recorder(recorder)

        p.setup()
        p.final_setup()

        # Write output
        write_xdsm(case_recording_filename, filename=filename, out_format='tex', show_browser=False, quiet=QUIET)

        # Check if file was created
        self.assertTrue(os.path.isfile(case_recording_filename))
        self.assertTrue(os.path.isfile(filename + '.tex'))

        # Check that there are no errors when running from the command line with a recording.
        check_call('openmdao xdsm --no_browser {}'.format(case_recording_filename))

    def test_pyxdsm_sellar_no_recurse(self):
        """Makes XDSM for the Sellar problem, with no recursion."""

        filename = 'xdsm1'
        p = om.Problem()
        p.model = model = SellarNoDerivatives()
        model.add_design_var('z', lower=np.array([-10.0, 0.0]), upper=np.array([10.0, 10.0]),
                             indices=np.arange(2, dtype=int))
        model.add_design_var('x', lower=0.0, upper=10.0)
        model.add_objective('obj')
        model.add_constraint('con1', equals=np.zeros(1))
        model.add_constraint('con2', upper=0.0)

        p.setup()
        p.final_setup()

        # Write output
        write_xdsm(p, filename=filename, out_format=PYXDSM_OUT, show_browser=SHOW, recurse=False, quiet=QUIET)

        # Check if file was created
        self.assertTrue(os.path.isfile(filename + '.' + PYXDSM_OUT))

    def test_pyxdsm_pdf(self):
        """
        Makes an XDSM of the Sphere test case. It also adds a design variable, constraint and
        objective.
        """

        class Square(om.ExplicitComponent):

            def setup(self):
                self.add_input('x', np.array([1.5, 1.5]))
                self.add_output('f', 0.0)
                self.declare_partials('f', 'x', method='fd', form='central', step=1e-4)

            def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
                x = inputs['x']
                outputs['f'] = sum(x ** 2)

        x0 = np.array([1.2, 1.5])
        filename = 'xdsm2'

        p = om.Problem()
        indeps = p.model.add_subsystem('indeps', om.IndepVarComp(), promotes=['*'])
        indeps.add_output('x', list(x0))

        p.model.add_subsystem('sphere', Square(), promotes=['*'])
        p.model.add_subsystem('con', om.ExecComp('c=sum(x)', x=np.ones(2)), promotes=['*'])
        p.driver = om.ScipyOptimizeDriver()
        p.model.add_design_var('x')
        p.model.add_objective('f')
        p.model.add_constraint('c', lower=1.0)

        p.setup()
        p.final_setup()

        # requesting 'pdf', but if 'pdflatex' is not found we will only get 'tex'
        pdflatex = find_executable('pdflatex')

        # Write output
        write_xdsm(p, filename=filename, out_format='pdf', show_browser=SHOW, quiet=QUIET)

        # Check if file was created
        self.assertTrue(os.path.isfile(filename + '.tex'))
        # Check if PDF was created (only if pdflatex is installed)
        self.assertTrue(not pdflatex or os.path.isfile(filename + '.pdf'))

    def test_pyxdsm_tikz_content(self):
        # Check if TiKZ file was created.
        # Compare the content of the sample below and the newly created TiKZ file.
        # The texts are cleaned up before comparison from whitespaces, line ends and comments
        # Despite this different versions of pyxdsm *might* produce different outputs. If the test fails for you,
        # it might be that the program still produces the correct output.
        # The ordering of some lines might be different at different runs, but the test should work regardless
        # of these changes.
        # The sample text should be replaced if changes in the formatting or in the test problem are made.

        sample_tikz_txt = r"""

            %%% Preamble Requirements %%%
            % \usepackage{geometry}
            % \usepackage{amsfonts}
            % \usepackage{amsmath}
            % \usepackage{amssymb}
            % \usepackage{tikz}

            % Optional packages such as sfmath set through python interface
            % \usepackage{sfmath}

            % \usetikzlibrary{arrows,chains,positioning,scopes,shapes.geometric,shapes.misc,shadows}

            %%% End Preamble Requirements %%%

            \input{D:/Documents/GitHub/OpenMDAO-XDSM/venv_py/lib/site-packages/pyxdsm/diagram_styles}
            \begin{tikzpicture}

            \matrix[MatrixSetup]{
            %Row 0
            \node [Optimization] (Driver) {$\text{\text{0, 10 $ \rightarrow $ 1: Driver}}$};&
            &
            &
            &
            &
            &
            &
            \\
            %Row 1
            &
            \node [Function] (indeps) {$\begin{array}{c}\text{1: indeps} \\ \text{\textit{IndepVarComp}}\end{array}$};&
            &
            \node [DataInter] (indeps-cycle@d1) {$\begin{array}{c}x, z\end{array}$};&
            \node [DataInter] (indeps-cycle@d2) {$\begin{array}{c}z\end{array}$};&
            \node [DataInter] (indeps-obj@cmp) {$\begin{array}{c}x, z\end{array}$};&
            &
            \\
            %Row 2
            &
            &
            \node [MDA] (cycle@solver) {$\text{\text{2, 5 $ \rightarrow $ 3: NL: NLBGS}}$};&
            \node [DataInter] (cycle@solver-cycle@d1) {$\begin{array}{c}y2^{t}\end{array}$};&
            \node [DataInter] (cycle@solver-cycle@d2) {$\begin{array}{c}y1^{t}\end{array}$};&
            &
            &
            \\
            %Row 3
            &
            &
            \node [DataInter] (cycle@d1-cycle@solver) {$\begin{array}{c}y1\end{array}$};&
            \node [Function] (cycle@d1) {$\begin{array}{c}\text{3: d1} \\ \text{\textit{SellarDis1}}\end{array}$};&
            \node [DataInter] (cycle@d1-cycle@d2) {$\begin{array}{c}y1\end{array}$};&
            \node [DataInter] (cycle@d1-obj@cmp) {$\begin{array}{c}y1\end{array}$};&
            \node [DataInter] (cycle@d1-con@cmp1) {$\begin{array}{c}y1\end{array}$};&
            \\
            %Row 4
            &
            &
            \node [DataInter] (cycle@d2-cycle@solver) {$\begin{array}{c}y2\end{array}$};&
            \node [DataInter] (cycle@d2-cycle@d1) {$\begin{array}{c}y2\end{array}$};&
            \node [Function] (cycle@d2) {$\begin{array}{c}\text{4: d2} \\ \text{\textit{SellarDis2}}\end{array}$};&
            \node [DataInter] (cycle@d2-obj@cmp) {$\begin{array}{c}y2\end{array}$};&
            &
            \node [DataInter] (cycle@d2-con@cmp2) {$\begin{array}{c}y2\end{array}$};\\
            %Row 5
            &
            &
            &
            &
            &
            \node [Function] (obj@cmp) {$\begin{array}{c}\text{6: obj\_cmp} \\ \text{\textit{ExecComp}}\end{array}$};&
            &
            \\
            %Row 6
            &
            &
            &
            &
            &
            &
            \node [Function] (con@cmp1) {$\begin{array}{c}\text{7: con\_cmp1} \\ \text{\textit{ExecComp}}\end{array}$};&
            \\
            %Row 7
            &
            &
            &
            &
            &
            &
            &
            \node [Function] (con@cmp2) {$\begin{array}{c}\text{8: con\_cmp2} \\ \text{\textit{ExecComp}}\end{array}$};\\
            };

            % XDSM process chains
            { [start chain=process]
             \begin{pgfonlayer}{process} 
            \chainin (Driver);
            \chainin (indeps) [join=by ProcessHV];
            \chainin (cycle@solver) [join=by ProcessHV];
            \chainin (obj@cmp) [join=by ProcessHV];
            \chainin (con@cmp1) [join=by ProcessHV];
            \chainin (con@cmp2) [join=by ProcessHV];
            \chainin (Driver) [join=by ProcessHV];
            \end{pgfonlayer}
            }{ [start chain=process]
             \begin{pgfonlayer}{process} 
            \chainin (cycle@solver);
            \chainin (cycle@d1) [join=by ProcessHV];
            \chainin (cycle@d2) [join=by ProcessHV];
            \chainin (cycle@solver) [join=by ProcessHV];
            \end{pgfonlayer}
            }

            \begin{pgfonlayer}{data}
            \path
            % Horizontal edges
            (cycle@solver) edge [DataLine] (cycle@solver-cycle@d2)
            (cycle@d1) edge [DataLine] (cycle@d1-cycle@solver)
            (cycle@solver) edge [DataLine] (cycle@solver-cycle@d1)
            (cycle@d2) edge [DataLine] (cycle@d2-cycle@solver)
            (cycle@d1) edge [DataLine] (cycle@d1-obj@cmp)
            (cycle@d1) edge [DataLine] (cycle@d1-con@cmp1)
            (cycle@d1) edge [DataLine] (cycle@d1-cycle@d2)
            (cycle@d2) edge [DataLine] (cycle@d2-obj@cmp)
            (cycle@d2) edge [DataLine] (cycle@d2-con@cmp2)
            (cycle@d2) edge [DataLine] (cycle@d2-cycle@d1)
            (indeps) edge [DataLine] (indeps-cycle@d1)
            (indeps) edge [DataLine] (indeps-obj@cmp)
            (indeps) edge [DataLine] (indeps-cycle@d2)
            % Vertical edges
            (cycle@solver-cycle@d2) edge [DataLine] (cycle@d2)
            (cycle@d1-cycle@solver) edge [DataLine] (cycle@solver)
            (cycle@solver-cycle@d1) edge [DataLine] (cycle@d1)
            (cycle@d2-cycle@solver) edge [DataLine] (cycle@solver)
            (cycle@d1-obj@cmp) edge [DataLine] (obj@cmp)
            (cycle@d1-con@cmp1) edge [DataLine] (con@cmp1)
            (cycle@d1-cycle@d2) edge [DataLine] (cycle@d2)
            (cycle@d2-obj@cmp) edge [DataLine] (obj@cmp)
            (cycle@d2-con@cmp2) edge [DataLine] (con@cmp2)
            (cycle@d2-cycle@d1) edge [DataLine] (cycle@d1)
            (indeps-cycle@d1) edge [DataLine] (cycle@d1)
            (indeps-obj@cmp) edge [DataLine] (obj@cmp)
            (indeps-cycle@d2) edge [DataLine] (cycle@d2);
            \end{pgfonlayer}

            \end{tikzpicture}"""

        def filter_lines(lns):
            # Empty lines are excluded.
            # Leading and trailing whitespaces are removed
            # Comments are removed.
            return [ln.strip() for ln in lns if ln.strip() and not ln.strip().startswith('%')]

        filename = 'pyxdsm_mda_tikz'
        out_format = PYXDSM_OUT
        p = om.Problem(model=SellarMDA())
        p.setup()
        p.final_setup()

        # Write output
        write_xdsm(p, filename=filename, out_format=out_format, quiet=QUIET, show_browser=SHOW, include_solver=True)
        # Check if file was created
        tikz_file = filename + '.tikz'

        self.assertTrue(os.path.isfile(tikz_file))

        sample_lines = sample_tikz_txt.split('\n')
        sample_lines = filter_lines(sample_lines)

        with open(tikz_file, "r") as f:
            new_lines = filter_lines(f.readlines())

        no_match_sample = []  # Sample text
        no_match_new = []  # New text

        for new_line, sample_line in zip(new_lines, sample_lines):
            if new_line != sample_line:  # else everything is okay
                # This can be because of the different ordering of lines or because of an error.
                no_match_sample.append(new_line)
                no_match_new.append(sample_line)

        # Sort both sets of suspicious lines
        no_match_sample.sort()
        no_match_new.sort()

        for sample_line, new_line in zip(no_match_sample, no_match_new):
            # Now the lines should match, if only the ordering was different
            self.assertEqual(sample_line, new_line)

        # To be sure, check the length, otherwise a missing last line could get unnoticed because of using zip
        self.assertEqual(len(new_lines), len(sample_lines))

    def test_pyxdsm_identical_relative_names(self):
        class TimeComp(om.ExplicitComponent):

            def setup(self):
                self.add_input('t_initial', val=0.)
                self.add_input('t_duration', val=1.)
                self.add_output('time', shape=(2,))

            def compute(self, inputs, outputs):
                t_initial = inputs['t_initial']
                t_duration = inputs['t_duration']

                outputs['time'][0] = t_initial
                outputs['time'][1] = t_initial + t_duration

        class Phase(om.Group):

            def setup(self):
                super(Phase, self).setup()

                indep = om.IndepVarComp()
                for var in ['t_initial', 't_duration']:
                    indep.add_output(var, val=1.0)

                self.add_subsystem('time_extents', indep, promotes_outputs=['*'])

                time_comp = TimeComp()
                self.add_subsystem('time', time_comp)

                self.connect('t_initial', 'time.t_initial')
                self.connect('t_duration', 'time.t_duration')

                self.set_order(['time_extents', 'time'])

        p = om.Problem()
        p.driver = om.ScipyOptimizeDriver()
        orbit_phase = Phase()
        p.model.add_subsystem('orbit_phase', orbit_phase)

        systems_phase = Phase()
        p.model.add_subsystem('systems_phase', systems_phase)

        systems_phase = Phase()
        p.model.add_subsystem('extra_phase', systems_phase)
        p.model.add_design_var('orbit_phase.t_initial')
        p.model.add_design_var('orbit_phase.t_duration')
        p.model.add_objective('systems_phase.time.time')
        p.setup()

        p.run_model()

        # Test non unique local names
        filename = 'pyxdsm_identical_rel_names'
        write_xdsm(p, filename, out_format=PYXDSM_OUT, quiet=QUIET, show_browser=SHOW)
        self.assertTrue(os.path.isfile(filename + '.' + PYXDSM_OUT))

        # Check formatting

        # Max character box formatting
        filename = 'pyxdsm_cut_char'
        write_xdsm(p, filename, out_format=PYXDSM_OUT, quiet=QUIET, show_browser=SHOW, box_stacking='cut_chars',
                   box_width=15)
        self.assertTrue(os.path.isfile(filename + '.' + PYXDSM_OUT))

        # Cut characters box formatting
        filename = 'pyxdsm_max_chars'
        write_xdsm(p, filename, out_format=PYXDSM_OUT, quiet=True, show_browser=SHOW, box_stacking='max_chars',
                   box_width=15)
        self.assertTrue(os.path.isfile(filename + '.' + PYXDSM_OUT))

    def test_no_indepvarcomps(self):
        p = om.Problem()
        p.model = model = SellarNoDerivatives()
        model.add_design_var('z', lower=np.array([-10.0, 0.0]), upper=np.array([10.0, 10.0]),
                             indices=np.arange(2, dtype=int))
        # model.add_design_var('x', lower=0.0, upper=10.0)
        model.add_objective('obj')
        model.add_constraint('con1', equals=np.zeros(1))
        model.add_constraint('con2', upper=0.0)

        p.setup()
        p.final_setup()

        filename = 'pyxdsm_no_indepvarcomps'
        write_xdsm(p, filename=filename, out_format='pdf', show_browser=SHOW, quiet=True, include_indepvarcomps=False)
        self.assertTrue(os.path.isfile(filename + '.' + PYXDSM_OUT))

    def test_model_path_and_recursion(self):

        import openmdao.api as om

        p = om.Problem()
        model = p.model

        group = model.add_subsystem('G1', om.Group(), promotes=['*'])
        group2 = model.add_subsystem('G2', om.Group())
        group.add_subsystem('ground', om.IndepVarComp('V', 0., units='V'))
        group.add_subsystem('source', om.IndepVarComp('I', 0.1, units='A'))
        group2.add_subsystem('source2', om.IndepVarComp('I', 0.1, units='A'))
        group.add_subsystem('circuit', Circuit())

        group.connect('source.I', 'circuit.I_in')
        group.connect('ground.V', 'circuit.Vg')

        model.add_design_var('ground.V')
        model.add_design_var('source.I')
        model.add_objective('circuit.D1.I')

        p.setup()

        # set some initial guesses
        p['circuit.n1.V'] = 10.
        p['circuit.n2.V'] = 1.

        p.run_model()

        # No model path, no recursion
        write_xdsm(p, 'xdsm_circuit', out_format=PYXDSM_OUT, quiet=QUIET, show_browser=SHOW, recurse=False)
        self.assertTrue(os.path.isfile('xdsm_circuit.' + PYXDSM_OUT))

        # Model path given + recursion
        write_xdsm(p, 'xdsm_circuit2', out_format=PYXDSM_OUT, quiet=QUIET, show_browser=SHOW, recurse=True,
                   model_path='G2', include_external_outputs=False)
        self.assertTrue(os.path.isfile('xdsm_circuit2.' + PYXDSM_OUT))

        # Model path given + no recursion
        write_xdsm(p, 'xdsm_circuit3', out_format=PYXDSM_OUT, quiet=QUIET, show_browser=SHOW, recurse=False,
                   model_path='G1')
        self.assertTrue(os.path.isfile('xdsm_circuit3.' + PYXDSM_OUT))

        # Invalid model path, should raise error
        with self.assertRaises(ValueError):
            write_xdsm(p, 'xdsm_circuit4', out_format='tex', quiet=QUIET, show_browser=SHOW, recurse=False,
                       model_path='G3')

    def test_pyxdsm_solver(self):
        import openmdao.api as om

        out_format = PYXDSM_OUT
        p = om.Problem()
        p.model = model = SellarNoDerivatives()
        model.nonlinear_solver = om.NonlinearBlockGS()
        p.driver = om.ScipyOptimizeDriver()
        p.model.add_objective('obj')

        p.setup()
        p.run_model()

        filename = 'pyxdsm_solver'
        # Write output
        write_xdsm(p, filename=filename, out_format=out_format, quiet=QUIET, show_browser=SHOW, include_solver=True)
        # Check if file was created
        self.assertTrue(os.path.isfile(filename + '.' + out_format))

        filename = 'pyxdsm_solver2'
        # Write output
        write_xdsm(p, filename=filename, out_format=out_format, quiet=QUIET, show_browser=SHOW, include_solver=True,
                   recurse=False)
        # Check if file was created
        self.assertTrue(os.path.isfile(filename + '.' + out_format))

    def test_pyxdsm_mda(self):
        filename = 'pyxdsm_mda'
        out_format = PYXDSM_OUT
        p = om.Problem(model=SellarMDA())
        p.setup()
        p.final_setup()

        # Write output
        write_xdsm(p, filename=filename, out_format=out_format, quiet=QUIET, show_browser=SHOW, include_solver=True)
        # Check if file was created
        self.assertTrue(os.path.isfile(filename + '.' + out_format))

    def test_pyxdsm_mdf(self):
        filename = 'pyxdsm_mdf'
        out_format = PYXDSM_OUT
        p = om.Problem(model=SellarMDA())
        model = p.model
        p.driver = om.ScipyOptimizeDriver()

        model.add_design_var('z', lower=np.array([-10.0, 0.0]),
                             upper=np.array([10.0, 10.0]), indices=np.arange(2, dtype=int))
        model.add_design_var('x', lower=0.0, upper=10.0)
        model.add_objective('obj')
        model.add_constraint('con1', equals=np.zeros(1))
        model.add_constraint('con2', upper=0.0)

        p.setup()
        p.final_setup()

        # Write output
        write_xdsm(p, filename=filename, out_format=out_format, quiet=QUIET, show_browser=SHOW, include_solver=True)
        # Check if file was created
        self.assertTrue(os.path.isfile(filename + '.' + out_format))

    def test_parallel(self):
        import openmdao.api as om

        class SellarMDA(om.Group):
            """
            Group containing the Sellar MDA.
            """

            def setup(self):
                indeps = self.add_subsystem('indeps', om.IndepVarComp(), promotes=['*'])
                indeps.add_output('x', 1.0)
                indeps.add_output('z', np.array([5.0, 2.0]))
                cycle = self.add_subsystem('cycle', om.ParallelGroup(), promotes=['*'])
                cycle.add_subsystem('d1', SellarDis1(), promotes_inputs=['x', 'z', 'y2'], promotes_outputs=['y1'])
                cycle.add_subsystem('d2', SellarDis2(), promotes_inputs=['z', 'y1'], promotes_outputs=['y2'])

                # Nonlinear Block Gauss Seidel is a gradient free solver
                cycle.nonlinear_solver = om.NonlinearBlockGS()

                self.add_subsystem('obj_cmp', om.ExecComp('obj = x**2 + z[1] + y1 + exp(-y2)',
                                                          z=np.array([0.0, 0.0]), x=0.0),
                                   promotes=['x', 'z', 'y1', 'y2', 'obj'])

                self.add_subsystem('con_cmp1', om.ExecComp('con1 = 3.16 - y1'), promotes=['con1', 'y1'])
                self.add_subsystem('con_cmp2', om.ExecComp('con2 = y2 - 24.0'), promotes=['con2', 'y2'])

        filename = 'pyxdsm_parallel'
        out_format = PYXDSM_OUT
        p = om.Problem(model=SellarMDA())
        model = p.model
        p.driver = om.ScipyOptimizeDriver()

        model.add_design_var('z', lower=np.array([-10.0, 0.0]), upper=np.array([10.0, 10.0]),
                             indices=np.arange(2, dtype=int))
        model.add_design_var('x', lower=0.0, upper=10.0)
        model.add_objective('obj')
        model.add_constraint('con1', equals=np.zeros(1))
        model.add_constraint('con2', upper=0.0)

        p.setup()
        p.final_setup()

        # Write output
        write_xdsm(p, filename=filename, out_format=out_format, quiet=QUIET, show_browser=SHOW, show_parallel=True)
        # Check if file was created
        self.assertTrue(os.path.isfile(filename + '.' + out_format))

    def test_execcomp(self):
        filename = 'pyxdsm_execcomp'
        out_format = PYXDSM_OUT
        p = om.Problem()
        indeps = p.model.add_subsystem('indeps', om.IndepVarComp(), promotes=['*'])
        indeps.add_output('x')
        p.model.add_subsystem('C1', om.ExecComp(['y=2.0*x+1.'], x=2.0), promotes=['*'])
        p.driver = om.ScipyOptimizeDriver()
        p.model.add_design_var('x', lower=0.0, upper=10.0)
        p.model.add_objective('y')
        p.setup()

        # Conclude setup but don't run model.
        p.final_setup()

        write_xdsm(p, filename=filename, out_format=out_format, quiet=QUIET, show_browser=SHOW, show_parallel=True)
        # Check if file was created
        self.assertTrue(os.path.isfile(filename + '.' + out_format))

        # Including the expression from the ExecComp formatted in LaTeX
        write_xdsm(p, filename=filename + "2", out_format=out_format, quiet=QUIET, show_browser=SHOW,
                   show_parallel=True, equations=True)
        # Check if file was created
        self.assertTrue(os.path.isfile(filename + '.' + out_format))

    def test_doe(self):
        filename = 'pyxdsm_doe'
        out_format = PYXDSM_OUT
        p = om.Problem()
        indeps = p.model.add_subsystem('indeps', om.IndepVarComp(), promotes=['*'])
        indeps.add_output('x')
        p.model.add_subsystem('C1', om.ExecComp(['y=2.0*x+1.'], x=2.0), promotes=['*'])
        p.driver = om.DOEDriver()
        p.model.add_design_var('x', lower=0.0, upper=10.0)
        p.model.add_objective('y')
        p.setup()

        # Conclude setup but don't run model.
        p.final_setup()

        write_xdsm(p, filename=filename, out_format=out_format, quiet=QUIET, show_browser=SHOW, show_parallel=True)
        # Check if file was created
        self.assertTrue(os.path.isfile(filename + '.' + out_format))

    def test_meta_model(self):
        import openmdao.api as om
        from openmdao.components.tests.test_meta_model_structured_comp import SampleMap

        filename = 'pyxdsm_meta_model'
        out_format = PYXDSM_OUT
        model = om.Group()
        ivc = om.IndepVarComp()

        mapdata = SampleMap()

        params = mapdata.param_data
        x, y, z = params
        outs = mapdata.output_data
        z = outs[0]
        ivc.add_output('x', x['default'], units=x['units'])
        ivc.add_output('y', y['default'], units=y['units'])
        ivc.add_output('z', z['default'], units=z['units'])

        model.add_subsystem('des_vars', ivc, promotes=["*"])

        comp = om.MetaModelStructuredComp(method='slinear', extrapolate=True)

        for param in params:
            comp.add_input(param['name'], param['default'], param['values'])

        for out in outs:
            comp.add_output(out['name'], out['default'], out['values'])

        model.add_subsystem('comp', comp, promotes=["*"])
        p = om.Problem(model)
        p.setup()
        p.final_setup()

        write_xdsm(p, filename=filename, out_format=out_format, quiet=QUIET, show_browser=SHOW, show_parallel=True)
        # Check if file was created
        self.assertTrue(os.path.isfile(filename + '.' + out_format))


@use_tempdirs
class TestXDSMjsViewer(unittest.TestCase):

    def test_xdsmjs(self):
        """
        Makes XDSMjs input file for the Sellar problem.

        Data is in a separate JSON file.
        """

        filename = 'xdsmjs'  # this name is needed for XDSMjs
        p = om.Problem()
        p.model = model = SellarNoDerivatives()
        model.add_design_var('z', lower=np.array([-10.0, 0.0]), upper=np.array([10.0, 10.0]),
                             indices=np.arange(2, dtype=int))
        model.add_design_var('x', lower=0.0, upper=10.0)
        model.add_objective('obj')
        model.add_constraint('con1', equals=np.zeros(1))
        model.add_constraint('con2', upper=0.0)

        p.setup()
        p.final_setup()

        # Write output
        write_xdsm(p, filename=filename, out_format='html', subs=(), show_browser=SHOW, embed_data=False)

        # Check if file was created
        self.assertTrue(os.path.isfile(filename + '.json'))
        self.assertTrue(os.path.isfile(filename + '.html'))

    def test_xdsmjs_embed_data(self):
        """
        Makes XDSMjs HTML file for the Sellar problem.

        Data is embedded into the HTML file.
        """

        filename = 'xdsmjs_embedded'  # this name is needed for XDSMjs
        p = om.Problem()
        p.model = model = SellarNoDerivatives()
        model.add_design_var('z', lower=np.array([-10.0, 0.0]), upper=np.array([10.0, 10.0]),
                             indices=np.arange(2, dtype=int))
        model.add_design_var('x', lower=0.0, upper=10.0)
        model.add_objective('obj')
        model.add_constraint('con1', equals=np.zeros(1))
        model.add_constraint('con2', upper=0.0)

        p.setup()
        p.final_setup()

        # Write output
        write_xdsm(p, filename=filename, out_format='html', subs=(), show_browser=SHOW, embed_data=True)

        # Check if file was created
        self.assertTrue(os.path.isfile(filename + '.html'))

    def test_xdsmjs_embeddable(self):
        """
        Makes XDSMjs HTML file for the Sellar problem.

        The HTML file is embeddable (no head and body tags).
        """

        filename = 'xdsmjs_embeddable'  # this name is needed for XDSMjs
        p = om.Problem()
        p.model = model = SellarNoDerivatives()
        model.add_design_var('z', lower=np.array([-10.0, 0.0]), upper=np.array([10.0, 10.0]),
                             indices=np.arange(2, dtype=int))
        model.add_design_var('x', lower=0.0, upper=10.0)
        model.add_objective('obj')
        model.add_constraint('con1', equals=np.zeros(1))
        model.add_constraint('con2', upper=0.0)

        p.setup()
        p.final_setup()

        # Write output
        write_xdsm(p, filename=filename, out_format='html', subs=(), show_browser=SHOW, embed_data=True,
                   embeddable=True)

        # Check if file was created
        self.assertTrue(os.path.isfile(filename + '.html'))

    def test_html_writer_dct(self):
        """
        Makes XDSMjs input file.

        Data is in a dictionary
        """

        filename = 'xdsmjs2'  # this name is needed for XDSMjs

        data = {
            "nodes": [{"id": "Opt", "name": "Optimization", "type": "optimization"},
                      {"id": "MDA", "name": "MDA", "type": "mda"},
                      {"id": "DA1", "name": "Analysis 1"},
                      {"id": "DA2", "name": "Analysis 2"},
                      {"id": "DA3", "name": "Analysis 3"},
                      {"id": "Func", "name": "Functions"}
                      ],
            "edges": [{"from": "Opt", "to": "DA1", "name": "x_0,x_1"},
                      {"from": "DA1", "to": "DA3", "name": "x_share"},
                      {"from": "DA3", "to": "DA1", "name": "y_1^2"},
                      {"from": "MDA", "to": "DA1", "name": "x_2"},
                      {"from": "Func", "to": "Opt", "name": "f,c"},
                      {"from": "_U_", "to": "DA1", "name": "x_0"},
                      {"from": "DA3", "to": "_U_", "name": "y_0"}
                      ],
            "workflow": ["Opt", ["MDA", "DA1", "DA2", "DA3"], "Func"]
        }

        outfile = filename + '.html'
        write_html(outfile=outfile, source_data=data)

        self.assertTrue(os.path.isfile(outfile))

    def test_html_writer_str(self):
        """
        Makes XDSMjs input file.

        Data is a string.
        """

        filename = 'xdsmjs4'  # this name is needed for XDSMjs

        data = ("{'nodes': [{'type': 'optimization', 'id': 'Opt', 'name': 'Optimization'}, "
                "{'type': 'mda', 'id': 'MDA', 'name': 'MDA'}, {'id': 'DA1', 'name': 'Analysis 1'}, "
                "{'id': 'DA2', 'name': 'Analysis 2'}, {'id': 'DA3', 'name': 'Analysis 3'}, "
                "{'id': 'Func', 'name': 'Functions'}], "
                "'edges': [{'to': 'DA1', 'from': 'Opt', 'name': 'x_0,x_1'}, "
                "{'to': 'DA3', 'from': 'DA1', 'name': 'x_share'}, "
                "{'to': 'DA1', 'from': 'DA3', 'name': 'y_1^2'}, "
                "{'to': 'DA1', 'from': 'MDA', 'name': 'x_2'}, "
                "{'to': 'Opt', 'from': 'Func', 'name': 'f,c'}, "
                "{'to': 'DA1', 'from': '_U_', 'name': 'x_0'}, "
                "{'to': '_U_', 'from': 'DA3', 'name': 'y_0'}], "
                "'workflow': ['Opt', ['MDA', 'DA1', 'DA2', 'DA3'], 'Func']}")

        outfile = filename + '.html'
        write_html(outfile=outfile, source_data=data)

        self.assertTrue(os.path.isfile(outfile))

    def test_pyxdsm_identical_relative_names(self):
        class TimeComp(om.ExplicitComponent):

            def setup(self):
                self.add_input('t_initial', val=0.)
                self.add_input('t_duration', val=1.)
                self.add_output('time', shape=(2,))

            def compute(self, inputs, outputs):
                t_initial = inputs['t_initial']
                t_duration = inputs['t_duration']

                outputs['time'][0] = t_initial
                outputs['time'][1] = t_initial + t_duration

        class Phase(om.Group):

            def setup(self):
                super(Phase, self).setup()

                indep = om.IndepVarComp()
                for var in ['t_initial', 't_duration']:
                    indep.add_output(var, val=1.0)

                self.add_subsystem('time_extents', indep, promotes_outputs=['*'])

                time_comp = TimeComp()
                self.add_subsystem('time', time_comp)

                self.connect('t_initial', 'time.t_initial')
                self.connect('t_duration', 'time.t_duration')

                self.set_order(['time_extents', 'time'])

        p = om.Problem()
        p.driver = om.ScipyOptimizeDriver()
        orbit_phase = Phase()
        p.model.add_subsystem('orbit_phase', orbit_phase)

        systems_phase = Phase()
        p.model.add_subsystem('systems_phase', systems_phase)

        systems_phase = Phase()
        p.model.add_subsystem('extra_phase', systems_phase)
        p.model.add_design_var('orbit_phase.t_initial')
        p.model.add_design_var('orbit_phase.t_duration')
        p.model.add_objective('systems_phase.time.time')
        p.setup()

        p.run_model()

        write_xdsm(p, 'xdsmjs_orbit', out_format='html', show_browser=SHOW)
        self.assertTrue(os.path.isfile('xdsmjs_orbit.html'))

    def test_xdsmjs_mda(self):
        filename = 'xdsmjs_mda'
        out_format = 'html'
        prob = om.Problem(model=SellarMDA())
        prob.setup()
        prob.final_setup()

        # Write output
        write_xdsm(prob, filename=filename, out_format=out_format, quiet=QUIET, show_browser=SHOW, embed_data=True,
                   embeddable=True, include_solver=True)
        # Check if file was created
        self.assertTrue(os.path.isfile(filename + '.' + out_format))

    def test_xdsmjs_mdf(self):
        filename = 'xdsmjs_mdf'
        out_format = 'html'
        p = om.Problem(model=SellarMDA())
        model = p.model
        p.driver = om.ScipyOptimizeDriver()

        model.add_design_var('z', lower=np.array([-10.0, 0.0]), upper=np.array([10.0, 10.0]),
                             indices=np.arange(2, dtype=int))
        model.add_design_var('x', lower=0.0, upper=10.0)
        model.add_objective('obj')
        model.add_constraint('con1', equals=np.zeros(1))
        model.add_constraint('con2', upper=0.0)

        p.setup()
        p.final_setup()

        # Write output
        write_xdsm(p, filename=filename, out_format=out_format, show_browser=SHOW, include_solver=True)
        # Check if file was created
        self.assertTrue(os.path.isfile(filename + '.' + out_format))

    def test_xdsm_solver(self):
        import openmdao.api as om

        filename = 'xdsmjs_solver'
        out_format = 'html'
        p = om.Problem(model=SellarNoDerivatives())
        p.model.nonlinear_solver = om.NonlinearBlockGS()
        p.driver = om.ScipyOptimizeDriver()
        p.model.add_objective('obj')

        p.setup()
        p.run_model()

        # Write output
        write_xdsm(p, filename=filename, out_format=out_format, show_browser=SHOW, include_solver=True)
        # Check if file was created
        self.assertTrue(os.path.isfile(filename + '.' + out_format))

    def test_parallel(self):
        import openmdao.api as om

        class SellarMDA(om.Group):
            """
            Group containing the Sellar MDA.
            """

            def setup(self):
                indeps = self.add_subsystem('indeps', om.IndepVarComp(), promotes=['*'])
                indeps.add_output('x', 1.0)
                indeps.add_output('z', np.array([5.0, 2.0]))
                cycle = self.add_subsystem('cycle', om.ParallelGroup(), promotes=['*'])
                cycle.add_subsystem('d1', SellarDis1(), promotes_inputs=['x', 'z', 'y2'], promotes_outputs=['y1'])
                cycle.add_subsystem('d2', SellarDis2(), promotes_inputs=['z', 'y1'], promotes_outputs=['y2'])

                # Nonlinear Block Gauss Seidel is a gradient free solver
                cycle.nonlinear_solver = om.NonlinearBlockGS()

                self.add_subsystem('obj_cmp', om.ExecComp('obj = x**2 + z[1] + y1 + exp(-y2)',
                                                          z=np.array([0.0, 0.0]), x=0.0),
                                   promotes=['x', 'z', 'y1', 'y2', 'obj'])

                self.add_subsystem('con_cmp1', om.ExecComp('con1 = 3.16 - y1'), promotes=['con1', 'y1'])
                self.add_subsystem('con_cmp2', om.ExecComp('con2 = y2 - 24.0'), promotes=['con2', 'y2'])

        filename = 'xdsmjs_parallel'
        out_format = 'html'
        p = om.Problem(model=SellarMDA())
        model = p.model
        p.driver = om.ScipyOptimizeDriver()

        model.add_design_var('z', lower=np.array([-10.0, 0.0]), upper=np.array([10.0, 10.0]),
                             indices=np.arange(2, dtype=int))
        model.add_design_var('x', lower=0.0, upper=10.0)
        model.add_objective('obj')
        model.add_constraint('con1', equals=np.zeros(1))
        model.add_constraint('con2', upper=0.0)

        p.setup()
        p.final_setup()

        # Write output
        write_xdsm(p, filename=filename, out_format=out_format, quiet=QUIET, show_browser=SHOW, show_parallel=True)
        # Check if file was created
        self.assertTrue(os.path.isfile(filename + '.' + out_format))

    def test_execcomp(self):
        filename = 'xdsmjs_execcomp'
        out_format = 'html'
        p = om.Problem()
        indeps = p.model.add_subsystem('indeps', om.IndepVarComp(), promotes=['*'])
        indeps.add_output('x')
        p.model.add_subsystem('C1', om.ExecComp(['y=2.0*x+1.'], x=2.0), promotes=['*'])
        p.driver = om.ScipyOptimizeDriver()
        p.model.add_design_var('x', lower=0.0, upper=10.0)
        p.model.add_objective('y')
        p.setup()

        # Conclude setup but don't run model.
        p.final_setup()

        write_xdsm(p, filename=filename, out_format=out_format, quiet=QUIET, show_browser=SHOW, show_parallel=True)
        # Check if file was created
        self.assertTrue(os.path.isfile(filename + '.' + out_format))

    def test_doe(self):
        filename = 'xdsmjs_doe'
        out_format = 'html'
        p = om.Problem()
        indeps = p.model.add_subsystem('indeps', om.IndepVarComp(), promotes=['*'])
        indeps.add_output('x')
        p.model.add_subsystem('C1', om.ExecComp(['y=2.0*x+1.'], x=2.0), promotes=['*'])
        p.driver = om.DOEDriver()
        p.model.add_design_var('x', lower=0.0, upper=10.0)
        p.model.add_objective('y')
        p.setup()

        # Conclude setup but don't run model.
        p.final_setup()

        write_xdsm(p, filename=filename, out_format=out_format, quiet=QUIET, show_browser=SHOW, show_parallel=True)
        # Check if file was created
        self.assertTrue(os.path.isfile(filename + '.' + out_format))

    def test_meta_model(self):
        import openmdao.api as om
        from openmdao.components.tests.test_meta_model_structured_comp import SampleMap

        filename = 'xdsmjs_meta_model'
        out_format = 'html'
        model = om.Group()
        ivc = om.IndepVarComp()

        mapdata = SampleMap()

        params = mapdata.param_data
        x, y, z = params
        outs = mapdata.output_data
        z = outs[0]
        ivc.add_output('x', x['default'], units=x['units'])
        ivc.add_output('y', y['default'], units=y['units'])
        ivc.add_output('z', z['default'], units=z['units'])

        model.add_subsystem('des_vars', ivc, promotes=["*"])

        comp = om.MetaModelStructuredComp(method='slinear', extrapolate=True)

        for param in params:
            comp.add_input(param['name'], param['default'], param['values'])

        for out in outs:
            comp.add_output(out['name'], out['default'], out['values'])

        model.add_subsystem('comp', comp, promotes=["*"])
        p = om.Problem(model)
        p.setup()
        p.final_setup()

        write_xdsm(p, filename=filename, out_format=out_format, quiet=QUIET, show_browser=SHOW, show_parallel=True)
        # Check if file was created
        self.assertTrue(os.path.isfile(filename + '.' + out_format))

    def test_circuit_recurse(self):
        # Implicit component is also tested here

        import openmdao.api as om

        p = om.Problem()
        model = p.model

        model.add_subsystem('ground', om.IndepVarComp('V', 0., units='V'))
        model.add_subsystem('source', om.IndepVarComp('I', 0.1, units='A'))
        model.add_subsystem('circuit', Circuit())

        model.connect('source.I', 'circuit.I_in')
        model.connect('ground.V', 'circuit.Vg')

        model.add_design_var('ground.V')
        model.add_design_var('source.I')
        model.add_objective('circuit.D1.I')

        p.setup()

        # set some initial guesses
        p['circuit.n1.V'] = 10.
        p['circuit.n2.V'] = 1.

        p.run_model()

        write_xdsm(p, 'xdsmjs_circuit', out_format='html', quiet=QUIET, show_browser=SHOW, recurse=True)
        self.assertTrue(os.path.isfile('xdsmjs_circuit' + '.html'))

    def test_legend_and_class_names(self):
        import openmdao.api as om

        p = om.Problem()
        model = p.model

        model.add_subsystem('ground', om.IndepVarComp('V', 0., units='V'))
        model.add_subsystem('source', om.IndepVarComp('I', 0.1, units='A'))
        model.add_subsystem('circuit', Circuit())

        model.connect('source.I', 'circuit.I_in')
        model.connect('ground.V', 'circuit.Vg')

        model.add_design_var('ground.V')
        model.add_design_var('source.I')
        model.add_objective('circuit.D1.I')

        p.setup()

        # set some initial guesses
        p['circuit.n1.V'] = 10.
        p['circuit.n2.V'] = 1.

        p.run_model()

        write_xdsm(p, 'xdsmjs_circuit_legend', out_format='html', quiet=QUIET, show_browser=SHOW, recurse=True,
                   legend=True)
        self.assertTrue(os.path.isfile('xdsmjs_circuit_legend' + '.html'))

        write_xdsm(p, 'xdsmjs_circuit_class_names', out_format='html', quiet=QUIET, show_browser=SHOW, recurse=True,
                   class_names=True)
        self.assertTrue(os.path.isfile('xdsmjs_circuit_class_names' + '.html'))

    def test_xdsmjs_right_outputs(self):
        """Makes XDSM for the Sellar problem"""
        filename = 'xdsmjs_outputs_on_the_right'
        p = om.Problem()
        p.model = model = SellarNoDerivatives()
        model.add_design_var('z', lower=np.array([-10.0, 0.0]), upper=np.array([10.0, 10.0]),
                             indices=np.arange(2, dtype=int))
        model.add_design_var('x', lower=0.0, upper=10.0)
        model.add_objective('obj')
        model.add_constraint('con1', equals=np.zeros(1))
        model.add_constraint('con2', upper=0.0)

        p.setup()
        p.final_setup()

        msg = 'Right side outputs not implemented for XDSMjs.'

        # Write output
        with assert_warning(Warning, msg):
            write_xdsm(p, filename=filename, out_format='html', show_browser=SHOW, quiet=QUIET, output_side='right')

        # Check if file was created
        self.assertTrue(os.path.isfile(filename + '.html'))

    def test_wrong_out_format(self):
        """Incorrect output format error."""

        filename = 'xdsm_wrong_format'  # this name is needed for XDSMjs
        prob = om.Problem()
        prob.model = SellarNoDerivatives()

        prob.setup()
        prob.final_setup()

        # no output checking, just make sure no exceptions raised
        with self.assertRaises(ValueError):
            write_xdsm(prob, filename=filename, out_format='jpg', subs=(), show_browser=SHOW)

    def test_command(self):
        """
        Check that there are no errors when running from the command line with a script.
        """
        from openmdao.test_suite.scripts import sellar
        filename = os.path.abspath(sellar.__file__)
        check_call('openmdao xdsm --no_browser {}'.format(filename))


@unittest.skipUnless(XDSM, "The pyXDSM package is required.")
@use_tempdirs
class TestCustomXDSMViewer(unittest.TestCase):

    def test_custom_writer(self):
        from omxdsm.xdsm_writer import XDSMjsWriter

        class CustomWriter(XDSMjsWriter):
            """Customized XDSM writer, based on the XDSMjs writer."""

            @staticmethod
            def format_block(names, **kwargs):
                """This method is overwritten, to implement some different formatting."""
                return [name.upper() for name in names]

        p = om.Problem()
        p.model = SellarNoDerivatives()

        p.setup()
        p.final_setup()

        my_writer = CustomWriter()
        filename = 'xdsm_custom_writer'  # this name is needed for XDSMjs
        # Write output
        write_xdsm(p, filename=filename, writer=my_writer, show_browser=SHOW)

        # Check if file was created
        self.assertTrue(os.path.isfile(filename + '.' + my_writer.extension))

        # Check that error is raised in case of wrong writer type
        filename = 'xdsm_custom_writer2'  # this name is needed for XDSMjs
        with self.assertRaises(TypeError):  # Wrong type passed for writer
            write_xdsm(p, filename=filename, writer=1, subs=(), show_browser=SHOW)

        # Check warning, if settings for custom writer are not found
        my_writer2 = CustomWriter(name='my_writer')
        filename = 'xdsm_custom_writer3'

        msg = 'Writer name "my_writer" not found, there will be no character ' \
              'substitutes used. Add "my_writer" to your settings, or provide a tuple for' \
              'character substitutes.'

        # Write output
        with assert_warning(Warning, msg):
            write_xdsm(p, filename=filename, writer=my_writer2, show_browser=SHOW)


if __name__ == "__main__":
    unittest.main()
