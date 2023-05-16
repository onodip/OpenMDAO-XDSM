"""
A console script wrapper for OpenMDAO-XDSM.
"""
from __future__ import print_function

import openmdao.utils.hooks as hooks
from openmdao.utils.file_utils import _load_and_exec, _to_filename  # TODO private methods

from omxdsm.settings import DEFAULT_OUTPUT_SIDE, CHAR_SUBS
from omxdsm.xdsm_writer import write_xdsm, \
    _DEFAULT_BOX_STACKING, _DEFAULT_BOX_WIDTH, _MAX_BOX_LINES


def _xdsm_setup_parser(parser):
    """
    Set up the OpenMDAO subparser for the 'openmdao xdsm' command.

    Parameters
    ----------
    parser : argparse subparser
        The parser we're adding options to.
    """
    parser.add_argument('file', nargs=1, help='Python script or recording containing the model.')
    parser.add_argument('-o', '--outfile', default='xdsm_out', action='store', dest='outfile',
                        help='XDSM output file. (use pathname without extension)')
    parser.add_argument('-f', '--format', default='html', action='store', dest='format',
                        choices=['html', 'pdf', 'tex'], help='format of XSDM output.')
    parser.add_argument('-m', '--model_path', action='store', dest='model_path',
                        help='Path to system to transcribe to XDSM.')
    parser.add_argument('-r', '--recurse', action='store_true', dest='recurse',
                        help="Don't treat the top level of each name as the source/target "
                             "component.")
    parser.add_argument('--no_browser', action='store_true', dest='no_browser',
                        help="Don't display in a browser.")
    parser.add_argument('--no_parallel', action='store_true', dest='no_parallel',
                        help="don't show stacked parallel blocks. Only active for 'pdf' and 'tex' "
                             "formats.")
    parser.add_argument('--no_ext', action='store_true', dest='no_extern_outputs',
                        help="Don't show externally connected outputs.")
    parser.add_argument('-s', '--include_solver', action='store_true', dest='include_solver',
                        help="Include the problem model's solver in the XDSM.")
    parser.add_argument('--no_process_conns', action='store_true', dest='no_process_conns',
                        help="Don't add process connections (thin black lines).")
    parser.add_argument('--box_stacking', action='store', default=_DEFAULT_BOX_STACKING,
                        choices=['max_chars', 'vertical', 'horizontal', 'cut_chars', 'empty'],
                        dest='box_stacking', help='Controls the appearance of boxes.')
    parser.add_argument('--box_width', action='store', default=_DEFAULT_BOX_WIDTH,
                        dest='box_width', type=int, help='Controls the width of boxes.')
    parser.add_argument('--box_lines', action='store', default=_MAX_BOX_LINES,
                        dest='box_lines', type=int,
                        help='Limits number of vertical lines in box if box_stacking is vertical.')
    parser.add_argument('--numbered_comps', action='store_true', dest='numbered_comps',
                        help="Display components with numbers.  Only active for 'pdf' and 'tex' "
                        "formats.")
    parser.add_argument('--number_alignment', action='store', dest='number_alignment',
                        choices=['horizontal', 'vertical'], default='horizontal',
                        help='Positions the number either above or in front of the component label '
                        'if numbered_comps is true.')
    parser.add_argument('--output_side', action='store', dest='output_side',
                        default=DEFAULT_OUTPUT_SIDE,
                        help='Position of the outputs on the diagram. Left or right, or a '
                             'dictionary with component types as keys. Component type key can be '
                             '"optimization", "doe" or "default".')
    parser.add_argument('--legend', action='store_true', dest='legend',
                        help='If True, show legend.')
    parser.add_argument('--class_names', action='store_true', dest='class_names',
                        help='If true, appends class name of the groups/components to the '
                             'component blocks of the diagram.')
    parser.add_argument('--equations', action='store_true', dest='equations',
                        help='If true, for ExecComps their equations are shown in the diagram.')
    parser.add_argument('--no_indepvarcomps', action='store_true', dest='no_indepvarcomps',
                        help="Don't include IndepVarComps as system but only as inputs.")


def _xdsm_cmd(options, user_args):
    """
    Process command line args and call xdsm on the specified file.

    Parameters
    ----------
    options : argparse Namespace
        Command line options.
    user_args : list of str
        Command line options after '--' (if any).  Passed to user script.
    """
    filename = _to_filename(options.file[0])

    kwargs = {}
    for name in ['box_stacking', 'box_width', 'box_lines', 'numbered_comps', 'number_alignment']:
        val = getattr(options, name)
        if val is not None:
            kwargs[name] = val

    if filename.endswith('.py'):
        # the file is a python script, run as a post_setup hook
        def _xdsm(prob):
            write_xdsm(prob, filename=options.outfile, model_path=options.model_path,
                       recurse=options.recurse,
                       include_external_outputs=not options.no_extern_outputs,
                       out_format=options.format,
                       include_solver=options.include_solver, subs=CHAR_SUBS,
                       show_browser=not options.no_browser, show_parallel=not options.no_parallel,
                       add_process_conns=not options.no_process_conns,
                       output_side=options.output_side,
                       legend=options.legend,
                       class_names=options.class_names,
                       equations=options.equations,
                       include_indepvarcomps=not options.no_indepvarcomps,
                       **kwargs)
            exit()

        hooks._register_hook('setup', 'Problem', post=_xdsm)

        _load_and_exec(options.file[0], user_args)
    else:
        # assume the file is a recording, run standalone
        write_xdsm(options.file[0], filename=options.outfile, model_path=options.model_path,
                   recurse=options.recurse,
                   include_external_outputs=not options.no_extern_outputs,
                   out_format=options.format,
                   include_solver=options.include_solver, subs=CHAR_SUBS,
                   show_browser=not options.no_browser, show_parallel=not options.no_parallel,
                   add_process_conns=not options.no_process_conns, output_side=options.output_side,
                   legend=options.legend,
                   class_names=options.class_names,
                   equations=options.equations,
                   **kwargs)


def _xdsm_setup():
    """
    This command prints a hello message after final setup.
    """
    return _xdsm_setup_parser, _xdsm_cmd, 'Generate an XDSM diagram of a model.'
