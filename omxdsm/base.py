from omxdsm.settings import SUPERSCRIPTS, DEFAULT_OUTPUT_SIDE


class BaseXDSMWriter(object):
    """
    All XDSM writers have to inherit from this base class.

    Attributes
    ----------
    name : str
        Name of XDSM writer.
    extension : str
        Output file saved with this extension.
    type_map : str
        XDSM component type.
    """

    def __init__(self, name, options={}):
        """
        Initialize.

        Parameters
        ----------
        name : str
            Name of this XDSM writer
        options : dict
            Writer options.
        """
        self.name = name
        # This should be a dictionary mapping OpenMDAO system types to XDSM component types.
        # See for example any value in _COMPONENT_TYPE_MAP
        self.type_map = None
        self.extension = None  # Implement in child class as string file extension


class AbstractXDSMWriter(BaseXDSMWriter):
    """
    Abstract class to define methods for XDSM writers.

    All methods should be implemented in child classes.

    Attributes
    ----------
    comps : list of dicts
        List of systems where the list items are dicts indicating type, id, and name.
    connections : list of dicts
        List of connections where the list items are dicts indicating 'to', 'from', 'name' of edge.
    processes : list
        List of process.
    """

    def __init__(self, name='abstract_xdsm_writer'):
        """
        Initialize.

        Parameters
        ----------
        name : str
            Name of XDSM writer.
        """
        super(AbstractXDSMWriter, self).__init__(name=name)
        self.comps = []
        self.connections = []
        self.processes = []

    def add_solver(self, label, name='solver', **kwargs):
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
        pass  # Implement in child class

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
        pass  # Implement in child class

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
        pass  # Implement in child class

    def add_input(self, name, label, style='DataIO', stack=False):
        """
        Add input connection.

        Parameters
        ----------
        name : str
            Target name.
        label : str
            Label for connection.
        style : str
            Formatting style.
        stack : bool
            True for parallel.
            Defaults to False.
        """
        pass  # Implement in child class

    def add_output(self, name, label, style='DataIO', stack=False, side=DEFAULT_OUTPUT_SIDE):
        """
        Add output connection.

        Parameters
        ----------
        name : str
            Target name.
        label : str
            Label for connection.
        style : str
            Formatting style.
        stack : bool
            True for parallel.
            Defaults to False.
        side : str
            Location of output, either 'left' or 'right'.
        """
        pass  # Implement in child class

    def add_process(self, systems, arrow=True):
        """
        Add process.

        Parameters
        ----------
        systems : list
            List of systems.
        arrow : bool
            Show process arrow.
        """
        pass  # Implement in child class

    @staticmethod
    def format_block(names, **kwargs):
        """
        Reimplement this method to format the names in a data block.

        Parameters
        ----------
        names : list
            List of items in the block
        **kwargs : dict
            Keyword arguments.

        Returns
        -------
            list(str)
        """
        return names

    @staticmethod
    def format_var_str(name, var_type, superscripts=None):
        """
        Format a variable name to include a superscript for the variable type.

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
        return '{}^{}'.format(name, sup)

    @staticmethod
    def _make_loop_str(first, last, start_index=0):
        # Implement, so number is formatted as follows: start, end --> next
        # Where start = first + start_index, end = last + start_index, next = start + 1
        return ''