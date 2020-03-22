.. _xdsm_generation:

***************
XDSM generation
***************

OpenMDAO also supports the generation of XDSM diagrams of models. For more information about XDSM diagrams see XDSM_Overview_.

.. _XDSM_Overview: http://mdolab.engin.umich.edu/content/xdsm-overview

The diagrams can be in the form of HTML or LaTeX files.

To use the feature which generates LaTeX (`tex`) files, you will need to install pyXDSM. This can be done as follows:

::

    pip install git+https://github.com/mdolab/pyXDSM

or:

::

    git clone https://github.com/mdolab/pyXDSM
    cd pyXDSM
    python setup.py install

To generate PDF files you must also have LaTeX on your system, specifically the `pdflatex` command.


You can generate XDSM files either from the command line or from a script.

From the Command Line
---------------------

.. _om-command-view_xdsm:

Generating an XDSM diagram for a model from the command line is easy. First, you need a Python
script that runs the model or a case recording file that was created when running the model.

.. note::

    If :code:`final_setup` isn't called in the script (either directly or as a result
    of :code:`run_model`
    or :code:`run_driver`) then nothing will happen. Also, when using the command line version,
    even if the script does call :code:`run_model` or :code:`run_driver`,
    the script will terminate after :code:`final_setup` and will not actually run the model.

The :code:`openmdao xdsm` command will generate an XDSM diagram of the model that is
viewable in a browser, for example:

::

    openmdao xdsm omxdsm/examples/circuit_with_unconnected_input.py

will generate an XDSM diagram like the one below.


.. raw:: html
    :file: examples/xdsm_circuit_with_unconnected_input.html

The :code:`openmdao xdsm` command has many options:

::

    openmdao xdsm -h

::

    usage: openmdao xdsm [-h] [-o OUTFILE] [-f {html,pdf,tex}] [-m MODEL_PATH] [-r] [--no_browser] [--no_parallel] [--no_ext] [-s] [--no_process_conns] [--box_stacking {max_chars,vertical,horizontal,cut_chars,empty}] [--box_width BOX_WIDTH] [--box_lines BOX_LINES] [--numbered_comps]
                         [--number_alignment {horizontal,vertical}] [--output_side OUTPUT_SIDE] [--legend] [--class_names] [--equations] [--no_indepvarcomps]
                         file

    positional arguments:
      file                  Python script or recording containing the model.

    optional arguments:
      -h, --help            show this help message and exit
      -o OUTFILE, --outfile OUTFILE
                            XDSM output file. (use pathname without extension)
      -f {html,pdf,tex}, --format {html,pdf,tex}
                            format of XSDM output.
      -m MODEL_PATH, --model_path MODEL_PATH
                            Path to system to transcribe to XDSM.
      -r, --recurse         Don't treat the top level of each name as the source/target component.
      --no_browser          Don't display in a browser.
      --no_parallel         don't show stacked parallel blocks. Only active for 'pdf' and 'tex' formats.
      --no_ext              Don't show externally connected outputs.
      -s, --include_solver  Include the problem model's solver in the XDSM.
      --no_process_conns    Don't add process connections (thin black lines).
      --box_stacking {max_chars,vertical,horizontal,cut_chars,empty}
                            Controls the appearance of boxes.
      --box_width BOX_WIDTH
                            Controls the width of boxes.
      --box_lines BOX_LINES
                            Limits number of vertical lines in box if box_stacking is vertical.
      --numbered_comps      Display components with numbers. Only active for 'pdf' and 'tex' formats.
      --number_alignment {horizontal,vertical}
                            Positions the number either above or in front of the component label if numbered_comps is true.
      --output_side OUTPUT_SIDE
                            Position of the outputs on the diagram. Left or right, or a dictionary with component types as keys. Component type key can be "optimization", "doe" or "default".
      --legend              If True, show legend.
      --class_names         If true, appends class name of the groups/components to the component blocks of the diagram.
      --equations           If true, for ExecComps their equations are shown in the diagram.
      --no_indepvarcomps    Don't include IndepVarComps as system but only as inputs.


From a Script
-------------

.. _script_view_xdsm:

You can do the same thing programmatically by calling the :code:`write_xdsm` function. The options are
detailed in the docstring of the function.

Notice that the data source can be either a :code:`Problem` containing the model or
or a case recorder database containing the model data. The latter is indicated by a string
giving the file path to the case recorder file.

Here are some code snippets showing the two cases.

Problem as Data Source
**********************

.. code:: python

    p.setup()
    p.run_model()

    import openmdao.api as om
    om.write_xdsm(p, 'xdsmjs_circuit', out_format='html', show_browser=False)


Case Recorder as Data Source
****************************

.. code:: python

    r = SqliteRecorder('circuit.sqlite')
    p.driver.add_recorder(r)

    p.setup()
    p.final_setup()
    r.shutdown()

    import openmdao.api as om
    om.write_xdsm('circuit.sqlite', 'xdsmjs_circuit', out_format='html', show_browser=False)


In the latter case, you could view the XDSM diagram at a later time using the command:

::

    openmdao xdsm circuit.sqlite
