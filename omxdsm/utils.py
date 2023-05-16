from omxdsm.formatting import _replace_illegal_chars, _make_rel_path
from omxdsm.settings import DEFAULT_SOLVER_NAMES


def _prune_connections(conns, model_path=None, sep='.'):
    """
    Remove connections that don't involve components within model.

    Parameters
    ----------
    conns : list
        A list of connections from viewer_data
    model_path : str or None, optional
        The path in model to the system to be transcribed to XDSM.
        Defaults to None.
    sep : str, optional
        Separator character.
        Defaults to '.'.

    Returns
    -------
    internal_conns : list(dict)
        A list of the connections with sources and targets inside the given model path.
    external_inputs : list(dict)
        A list of the connections where the target is inside the model path but is connected
        to an external source.
    external_outputs : list(dict)
        A list of the connections where the source is inside the model path but is connected
        to an external target.

    """
    external_inputs = []
    external_outputs = []

    if model_path is None:
        return conns, external_inputs, external_outputs
    else:
        internal_conns = []

        path = model_path + sep  # Add separator character
        for conn in conns:
            src = conn['src']
            src_path = _make_rel_path(src, model_path=model_path)
            tgt = conn['tgt']
            tgt_path = _make_rel_path(tgt, model_path=model_path)
            conn_dct = {'src': src_path, 'tgt': tgt_path}

            if src.startswith(path):
                if tgt.startswith(path):
                    internal_conns.append(conn_dct)  # Internal connections
                else:
                    external_outputs.append(conn_dct)  # Externally connected output
            elif tgt.startswith(path):
                external_inputs.append(conn_dct)  # Externally connected input
        return internal_conns, external_inputs, external_outputs


def _get_comps(tree, model_path=None, recurse=True, include_solver=False, include_indepvarcomps=True):
    """
    Return the components in the tree, optionally only those within the given model_path.

    It also includes the solvers of the subsystems, if "include_solver" is True and not the
    default solvers are assigned to the subsystems.

    Parameters
    ----------
    tree : list(OrderedDict)
        The model tree as returned by viewer_data.
    model_path : str or None
        The path of the model within the tree to be transcribed to XDSM. If None, transcribe
        the entire tree.
    recurse : bool
        If True, return individual components within the model_path.  If False, treat
        Groups as black-box components and don't show their internal components.
    include_solver : bool, optional
        Defaults to False.
    include_indepvarcomps : bool, optional
         Defaults to True.

    Returns
    -------
    components : list
        A list of the components within the model_path in tree.  If recurse is False, this
        list may contain groups. If "include_solver" is True, it may include solvers.

    """
    # Components are ordered in the tree, so they can be collected by walking through the tree.
    components = list()  # Components will be collected to this list
    comp_names = set()  # To check if names are unique
    sep = '.'

    def get_children(tree_branch, path=''):
        local_comps = []

        for ch in tree_branch['children']:
            ch['path'] = path
            name = ch['name']
            if path:
                ch['abs_name'] = _replace_illegal_chars(sep.join([path, name]))
            else:
                ch['abs_name'] = _replace_illegal_chars(name)
            ch['rel_name'] = name
            if ch['subsystem_type'] == 'component':
                if name in comp_names:  # There is already a component with the same name
                    ch['name'] = sep.join([path, name])  # Replace with absolute name
                    for comp in components:
                        if comp['name'] == name:  # replace in the other component to abs. name
                            comp['name'] = sep.join([comp['path'], name])
                components.append(ch)
                comp_names.add(ch['rel_name'])
                local_comps.append(ch)
            else:  # Group
                # Add a solver to the component list, if this group has a linear or nonlinear
                # solver.
                has_solver = False
                if include_solver:
                    solver_names = []
                    solver_dct = {}
                    for solver_typ, default_solver in DEFAULT_SOLVER_NAMES.items():
                        k = '{}_solver'.format(solver_typ)
                        if ch[k] != default_solver:
                            solver_names.append(ch[k])
                            has_solver = True
                        solver_dct[k] = ch[k]
                    if has_solver:
                        i_solver = len(components)
                        name_str = ch['abs_name'] + '@solver'
                        # "comps" will be filled later
                        solver = {'abs_name': _replace_illegal_chars(name_str), 'rel_name': solver_names,
                                  'type': 'solver', 'name': name_str, 'is_parallel': False,
                                  'component_type': 'MDA', 'index': i_solver}
                        solver.update(solver_dct)
                        components.append(solver)
                        comp_names.add(name_str)
                # Add the group or components in the group
                if recurse:  # it is not a component and recurse is True
                    if path:
                        new_path = sep.join([path, ch['name']])
                    else:
                        new_path = ch['name']
                    local_comps = get_children(ch, new_path)
                else:
                    components.append(ch)
                    comp_names.add(ch['rel_name'])
                    local_comps = [ch]
                # Add to the solver, which components are in its loop.
                if include_solver and has_solver:
                    components[i_solver]['comps'] = local_comps
                    local_comps = []
        return list(local_comps)

    top_level_tree = tree
    if model_path is not None:
        path_list = model_path.split(sep)
        while path_list:
            next_path = path_list.pop(0)
            children = [child for child in top_level_tree['children']]
            top_level_tree = [c for c in children if c['name'] == next_path][0]

    get_children(top_level_tree)

    comps_filtered = []
    if not include_indepvarcomps:  # Filter out IndepVarComps
        comps_out = []
        for c in components:
            if c['component_type'] != 'indep':
                comps_out.append(c)
            else:
                comps_filtered.append(c)
        return comps_out, comps_filtered
    else:
        return components, comps_filtered
