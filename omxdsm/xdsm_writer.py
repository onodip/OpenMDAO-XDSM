"""
XDSM writer for OpenMDAO 3.X using the pyXDSM package or XDSMjs.

The XDSM (eXtended Design Structure Matrix) is a tool used to visualize MDO processes.
It is an extension of the classical Design Structure Matrix commonly used in systems engineering to
describe the interfaces among components of a complex system.

Theoretical background:
Lambe, AB and Martins, JRRA (2012): Extensions to the Design Structure Matrix for the Description of
Multidisciplinary Design, Analysis, and Optimization Processes.
In: Structural and Multidisciplinary Optimization.

The pyXDSM package is available at https://github.com/mdolab/pyXDSM.
XDSMjs is available at https://github.com/OneraHub/XDSMjs.
"""

import json
import warnings
from collections import OrderedDict
from distutils.version import LooseVersion

from numpy.distutils.exec_command import find_executable
from openmdao.api import Problem

from omxdsm.base import AbstractXDSMWriter, BaseXDSMWriter
from omxdsm.formatting import _textify, _multiline_block, _replace_chars, _format_solver_str, _replace_illegal_chars, \
    _convert_name, _make_rel_path
from omxdsm.settings import *
from omxdsm.utils import _prune_connections, _get_comps

try:
    from openmdao.utils.general_utils import simple_warning
except ImportError:
    simple_warning = warnings.warn
from openmdao.visualization.n2_viewer.n2_viewer import _get_viewer_data
from pyxdsm.XDSM import XDSM

from omxdsm.html_writer import write_html


# Settings for pyXDSM

# The box width can be set by the user:
# _DEFAULT_BOX_WIDTH or _DEFAULT_BOX_CHAR_LIMIT can be overwritten with keyword argument "box_width"
_DEFAULT_BOX_WIDTH = 3.  # Width of boxes [cm]. Depends on other settings, weather it is used or not
# Maximum characters for line breaking.
# The line can be longer, if a variable name is longer.
_DEFAULT_BOX_CHAR_LIMIT = 25
# Controls the appearance of boxes
# Can be set with keyword argument "box_stacking"
# Options: horizontal, vertical, max_chars, cut_chars, empty
_DEFAULT_BOX_STACKING = 'max_chars'
_PROCESS_ARROWS = False  # Show arrowheads in process connection lines
_MAX_BOX_LINES = None  # Maximum number of lines in a box. No limit, if None.
_START_INDEX = 0  # If components are indexed, this will be the first index. 0 or 1
_DEFAULT_NUMBER_ALIGNMENT = 'horizontal'  # Place the index above ("vertical") or beside ("horizontal") the name


class XDSMjsWriter(AbstractXDSMWriter):
    """
    Creates an interactive diagram with XDSMjs, which can be opened with a web browser.

    XDSMjs was created by Remi Lafage. The code and documentation is available at
    https://github.com/OneraHub/XDSMjs

    Attributes
    ----------
    driver : str
        Driver default name.
    comp_names : list
        Component names.
    _ul : str
        Name of the virtual first element.
    _multi_suffix : str
        If component ends with this string, it will be treated as a parallel component.
    reserved_words : tuple
        Ignored at text formatting.
    extension : str
        Output file saved with this extension. Value fixed at 'html' for this class.
    type_map : str
        XDSM component type.
    class_names : bool
        Include class names of components in diagonal blocks.
    """

    def __init__(self, name='xdsmjs', class_names=False, options={}):
        """
        Initialize.

        Parameters
        ----------
        name : str
            Name of this XDSM writer
        class_names : bool
            Include class names of the components in the diagonal
        options : dict
            Writer options.
        """
        super(XDSMjsWriter, self).__init__(name=name)
        self.driver = 'opt'  # Driver default name
        self.comp_names = []  # Component names
        self._ul = '_U_'  # Name of the virtual first element
        # If component ends with this string, it will be treated as a parallel component
        self._multi_suffix = '_multi'
        self.reserved_words = self._ul,  # Ignored at text formatting
        # Output file saved with this extension
        self.extension = 'html'
        if self.name in COMPONENT_TYPE_MAP:
            self.type_map = COMPONENT_TYPE_MAP[self.name]
        else:  # Use default
            self.type_map = COMPONENT_TYPE_MAP[DEFAULT_WRITER]
            msg = 'Name "{}" not found in component type mapping, will default to "{}"'
            simple_warning(msg.format(self.name, DEFAULT_WRITER))
        self.class_names = class_names

    def _format_id(self, name, subs=(('_', ''),)):
        # Changes forbidden characters in the "id" of a component
        if name not in self.reserved_words:
            return _replace_chars(name, subs)
        else:
            return name

    def connect(self, src, target, label, **kwargs):
        """
        Connect to system block.

        Parameters
        ----------
        src : str
            Source system name.
        target : str
            Target system name.
        label : str
            Label to be displayed in the XDSM data block.
        **kwargs : dict
            Keyword args
        """
        edge = {'to': self._format_id(target), 'from': self._format_id(src), 'name': label}
        self.connections.append(edge)

    def add_solver(self, name, label=None, **kwargs):
        """
        Add a solver.

        Parameters
        ----------
        name : str
            Name of the solver
        label : str
            Label in the XDSM
        **kwargs : dict
            Keyword args
        """
        self.comp_names.append(self._format_id(name))
        style = self.type_map['solver']
        self.add_system(node_name=name, style=style, label=label, **kwargs)

    def add_comp(self, name, label=None, stack=False, comp_type=None, **kwargs):
        """
        Add a component.

        Parameters
        ----------
        label : str
            Label in the XDSM, defaults to the name of the component.
        name : str
            Name of the component
        stack : bool
            True for parallel components.
            Defaults to False.
        comp_type : str or None
            Component type, e.g. explicit, implicit or metamodel
        **kwargs : dict
            Keyword args
        """
        style = self.type_map.get(comp_type, 'function')
        self.comp_names.append(self._format_id(name))
        self.add_system(node_name=name, style=style, label=label, stack=stack, **kwargs)

    def add_driver(self, label, name='opt', driver_type='optimization', **kwargs):
        """
        Add a driver.

        Parameters
        ----------
        label : str
            Label in the XDSM.
        name : str
            Name of the driver.
        driver_type : str
            Optimization or DOE.
            Defaults to "optimization".
        **kwargs : dict
            Keyword args
        """
        self.driver = self._format_id(name)
        style = self.type_map.get(driver_type, 'optimization')
        self.add_system(node_name=name, style=style, label=label, **kwargs)

    def add_system(self, node_name, style, label=None, stack=False, cls=None, **kwargs):
        """
        Add a system.

        Parameters
        ----------
        node_name : str
            Name of the system
        style : str
            Block formatting style.
        label : str, optional
            Label in the XDSM, defaults to the name of the component.
        stack : bool, optional
            True for parallel.
            Defaults to False.
        **kwargs : dict
            Keyword args
        """
        if label is None:
            label = node_name
        if stack:  # Parallel block
            style += self._multi_suffix  # Block will be stacked in XDSMjs, if ends with this string
        if cls is not None:
            label += '-{}'.format(cls)  # Append class name
        sys_dct = {"type": style, "id": self._format_id(node_name), "name": label}
        self.comps.append(sys_dct)

    def add_workflow(self, solver=None):
        """
        Add a workflow. If "comp_names" is None, all components will be included.

        Parameters
        ----------
        solver : dict or None, optional
            Solver info.
        """
        def recurse(solv, nr, process):
            for i, cmp in enumerate(process, start=1):
                if cmp == solv:
                    process[i:i + nr] = [process[i:i + nr]]
                    return
                elif isinstance(cmp, list):
                    recurse(solv, nr, cmp)
                    break

        if solver is None:
            comp_names = self.comp_names
            solver_name = None
        else:
            solver_name = solver['abs_name']
            comp_names = [c['abs_name'] for c in solver['comps']]
        nr_comps = len(comp_names)

        if not self.processes:  # If no process was added yet, add the process of the driver
            self.processes = [self.driver, list(self.comp_names)]
        recurse(solver_name, nr_comps, self.processes)  # Mutates self.processes

    def add_input(self, name, label=None, style='DataIO', stack=False):
        """
        Add input connection.

        Parameters
        ----------
        name : str
            Target name.
        label : str, optional
            Label for connection.
        style : str, optional
            Formatting style.
        stack : bool, optional
            True for parallel.
            Defaults to False.
        """
        self.connect(src=self._ul, target=name, label=label)

    def add_output(self, name, label=None, style='DataIO', stack=False, side=DEFAULT_OUTPUT_SIDE):
        """
        Add output connection.

        Parameters
        ----------
        name : str
            Target name.
        label : str, optional
            Label for connection.
        style : str, optional
            Formatting style.
        stack : bool, optional
            True for parallel.
            Defaults to False.
        side : str, optional
            Location of output, either 'left' or 'right'.
        """
        if side == "left":
            self.connect(src=name, target=self._ul, label=label)
        else:
            simple_warning('Right side outputs not implemented for XDSMjs.')
            self.connect(src=name, target=self._ul, label=label)

    def collect_data(self):
        """
        Make a dictionary with the structure of an XDSMjs JSON file.

        Returns
        -------
            dict
        """
        return {'edges': self.connections, 'nodes': self.comps, 'workflow': self.processes}

    def write(self, filename='xdsmjs', embed_data=True, **kwargs):
        """
        Write HTML output file, and depending on value of "embed_data" a JSON file with the data.

        If "embed_data" is true, a single standalone HTML file will be generated, which includes
        the data of the XDSM diagram.

        Parameters
        ----------
        filename : str, optional
            Output file name (without extension).
            Defaults to "xdsmjs".
        embed_data : bool, optional
            Embed XDSM data into the HTML file.
            If False, a JSON file will be also written.
            Defaults to True.
        **kwargs : dict
            Keyword args
        """
        data = self.collect_data()

        html_filename = '.'.join([filename, 'html'])

        embeddable = kwargs.pop('embeddable', False)
        if embed_data:
            write_html(outfile=html_filename, source_data=data, embeddable=embeddable)  # Write HTML file
        else:
            json_filename = '.'.join([filename, 'json'])
            with open(json_filename, 'w') as f:
                json.dump(data, f)
            write_html(outfile=html_filename, data_file=json_filename, embeddable=embeddable)  # Write HTML file
        print('XDSM output file written to: {}'.format(html_filename))


class XDSMWriter(XDSM, BaseXDSMWriter):
    r"""
    XDSM with some additional semantics.

    Creates a TeX file and TikZ file, and converts it to PDF.

    .. note:: On Windows it might be necessary to add the second line in the
       :class:`~pyxdsm.XDSM.XDSM`, if an older version of the package is installed::

        diagram_styles_path = os.path.join(module_path, 'diagram_styles')
        diagram_styles_path = diagram_styles_path.replace('\\', '/')  # Add this line on Windows

       This issue is resolved in the latest version of pyXDSM.

    Attributes
    ----------
    name : str
        Name of XDSM writer.
    box_stacking : str
        Controls the appearance of boxes. Possible values are: 'max_chars','vertical',
        'horizontal','cut_chars','empty'.
    number_alignment : str
        Position of number relative to the component label. Possible values are: 'horizontal',
        'vertical'.
    add_component_indices : bool
        If true, display components with numbers.
    has_legend : bool
        If true, a legend will be added to the diagram.
    class_names : bool
        If true, appends class name of groups/components to the component blocks of diagram.
    extension : str
        Output file saved with this extension. Value fixed at 'pdf' for this class.
    type_map : str
        XDSM component type.
    _comp_indices : dict
        Maps the component names to their index (position on the matrix diagonal).
    _styles_used : set
        Styles in use (needed for legend).
    _comps : list
        List of component dictionaries.
    _loop_ends : list
        Index of last components in a process.
    _nr_comps : int
        Number of components.
    _pyxdsm_version : str
        Version of the installed pyXDSM package.
    """

    def __init__(self, name='pyxdsm', box_stacking=_DEFAULT_BOX_STACKING,
                 number_alignment=_DEFAULT_NUMBER_ALIGNMENT, legend=False, class_names=False,
                 add_component_indices=True, options={}):
        """
        Initialize.

        Parameters
        ----------
        name : str
            Name of XDSM writer.
        box_stacking : str
            Controls the appearance of boxes. Possible values are: 'max_chars','vertical',
            'horizontal','cut_chars','empty'.
        number_alignment : str
            Position of number relative to the component label. Possible values
            are: 'horizontal', 'vertical'.
        legend : bool
            If true, a legend will be added to the diagram.
        class_names : bool, optional
            If true, appends class name of groups/components to the component blocks of diagram.
            Defaults to False.
        add_component_indices : bool
            If true, display components with numbers.
        options : dict
            Keyword argument options of the XDSM class.
        """
        try:
            from pyxdsm import __version__ as pyxdsm_version
            self._pyxdsm_version = pyxdsm_version
        except ImportError:
            # Older pyxdsm did not have a version attribute
            self._pyxdsm_version = '1.0.0'
            pyxdsm_version = LooseVersion(self._pyxdsm_version)

        if pyxdsm_version > LooseVersion('1.0.0'):
            super(XDSMWriter, self).__init__(**options)
        else:
            if options:
                msg = 'pyXDSM {} does not take keyword arguments. Consider upgrading this ' \
                      'package. Writer options "{}" will be ignored'
                simple_warning(msg.format(pyxdsm_version, options.keys()))
            super(XDSMWriter, self).__init__()

        self.name = name
        # Formatting options
        self.box_stacking = box_stacking
        self.class_names = class_names
        self.number_alignment = number_alignment
        self.add_component_indices = add_component_indices
        self.has_legend = legend  # If true, a legend will be added to the diagram
        # Output file saved with this extension
        self.extension = 'pdf'

        try:
            type_map_name = self.name
            if pyxdsm_version < LooseVersion('2.0.0'):
                type_map_name += ' 1.0'
            self.type_map = COMPONENT_TYPE_MAP[type_map_name]
        except KeyError:
            self.type_map = COMPONENT_TYPE_MAP[DEFAULT_WRITER]
            msg = 'Name "{}" not found in component type mapping, will default to "{}"'
            simple_warning(msg.format(self.name, DEFAULT_WRITER))
        # Number of components
        self._nr_comps = 0
        # Maps the component names to their index (position on the matrix diagonal)
        self._comp_indices = {}
        # List of component dictionaries
        self._comps = []
        # Index of last components in a process
        self._loop_ends = []
        # Styles in use (needed for legend)
        self._styles_used = set()

    def write(self, filename=None, **kwargs):
        """
        Write the output file.

        This just wraps the XDSM version and throws out incompatible arguments.

        Parameters
        ----------
        filename : str
            Name of the file to be written.
        **kwargs : dict
            Keyword args
        """
        build = kwargs.pop('build', False)
        if LooseVersion(self._pyxdsm_version) <= LooseVersion('1.0.0'):
            kwargs = {}
        else:
            kwargs.setdefault('cleanup', True)

        for comp in self._comps:
            label = comp['label']
            # If the process steps are included in the labels
            if self.add_component_indices:
                i = i0 = comp.pop('index', None)
                step = comp.pop('step', None)
                # For each closed loop increment the process index by one
                for loop in self._loop_ends:
                    if loop < i0:
                        i += 1
                # Step is not None for the driver and solvers, for these a different label
                # will be made showing the starting end and step and the index of the next
                # step.
                if step is not None:
                    i = self._make_loop_str(first=i, last=step, start_index=_START_INDEX)
            else:
                i = None
            label = self.finalize_label(i, label, self.number_alignment,
                                        class_name=comp['class'])

            # Convert from math mode to regular text, if it is a one-liner wrapped in math mode
            if isinstance(label, str):
                label = _textify(label)
            comp['label'] = label  # Now the label is finished.
            # Now really add the system with the XDSM class' method
            self.add_system(**comp)

        super(XDSMWriter, self).write(file_name=filename, build=build, **kwargs)

    def add_system(self, node_name, style, label, stack=False, faded=False, **kwargs):
        """
        Add a system.

        Parameters
        ----------
        node_name : str
            Name of the system.
        style : str
            Block formatting style, e.g. Analysis
        label : str
            Label of system in XDSM.
        stack : bool
            Defaults to False.
        faded : bool
            Defaults to False.
        **kwargs : dict
            Keyword arguments.
        """
        super(XDSMWriter, self).add_system(node_name=node_name, style=style, label=label,
                                           stack=stack, faded=faded)

    def _add_system(self, node_name, style, label, stack=False, faded=False, cls=None):
        # Adds a system dictionary to the components.
        # This dictionary can be modified by other methods.
        self._styles_used.add(style)

        if label is None:
            label = node_name
        self._comp_indices[node_name] = self._nr_comps
        sys_dct = {'node_name': node_name, 'style': style, 'label': label, 'stack': stack, 'faded': faded,
                   'index': self._nr_comps, 'class': cls}
        self._nr_comps += 1
        self._comps.append(sys_dct)

    def add_solver(self, name, label=None, **kwargs):
        """
        Add a solver.

        Parameters
        ----------
        label : str
            Label in the XDSM
        name : str
            Name of the solver
        **kwargs : dict
            Keyword args
        """
        style = self.type_map['solver']
        self._add_system(node_name=name, style=style, label=label, **kwargs)

    def add_comp(self, name, label=None, stack=False, comp_type=None, **kwargs):
        """
        Add a component.

        Parameters
        ----------
        label : str
            Label in the XDSM, defaults to the name of the component.
        name : str
            Name of the component
        stack : bool
            True for parallel components.
            Defaults to False.
        comp_type : str or None
            Component type, e.g. explicit, implicit or metamodel
        **kwargs : dict
            Keyword args
        """
        style = self.type_map.get(comp_type, 'Function')
        self._add_system(node_name=name, style=style, label=label, stack=stack, **kwargs)

    def add_driver(self, name, label=None, driver_type='Optimization', **kwargs):
        """
        Add an optimizer.

        Parameters
        ----------
        label : str
            Label in the XDSM
        name : str
            Name of the optimizer.
        driver_type : str
            Driver type can be "Optimizer" or "DOE".
            Defaults to "Optimizer"
        **kwargs : dict
            Keyword args
        """
        style = self.type_map.get(driver_type, 'Optimization')
        self._add_system(node_name=name, style=style, label=label, **kwargs)

    def add_workflow(self, solver=None):
        """
        Add a workflow. If "comp_names" is None, all components will be included.

        Parameters
        ----------
        solver : dict or None, optional
            List of component names.
            Defaults to None.
        """
        if hasattr(self, 'processes'):  # Not available in versions <= 1.0.0
            index_dct = self._comp_indices

            if solver is None:
                # Add driver
                idx = 0
                comp_names = [c['node_name'] for c in self._comps]  # Driver process
                step = len(self._comps) + 1
                self._comps[idx]['step'] = step
            else:
                solver_name = solver['abs_name']
                comp_names = [c['abs_name'] for c in solver['comps']]
                nr = len(comp_names)
                idx = index_dct[solver_name]
                self._comps[idx]['step'] = nr + idx + 1
                comp_names = [solver_name] + comp_names
                # Loop through all processes added so far
                # Assumes, that processes are added in the right order, first the higher level
                # processes
                for proc in self.processes:
                    process_name = proc[0]
                    for i, item in enumerate(proc, start=1):
                        if solver_name == item:  # solver found in an already added process
                            # Delete items belonging to the new process from the others
                            proc[i:i + nr] = []
                            process_index = index_dct[process_name]
                            # There is a process loop inside, this adds plus one step
                            self._comps[process_index]['step'] += 1
            self._loop_ends.append(self._comp_indices[comp_names[-1]])
            # Close the loop by
            comp_names.append(comp_names[0])
            self.add_process(comp_names, arrow=_PROCESS_ARROWS)

    @staticmethod
    def format_block(names, stacking='vertical', **kwargs):
        """
        Format a block.

        Parameters
        ----------
        names : list
            Names to put into block.
        stacking : str
            Controls the appearance of boxes. Possible values are: 'max_chars','vertical',
            'horizontal','cut_chars','empty'.
        **kwargs : dict
            Alternative way to add element attributes. Use with attention, can overwrite
            some built-in python names as "class" or "id" if misused.

        Returns
        -------
        str
            The block string.
        """
        end_str = ', ...'
        max_lines = kwargs.pop('box_lines', _MAX_BOX_LINES)
        if stacking == 'vertical':
            if (max_lines is None) or (max_lines >= len(names)):
                return names
            else:
                names = names[0:max_lines]
                names[-1] = names[-1] + end_str
                return names
        elif stacking == 'horizontal':
            return ', '.join(names)
        elif stacking in ('max_chars', 'cut_chars'):
            max_chars = kwargs.pop('box_width', _DEFAULT_BOX_CHAR_LIMIT)
            if len(names) < 2:
                return names
            else:
                lengths = 0
                lines = list()
                line = ''
                for name in names:
                    lengths += len(name)
                    if lengths <= max_chars:
                        if line:  # there are already var names on the line
                            line += ', ' + name
                        else:  # it will be the first var name on the line
                            line = name
                    else:  # make new line
                        if stacking == 'max_chars':
                            if line:
                                lines.append(line)
                            line = name
                            lengths = len(name)
                        else:  # 'cut_chars'
                            lines.append(line + end_str)
                            line = ''  # No new line
                            break
                if line:  # it will be the last line, if var_names was not empty
                    lines.append(line)
                if len(lines) > 1:
                    return lines
                else:
                    return lines[0]  # return the string instead of a list
        elif stacking == 'empty':  # No variable names in the data block, good for big diagrams
            return ''
        else:
            msg = 'Invalid block stacking option "{}".'
            raise ValueError(msg.format(stacking))

    @staticmethod
    def format_var_str(name, var_type, superscripts=None):
        """
        Format string displaying variable name.

        Parameters
        ----------
        name : str
            Name (label in the block) of the variable.
        var_type : str
            Variable type.
        superscripts : dict or None, optional
            A dictionary mapping variable types to their superscript notation

        Returns
        -------
        str
            Formatted var string.
        """
        if superscripts is None:
            superscripts = SUPERSCRIPTS
        sup = superscripts[var_type]
        return '{}^{{{}}}'.format(name, sup)

    @staticmethod
    def _make_loop_str(first, last, start_index=0):
        # Start index shifts all numbers
        i = start_index
        txt = '{}, {} $ \\rightarrow $ {}'
        return txt.format(first + i, last + i, first + i + 1)

    def finalize_label(self, number, txt, alignment, class_name=None):
        """
        Add an index to the label either above or on the left side.

        Parameters
        ----------
        number : None or empty string or int
            Number value for the label.
        txt : str
            Text appended to the number string.
        alignment : str
            Indicates alignment of label. Either 'horizontal' or 'vertical'.
        class_name : str or None, optional
            Class name.
            Defaults to None.

        Returns
        -------
        str or list(str)
            Label to be used for this item. List, if it is multiline.
        """
        if isinstance(txt, str):
            txt = [txt]  # Make iterable, it will be converted back if there is only 1 line.

        if self.class_names and (class_name is not None):
            # Change underscores to escaped characters
            class_name = _replace_chars(class_name, substitutes=(('_', r'\_'),))
            if self.class_names == "short" and ':' in class_name:  # If it has a path in the name, it contains ":"
                class_name = class_name.split(':')[-1]  # Keep only the name, remove path

            # Italic text. Replaces underscores with escaped underscores.
            cls_name = r'\textit{{{}}}'.format(class_name)
            txt.append(cls_name)  # Class name goes to a new line
        if number:  # If number is None or empty string, it won't be inserted
            number_str = '{}: '.format(number)
            if alignment == 'horizontal':
                txt[0] = number_str + txt[0]  # Number added to first line
            elif alignment == 'vertical':
                txt.insert(0, number_str)  # Number added to new line
            else:
                msg = '"{}" is an invalid option for number_alignment, it will be ignored.'
                simple_warning(msg.format(alignment))
        return _multiline_block(*txt)

    def _make_legend(self, title="Legend"):
        """
        Add a legend row to the matrix. The labels of this row show the used component types.

        Parameters
        ----------
        title : str, optional
            Defaults to "Legend".

        Returns
        -------
            str
        """
        node_str = r'\node [{style}] ({name}) {{{label}}};'
        styles = sorted(self._styles_used)  # Alphabetical sort
        for i, style in enumerate(styles):
            super(XDSMWriter, self).add_system(node_name="style{}".format(i), style=style, label=style)
        style_strs = [node_str.format(name="style{}".format(i), style=style, label=style)
                      for i, style in enumerate(styles)]
        title_str = r'\node (legend_title) {{\LARGE \textbf{{{title}}}}};\\'
        return title_str.format(title=title) + '  &\n'.join(style_strs) + r'\\'

    def _build_node_grid(self):
        """
        Optionally appends the legend to the node grid.

        Returns
        -------
        str
            A grid of the nodes.
        """
        node_grid = super(XDSMWriter, self)._build_node_grid()
        if self.has_legend:
            node_grid += self._make_legend()
        return node_grid


def write_xdsm(data_source, filename, model_path=None, recurse=True,
               include_external_outputs=True, out_format='tex',
               include_solver=False, subs=CHAR_SUBS, show_browser=True,
               add_process_conns=True, show_parallel=True, quiet=False, output_side=DEFAULT_OUTPUT_SIDE,
               legend=False, class_names=True, equations=False, include_indepvarcomps=True,
               writer_options={}, **kwargs):
    """
    Write XDSM diagram of an optimization problem.

    With the 'tex' or 'pdf' output format it uses the pyXDSM package, with 'html'
    output format it uses XDSMjs.

    If a component (or group) name is not unique in the diagram, the systems absolute path is
    used as a label. If the component (or group) name is unique, the relative name of the
    system is the label.

    In the diagram the connections are marked with the source name.

    Writer specific settings and default:

    pyXDSM

    * The appearance of the boxes can be controlled with "box_stacking" and "box_width" arguments.
      The box stacking can be:

      * "horizontal" - All variables in one line
      * "vertical" - All variables in one column
      * "cut_chars" - The text in the box will be one line with the maximum number of characters
        limited by "box_width".
      * "max_chars" - The "box_width" argument is used to determine
        the maximum allowed width of boxes (in characters).
      * "empty" - There are no variable names in the data block. Good for large diagrams.

      A default value is taken, if not specified.
    * By default the part of variable names following underscores (_)
      are not converted to subscripts.
      To write in subscripts wrap that part of the name into a round bracket.
      Example: To write :math:`x_12` the variable name should be "x(12)"
    * "box_lines" can be used to limit the number of lines, if the box stacking is vertical
    * "numbered_comps": bool, If True, components are numbered. Defaults to True.
    * "number_alignment": str, Horizontal or vertical. Defaults to horizontal. If "numbered_comps"
      is True, it positions the number either above or in front of the component label.

    XDSMjs

    * If "embed_data" is true, a single standalone HTML file will be generated, which includes
      the data of the XDSM diagram.
    * variable names with exactly one underscore have a subscript.
      Example: "x_12" will be :math:`x_12`
    * If "embeddable" is True, gives a single HTML file that doesn't have the <html>, <DOCTYPE>,
      <body> and <head> tags. If False, gives a single, standalone HTML file for viewing.

    Parameters
    ----------
    data_source : Problem or str
        The Problem or case recorder database containing the model or model data.
    filename : str
        Name of the output files (do not provide file extension)
    model_path : str or None, optional
        Path to the subsystem to be transcribed to XDSM.  If None, use the model root.
    recurse : bool, optional
        If False, treat the top level of each name as the source/target component.
    include_external_outputs : bool, optional
        If True, show externally connected outputs when transcribing a subsystem.
        Defaults to True.
    out_format : str, optional
        Output format, one of "tex" or "pdf" (pyXDSM) or "html" (XDSMjs).
        Defaults to "tex".
    include_solver : bool, optional
        Include or not the problem model's nonlinear solver in the XDSM.
    subs : dict(str, tuple), tuple(str, str), optional
        Characters to be replaced. Dictionary with writer names and character pairs or just the
        character pairs.
    show_browser : bool, optional
        If True, pop up a browser to view the generated html file.
        Defaults to True.
    add_process_conns : bool, optional
        Add process connections (thin black lines)
        Defaults to True.
    show_parallel : bool, optional
        Show parallel components with stacked blocks.
        Defaults to True.
    quiet : bool, optional
        Set to True to suppress output from pdflatex. Applicable only for 'tex' or 'pdf' output format.
    output_side : str or dict(str, str)
        Left or right, or a dictionary with component types as keys. Component type key can
        be 'optimization', 'doe' or 'default'.
        Defaults to "left".
    legend : bool, optional
        If true, it adds a legend to the diagram.
        Defaults to False.
    class_names : bool or str, optional
        If true, appends class name of the groups/components to the component blocks of the diagram.
        If it is equal to "short", only the class name is added, and not the full path of the class.
        Defaults to False.
    equations : bool, optional
        If true, for ExecComps their equations are shown in the diagram
        Defaults to False.
    include_indepvarcomps : bool, optional
        Include IndepVarComps as system but only as external inputs. If turned off, the XDSM is simpler.
        Defaults to True.
    writer_options : dict, optional
        Options passed to the writer class at initialization.
    **kwargs : dict
        Keyword arguments

    Returns
    -------
       XDSM or AbstractXDSMWriter
    """
    build_pdf = False
    writer = kwargs.pop('writer', None)

    if out_format in ('tex', 'pdf') and (writer is None):
        if out_format == 'pdf':
            if not find_executable('pdflatex'):
                print("Can't find pdflatex, so a pdf can't be generated.")
            else:
                build_pdf = True

    viewer_data = _get_viewer_data(data_source)

    driver = viewer_data.get('driver', None)
    if driver:
        driver_name = driver.get('name', None)
        driver_type = driver.get('type', 'optimization')
    else:
        driver_name = None
        driver_type = 'optimization'

    design_vars = viewer_data.get('design_vars', None)
    responses = viewer_data.get('responses', None)

    if model_path is not None:
        if isinstance(data_source, Problem):
            _model = data_source.model._get_subsystem(model_path)  # TODO private method
            if _model is None:
                msg = 'Model path "{}" does not exist in problem "{}".'
                raise ValueError(msg.format(model_path, data_source))
            design_vars = _model.get_design_vars()
            responses = _model.get_responses()
        else:
            msg = 'Model path is not supported when data source is "{}".'
            raise ValueError(msg.format(type(data_source)))

    if design_vars is None:
        simple_warning('The XDSM diagram will show only the model hierarchy, '
                       'as the driver, design variables and responses are not '
                       'available.')

    filename = filename.replace('\\', '/')  # Needed for LaTeX

    # If the "writer" argument not provided, the output format is used to choose the writer
    if writer is None:
        try:
            writer = OUT_FORMATS[out_format]
        except KeyError:
            msg = 'Invalid output format "{}", choose from: {}'
            raise ValueError(msg.format(out_format, OUT_FORMATS.keys()))
        writer_name = writer.lower()  # making it case-insensitive
        if isinstance(subs, dict):
            subs = subs[writer_name]  # Getting the character substitutes of the chosen writer
    else:
        if isinstance(writer, BaseXDSMWriter):
            try:
                subs = subs[writer.name]
            except KeyError:
                msg = 'Writer name "{0}" not found, there will be no character ' \
                      'substitutes used. Add "{0}" to your settings, or provide a tuple for' \
                      'character substitutes.'
                simple_warning(msg.format(writer.name, subs))
                subs = ()
        else:
            msg = 'Custom XDSM writer should be an instance of BaseXDSMWriter, now it is a "{}".'
            raise TypeError(msg.format(type(writer)))

    return _write_xdsm(filename, viewer_data=viewer_data, driver=driver_name, include_solver=include_solver,
                       model_path=model_path, design_vars=design_vars, responses=responses, writer=writer,
                       recurse=recurse, subs=subs, include_external_outputs=include_external_outputs,
                       show_browser=show_browser, add_process_conns=add_process_conns, build_pdf=build_pdf,
                       show_parallel=show_parallel, quiet=quiet, driver_type=driver_type, output_side=output_side,
                       legend=legend, class_names=class_names, writer_options=writer_options, equations=equations,
                       include_indepvarcomps=include_indepvarcomps, **kwargs)


def _write_xdsm(filename, viewer_data, driver=None, include_solver=False, cleanup=True,
                design_vars=None, responses=None, residuals=None, model_path=None, recurse=True,
                include_external_outputs=True, subs=CHAR_SUBS, writer='pyXDSM', show_browser=False,
                add_process_conns=True, show_parallel=True, quiet=False, build_pdf=False,
                output_side=DEFAULT_OUTPUT_SIDE, driver_type='optimization', legend=False,
                class_names=False, equations=False, include_indepvarcomps=True,
                writer_options={}, **kwargs):
    """
    XDSM writer. Components are extracted from the connections of the problem.

    Parameters
    ----------
    filename : str
        Filename (absolute path without extension)
    connections : list[(str, str)]
        Connections list
    driver : str or None, optional
        Driver name
    include_solver:  bool, optional
        Defaults to False.
    cleanup : bool, optional
        Clean-up temporary files after making the diagram.
        Defaults to True.
    design_vars : OrderedDict or None, optional
        Design variables
    responses : OrderedDict or None, optional
        Responses
    model_path : str or None, optional
        Path to the subsystem to be transcribed to XDSM.  If None, use the model root.
    recurse : bool, optional
        If False, treat the top level of each name as the source/target component.
    include_external_outputs : bool, optional
        If True, show externally connected outputs when transcribing a subsystem.
        Defaults to True.
    subs : tuple, optional
       Character pairs to be substituted. Forbidden characters or just for the sake of nicer names.
    writer: str or BaseXDSMWriter, optional
        Writer is either a string ("pyXDSM" or "XDSMjs") or a custom writer.
        Defaults to "pyXDSM".
    show_browser : bool, optional
        If True, pop up a browser to view the generated html file.
        Defaults to False.
    add_process_conns : bool, optional
        Add process connections (thin black lines)
        Defaults to True.
    show_parallel : bool, optional
        Show parallel components with stacked blocks.
        Defaults to True.
    quiet : bool, optional
        Set to True to suppress output from pdflatex. Applicable only for 'tex' or 'pdf' output format.
    build_pdf : bool, optional
        If True and a .tex file is generated, create a .pdf file from the .tex.
        Defaults to False.
    output_side : str or dict(str, str), optional
        Left or right, or a dictionary with component types as keys. Component type key can
        be 'optimization', 'doe' or 'default'.
        Defaults to "left".
    driver_type : str, optional
        Optimization or DOE.
        Defaults to "optimization".
    legend : bool, optional
        If true, it adds a legend to the diagram.
        Defaults to False.
    class_names : bool, optional
        If true, appends class name of the groups/components to the component blocks of the diagram.
        Defaults to False.
    equations : bool, optional
        If true, for ExecComps their equations are shown in the diagram
        Defaults to False.
    include_indepvarcomps : bool, optional
        Include IndepVarComps as system but only as external inputs. If turned off, the XDSM is simpler.
        Defaults to True.
    writer_options : dict, optional
        Options passed to the writer class at initialization.
    **kwargs : dict
        Keyword arguments, includes writer specific options.

    Returns
    -------
        BaseXDSMWriter
    """

    # TODO implement residuals
    # Box appearance
    box_stacking = kwargs.pop('box_stacking', _DEFAULT_BOX_STACKING)
    box_width = kwargs.pop('box_width', _DEFAULT_BOX_WIDTH)
    box_lines = kwargs.pop('box_lines', _MAX_BOX_LINES)
    # In XDSMjs components are numbered by default, so only add for pyXDSM as an option
    add_component_indices = kwargs.pop('numbered_comps', True)
    # Number alignment can be "horizontal" or "vertical"
    number_alignment = kwargs.pop('number_alignment', _DEFAULT_NUMBER_ALIGNMENT)

    error_msg = ('Undefined XDSM writer "{}". '
                 'Provide  a valid name or a BaseXDSMWriter instance.')
    if isinstance(writer, str):  # Standard writers (XDSMjs or pyXDSM)
        if writer.lower() == 'pyxdsm':  # pyXDSM
            x = XDSMWriter(box_stacking=box_stacking,
                           number_alignment=number_alignment,
                           add_component_indices=add_component_indices,
                           legend=legend,
                           class_names=class_names,
                           options=writer_options)
        elif writer.lower() == 'xdsmjs':  # XDSMjs
            x = XDSMjsWriter(options=writer_options)
        else:
            raise ValueError(error_msg.format(writer))
    elif isinstance(writer, BaseXDSMWriter):  # Custom writer
        x = writer
    else:
        raise TypeError(error_msg.format(writer))

    def replace_chars(name):
        # A shorthand for the functions, since within this scope the same always substitutes are used.
        return _replace_chars(name, substitutes=subs)

    def format_block(names, **kwargs):
        # Sets the width, number of lines and other string formatting for a block.
        return x.format_block(names=names, box_width=box_width, box_lines=box_lines, box_stacking=box_stacking,
                              **kwargs)

    def get_output_side(component_name):
        if isinstance(output_side, str):
            return output_side
        elif isinstance(output_side, dict):
            # Gets the specified key, or the default in the dictionary, or the global default
            # if both of them are missing from the dictionary.
            side = output_side.get(component_name, output_side.get('default', DEFAULT_OUTPUT_SIDE))
            return side
        else:
            msg = 'Output side argument should be string or dictionary, instead it is a {}.'
            raise ValueError(msg.format(type(output_side)))

    connections = viewer_data['connections_list']
    tree = viewer_data['tree']

    if driver is not None:
        design_vars2 = _collect_connections(design_vars, recurse=recurse, model_path=model_path,
                                            connection_namer=CONNECTION_NAMING, connections=connections)
        responses2 = _collect_connections(responses, recurse=recurse, model_path=model_path)
    else:
        design_vars2 = {}
        responses2 = {}

    # Get the top level system to be transcripted to XDSM
    comps, filtered_comps = _get_comps(tree, model_path=model_path, recurse=recurse, include_solver=include_solver,
                                       include_indepvarcomps=include_indepvarcomps)
    if include_solver:
        # Add the top level solver
        top_level_solver = dict(tree)
        top_level_solver.update({'comps': list(comps), 'abs_name': 'root@solver', 'index': 0, 'type': 'solver'})
        comps.insert(0, top_level_solver)  # Add top level solver
    comps_dct = {comp['abs_name']: comp for comp in comps if comp['type'] != 'solver'}

    solvers = []  # Solver labels

    conns1, external_inputs1, external_outputs1 = _prune_connections(connections, model_path=model_path)
    conns2 = _process_connections(conns1, recurse=recurse, subs=subs)
    external_inputs2 = _process_connections(external_inputs1, recurse=recurse, subs=subs)
    external_outputs2 = _process_connections(external_outputs1, recurse=recurse, subs=subs)

    if not include_indepvarcomps:  # Reconnect connections
        filtered_comp_names = [c['name'] for c in filtered_comps]

        for src, tgts in conns2.copy().items():
            if src in filtered_comp_names or (src == AUTO_IVC_NAME):
                if src in design_vars2:
                    for tgt in tgts:
                        dv_tgt = design_vars2.setdefault(tgt, [])
                        dv_tgt += design_vars2[src]
                    del design_vars2[src]
                else:  # Make external input from it
                    for tgt in tgts:
                        var_names = conns2[src][tgt]
                        var_names = [x.format_var_str(var, 'initial0') for var in var_names]  # make them initial vals
                        external_inputs2.setdefault(tgt, {}).setdefault(tgt, []).extend(var_names)
                del conns2[src]

    def add_solver(solver_dct):
        # Adds a solver. Uses some vars from the outer scope.
        # Returns True, if it is a non-default linear or nonlinear solver
        comp_names = [_replace_illegal_chars(c['abs_name']) for c in solver_dct['comps']]
        solver_label = _format_solver_str(solver_dct, stacking=box_stacking)

        if isinstance(solver_label, str):
            solver_label = replace_chars(solver_label)
        else:  # It is an iterable
            solver_label = [replace_chars(i) for i in solver_label]
        solver_name = _replace_illegal_chars(solver_dct['abs_name'])

        if solver_label:  # At least one non-default solver (default solvers are ignored)
            # If there is a driver, the start index is increased by one.
            solvers.append(solver_label)
            x.add_solver(name=solver_name, label=solver_label)

            # Add the connections
            for src, dct in conns2.items():
                for tgt, conn_vars in dct.items():
                    formatted_conns = format_block(conn_vars)
                    if (src in comp_names) and (tgt in comp_names):
                        formatted_targets = format_block([x.format_var_str(c, 'target') for c in conn_vars])
                        # From solver to components (targets)
                        x.connect(solver_name, tgt, formatted_targets)
                        # From components to solver
                        x.connect(src, solver_name, formatted_conns)
            return True
        else:
            return False

    if driver is not None:
        driver_label = driver
        driver_name = _replace_illegal_chars(driver)
        x.add_driver(name=driver_name, label=driver_label, driver_type=driver_type.lower())

        # Design variables
        for comp, conn_vars in design_vars2.items():
            # Format var names
            conn_vars = [replace_chars(var) for var in conn_vars]
            # Optimal var names
            opt_con_vars = [x.format_var_str(var, 'optimal') for var in conn_vars]
            # Initial var names
            init_con_vars = [x.format_var_str(var, 'initial') for var in conn_vars]
            # Connection from optimizer
            x.connect(driver_name, comp, label=format_block(conn_vars))
            # Optimal design variables
            x.add_output(comp, label=format_block(opt_con_vars), side=get_output_side('default'))
            x.add_output(driver_name, label=format_block(opt_con_vars), side=get_output_side(driver_type))
            # Initial design variables
            x.add_input(driver_name, label=format_block(init_con_vars))

        # Responses
        for comp, conn_vars in responses2.items():
            # Optimal var names
            conn_vars = [replace_chars(var) for var in conn_vars]
            opt_con_vars = [x.format_var_str(var, 'optimal') for var in conn_vars]
            # Connection to optimizer
            x.connect(comp, driver_name, conn_vars)
            # Optimal output
            x.add_output(comp, format_block(opt_con_vars), side=get_output_side('default'))

    # Add components
    solver_dcts = []
    if equations:
        try:
            # noinspection PyUnresolvedReferences
            from pytexit import py2tex
        except ImportError:
            equations = False
            msg = 'The LaTeX equation formatting requires the pytexit package.' \
                  'The "equations" options was turned off.' \
                  'To enable this option install the package with "pip install pytexit".'
            simple_warning(msg)

    has_auto_ivc = False

    # Add the connections
    for src, dct in conns2.items():
        for tgt, conn_vars in dct.items():
            if src and tgt:
                if src == AUTO_IVC_NAME:
                    has_auto_ivc = True
                # Because Auto-IVC not in comps, it has to be skipped
                src_parallel = comps_dct[src]['is_parallel'] if src in comps_dct else False
                stack = show_parallel and (src_parallel or comps_dct[tgt]['is_parallel'])
                x.connect(src, tgt, label=format_block(conn_vars), stack=stack)
            else:  # Source or target missing
                msg = 'Connection "{conn}" from "{src}" to "{tgt}" ignored.'
                simple_warning(msg.format(src=src, tgt=tgt, conn=conn_vars))

    if has_auto_ivc:
        auto_ivc_comp = OrderedDict(name=AUTO_IVC_NAME, stack=False, type="subsystem", expressions=None,
                                    is_parallel=False, component_type=None, subsystem_type='component')
        auto_ivc_comp["class"] = "IndepVarComp"
        auto_ivc_comp["abs_name"] = auto_ivc_comp["name"]
        if include_indepvarcomps:
            comps.insert(0, auto_ivc_comp)  # Auto-IVC added as the first component
        else:
            filtered_comps.insert(0, auto_ivc_comp)  # Auto-IVC added as the first filtered component (not on the XDSM)

    for comp in comps:  # Driver is 1, so starting from 2
        # The second condition is for backwards compatibility with older data.
        if equations and comp.get('expressions', None) is not None:
            # One of the $ signs has to be removed to correctly parse it
            if isinstance(x, XDSMWriter):
                def parse(expr):
                    # TODO add curly brackets to support multiple digit index
                    for (ch, rep) in (('$$', '$'), (r'[', '_'), (r']', '')):  # brackets converted to lower index
                        expr = expr.replace(ch, rep)
                    # One of the $ signs has to be removed to correctly parse it
                    return py2tex(expr).replace('$$', '$')

                expression = comp['expressions']
                try:
                    label = ', '.join(map(parse, expression))
                except TypeError:
                    label = replace_chars(comp['name'])
                    simple_warning('Could not parse "{}"'.format(expression))
            else:
                msg = 'The "equations" option is available only with pyXDSM. Set the output ' \
                      'format to "tex" or "pdf" to enable this option.'
                simple_warning(msg)
                label = replace_chars(comp['name'])
        else:
            label = replace_chars(comp['name'])
        stack = show_parallel and comp['is_parallel']
        if include_solver and comp['type'] == 'solver':  # solver
            if add_solver(comp):  # Return value is true, if solver is not the default
                # If not default solver, add to the solver dictionary
                solver_dcts.append(comp)
        else:  # component or group
            cls_name = comp.get('class', None) if class_names else None
            comp_type = comp['component_type']
            if comp.get('subsystem_type', None) == 'group':
                comp_type = 'group'
            x.add_comp(name=comp['abs_name'], label=label, stack=stack,
                       comp_type=comp_type, cls=cls_name)

    # Add process connections
    if add_process_conns:
        if driver is not None:
            x.add_workflow()  # Driver workflow
        for s in solver_dcts:
            x.add_workflow(s)  # Solver workflows

    # Add the externally sourced inputs
    for src, tgts in external_inputs2.items():
        for tgt, conn_vars in tgts.items():
            formatted_conn_vars = map(replace_chars, conn_vars)
            if tgt:
                stack = show_parallel and comps_dct[tgt]['is_parallel']
                x.add_input(tgt, format_block(formatted_conn_vars), stack=stack)
            else:  # Target missing
                msg = 'External input to "{tgt}" ignored.'
                simple_warning(msg.format(tgt=tgt, conn=conn_vars))

    # Add the externally connected outputs
    if include_external_outputs:
        for src, tgts in external_outputs2.items():
            output_vars = set()
            for tgt, conn_vars in tgts.items():
                output_vars |= set(conn_vars)
            formatted_outputs = map(replace_chars, output_vars)
            if src:
                stack = show_parallel and comps_dct[src]['is_parallel']
                x.add_output(src, formatted_outputs, side='right', stack=stack)
            else:  # Source or target missing
                msg = 'External output "{conn}" from "{src}" ignored.'
                simple_warning(msg.format(src=src, conn=output_vars))

    x.write(filename, cleanup=cleanup, quiet=quiet, build=build_pdf, **kwargs)

    if show_browser and (build_pdf or x.name == 'xdsmjs'):
        # path will be specified based on the "out_format", if all required inputs where
        # provided for showing the results.
        import webbrowser
        import sys
        import os
        ext = x.extension
        if not isinstance(ext, str):
            err_msg = '"{}" is an invalid extension.'
            raise ValueError(err_msg.format(writer))
        path = filename + '.' + ext
        if sys.platform == 'darwin':
            os.system('open {}'.format(path))
        else:
            webbrowser.get().open(path)

    return x  # Returns the writer instance


def _residual_str(name):
    """Make a residual symbol."""
    return '\\mathcal{R}(%s)' % name


def _process_connections(conns, recurse=True, subs=None):
    """
    Extracts information from the source and target paths.

    For each source and target returns the owner component (comp), variable name (var), absolute name and path.

    Parameters
    ----------
    conns : list(dict(str, str))
        List of source target pairs.
    recurse : bool, optional
    subs : list(tuple) or None, optional
        Character substitutes.
        Defaults to None.

    Returns
    -------
        list(dict(str, dict))
    """
    def convert(x):
        return _convert_name(x, recurse=recurse, subs=subs)

    conns_new = [{k: convert(v) for k, v in conn.items() if k in ('src', 'tgt')} for conn in conns]
    return _accumulate_connections(conns_new, connection_namer=CONNECTION_NAMING)


def _accumulate_connections(conns, connection_namer='mixed'):
    """
    Makes a dictionary with source and target components and with the connection sources.

    Returns a dictionary, where the keys are the source components, and the values are dictionaries of target components
    and the connection names.

    Example::

        {'source_comp1': {'target_comp1': ['var1', 'var2']}}

    Parameters
    ----------
    conns : list
        Connections.
    connection_namer : str, optional
        Defaults to "mixed", where in case of Auto-IVC the target names are used, otherwise the source names.
        Other valid options are

    Returns
    -------
        dict(str, dict)
    """
    name_type = 'path'
    conns_new = dict()
    for conn in conns:  # list
        src_comp = conn['src'][name_type]
        tgt_comp = conn['tgt'][name_type]
        if src_comp == tgt_comp:
            # When recurse is False, ignore connections within the same subsystem.
            continue
        # From which component the connection get its name
        if connection_namer == "both":
            var = f"{conn['src']['var']}-{conn['tgt']['var']}"
        elif connection_namer == "mixed":
            namer = 'src' if src_comp != AUTO_IVC_NAME else 'tgt'
            var = conn[namer]['var']
        else:
            var = conn[connection_namer]['var']
        conns_new.setdefault(src_comp, {})
        if var not in conns_new[src_comp].setdefault(tgt_comp, []):  # Avoid duplicates
            conns_new[src_comp][tgt_comp].append(var)
    return conns_new


def _collect_connections(variables, recurse, model_path=None, connections=None, connection_namer='src'):
    """
    Collect connections of components.

    Parameters
    ----------
    variables : OrderedDict(str, OrderedDict)
        Info on connections, keys are source absolute path names.
    recurse : bool
    model_path : str or None, optional
        Defaults to None.
    connections : list(dict) or None, optional
        Connections. Only used if connection_namer is not 'src'
    connection_namer : str, optional
        Defaults to 'src'. Other valid options are 'tgt' or 'mixed' ('tgt' used only for Auto-IVC)

    Returns
    -------
        dict(str, list)
    """

    conv_vars = [_convert_name(v, recurse) for v in variables]
    if connection_namer != 'src':
        tgt_vars = {_convert_name(c['src'], recurse)['abs_name']: _convert_name(c['tgt'], recurse)
                    for c in connections if c['src'] in variables}
    connections = dict()  # Initialize
    for conv_var in conv_vars:
        path = _make_rel_path(conv_var['path'], model_path=model_path)
        if connection_namer == 'src':
            var_name = conv_var['var']
        elif connection_namer == 'tgt':
            var_name = tgt_vars[conv_var['abs_name']]['var']
        elif connection_namer == 'mixed':
            if conv_var['comp'].replace('_', '@') == AUTO_IVC_NAME:
                var_name = tgt_vars[conv_var['abs_name']]['var']
            else:
                var_name = conv_var['var']
        else:
            raise ValueError(f'Invalid connection namer "{connection_namer}", choose from "src", "tgt" or "mixed"')
        connections.setdefault(path, []).append(var_name)
    return connections