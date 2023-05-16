# Writer is chosen based on the output format
OUT_FORMATS = {'tex': 'pyxdsm', 'pdf': 'pyxdsm', 'json': 'xdsmjs', 'html': 'xdsmjs'}

# Variable formatting settings.
# Last item (initial0) is used to pass the character substitution  step without changes in the string.
# This string won't appear on the XDSM. Variable names should not contain this substring.
SUPERSCRIPTS = {'optimal': '*', 'initial': '(0)', 'target': 't', 'consistency': 'c', 'initial0': '#INIT#'}

# Character substitutions in labels
# pyXDSM:
# Interpreted as TeX syntax
# Underscore is replaced with a skipped underscore
# Round parenthesis is replaced with subscript syntax, e.g. x(1) --> x_{1}
CHAR_SUBS = {
    'pyxdsm': (
        ('_', r'\_'),
        ('(', '_{'),
        (')', '}'),
        ('@', r'\_'),
        (SUPERSCRIPTS['initial0'], SUPERSCRIPTS['initial'])
    ),
    'xdsmjs': (
        (' ', '-'),
        (':', ''),
        ('_', r'\_'),
        ('@', '_'),
        (SUPERSCRIPTS['initial0'], SUPERSCRIPTS['initial'])
    ),
}
AUTO_IVC_NAME = '@auto@ivc'
CONNECTION_NAMING = 'mixed'  # Auto-IVC connections inherit the name from the target, if it is set to 'mixed'

# Default solver names in OpenMDAO, when no solver is assigned to a system.
DEFAULT_SOLVER_NAMES = {'linear': 'LN: RUNONCE', 'nonlinear': 'NL: RUNONCE'}
# On which side to place outputs? One of "left", "right"
DEFAULT_OUTPUT_SIDE = 'left'
# Default writer, this will be used if settings are not found for a custom writer
DEFAULT_WRITER = 'pyxdsm'

# Maps OpenMDAO component types with the available block styling options in the writer.
# For pyXDSM check the "diagram_styles" file for style definitions.
# For XDSMjs check the CSS style sheets.
# 'indep' is used only if include_indepvarcomps is turned on.
COMPONENT_TYPE_MAP = {
    'pyxdsm': {  # Newest release
        'indep': 'Function',
        'explicit': 'Function',
        'implicit': 'ImplicitFunction',
        'exec': 'Function',
        'metamodel': 'Metamodel',
        'group': 'Group',
        'implicit_group': 'ImplicitGroup',
        'optimization': 'Optimization',
        'doe': 'DOE',
        'solver': 'MDA',
    },
    'pyxdsm 1.0': {  # Legacy color scheme
        'indep': 'Function',
        'explicit': 'Function',
        'implicit': 'ImplicitAnalysis',
        'exec': 'Function',
        'metamodel': 'Metamodel',
        'group': 'Function',
        'implicit_group': 'ImplicitAnalysis',
        'optimization': 'Optimization',
        'doe': 'DOE',
        'solver': 'MDA',
    },
    'xdsmjs': {
        'indep': 'function',
        'explicit': 'function',
        'implicit': 'analysis',
        'exec': 'function',
        'metamodel': 'metamodel',
        'group': 'function',
        'implicit_group': 'analysis',
        'optimization': 'optimization',
        'doe': 'doe',
        'solver': 'mda',
    }
}