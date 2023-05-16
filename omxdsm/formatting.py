"""
Common text formatting utilities.
"""
from settings import DEFAULT_SOLVER_NAMES


def _replace_chars(name, substitutes):
    """
    Replace characters in `name` with the substitute characters.

    If some characters are both to be replaced or other characters are replaced with them
    (e.g.: ? -> !, ! ->#), than it is not safe to give a dictionary as the `substitutes`
    (because it is unordered).

    .. warning::

       Order matters, because otherwise some characters could be replaced more than once.

    Parameters
    ----------
    name : str
        Name
    substitutes: tuple or None
        Character pairs with old and substitute characters

    Returns
    -------
       str
    """
    if substitutes:
        for k, v in substitutes:
            name = name.replace(k, v)
    return name


def _format_solver_str(dct, stacking='horizontal', solver_types=('nonlinear', 'linear')):
    """
    Format solver string.

    Parameters
    ----------
    dct : dict
        Dictionary, which contains keys for the solver names
    stacking : str
        Box stacking
    solver_types : tuple(str)
        Solver types, e.g. "linear"

    Returns
    -------
        str
    """
    stacking = stacking.lower()

    solvers = []
    for solver_type in solver_types:  # loop through all solver types
        solver_name = dct['{}_solver'.format(solver_type)]
        if solver_name != DEFAULT_SOLVER_NAMES[solver_type]:  # Not default solver found
            solvers.append(solver_name)
    if stacking == 'vertical':
        # Make multiline comp if not numbered
        return _multiline_block(*solvers)
    elif stacking in ('horizontal', 'max_chars', 'cut_chars'):
        return ' '.join(solvers)
    else:
        msg = ('Invalid stacking "{}". Choose from: "vertical", "horizontal", "max_chars", '
               '"cut_chars"')
        raise ValueError(msg.format(stacking))


def _multiline_block(*texts, **kwargs):
    """
    Make a string for a multiline block.

    A string is returned, if there would be only 1 line.

    texts : iterable(str)
        Text strings, each will go to new line
    **kwargs : dict
        Unused keywords are ignored.
        "end_char" is the separator at the end of line. Defaults to '' (no separator).

    Returns
    -------
       list(str) or str
    """
    end_char = kwargs.pop('end_char', '')
    out_txts = [_textify(t + end_char) for t in texts]
    if len(out_txts) == 1:
        out_txts = out_txts[0]
    return out_txts


def _textify(name):
    # Uses the LaTeX \text{} command to insert plain text in math mode
    return r'\text{{{}}}'.format(name)


def _replace_illegal_chars(name, illegal_cars=('.', ' ', '-', '_', ':')):
    # Replaces illegal characters in names for pyXDSM component and connection names
    # This does not affect the labels, only reference names in TikZ
    if isinstance(name, str):
        for char in illegal_cars:
            name = name.replace(char, '@')
    return name


def _convert_name(name, recurse=True, subs=None):
    """
    From an absolute path returns the variable name and its owner component in a dict.

    Names are also formatted.

    Parameters
    ----------
    name : str or list(str)
        Connection absolute path and name
    recurse : bool
        If False, treat the top level of each name as the source/target component.
    subs: tuple or None
        Character pairs with old and substitute characters

    Returns
    -------
        dict(str, str)
    """
    def convert(abs_name):
        sep = '.'
        abs_name = abs_name.replace('@', sep)
        name_items = abs_name.split(sep)
        if recurse:
            if len(name_items) > 1:
                comp = name_items[-2]  # -1 is variable name, before that -2 is the component name
                path = _get_path(abs_name, sep=sep)
            else:
                msg = ('The name "{}" cannot be processed. The separator character is "{}", '
                       'which does not occur in the name.')
                raise ValueError(msg.format(abs_name, sep))
        else:
            comp = name_items[0]
            path = comp
        var = name_items[-1]
        var = _replace_chars(var, substitutes=subs)
        return {'comp': comp, 'var': var,
                'abs_name': _replace_illegal_chars(abs_name), 'path': _replace_illegal_chars(path)}

    if isinstance(name, list):  # If a source has multiple targets
        return map(convert, name)
    else:  # string
        return convert(name)


def _get_path(name, sep='.'):
    # Returns path until the last separator in the name
    return name.rsplit(sep, 1)[0]


def _make_rel_path(full_path, model_path, sep='.'):
    # Path will be cut from this character. Length of model path + separator after it.
    # If path does not contain the model path, the full path will be returned.
    if model_path is not None:
        path = model_path + sep  # Add separator character
        first_char = len(path)
        if full_path.startswith(path):
            return full_path[first_char:]
    return full_path  # No model path, so return the original
