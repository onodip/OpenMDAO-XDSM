_DEFAULT_SOLVER_NAMES = {'linear': 'LN: RUNONCE', 'nonlinear': 'NL: RUNONCE'}  # TODO duplicate


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
        if solver_name != _DEFAULT_SOLVER_NAMES[solver_type]:  # Not default solver found
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