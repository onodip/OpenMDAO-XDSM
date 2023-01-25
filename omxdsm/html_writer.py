"""
HTML file writing to create standalone XDSMjs output file.
"""

import xdsmjs

try:  # This should work until OpenMDAO 3.20
    from openmdao.visualization.html_utils import (
        write_div,
        head_and_body,
        write_script,
        write_style,
    )
except ModuleNotFoundError:  # They are imported directly if the OpenMDAO import fails
    from omxdsm.html_utils import (
        write_div,
        head_and_body,
        write_script,
        write_style,
    )


def write_html(
    outfile, source_data=None, data_file=None, embeddable=False, char_set="utf-8"
):
    """
    Write XDSMjs HTML output file, with style and script files embedded.

    The source data can be the name of a JSON file or a dictionary.
    If a JSON file name is provided, the file will be referenced in the HTML.
    If the input is a dictionary, it will be embedded.

    If both data file and source data are given, data file is

    Parameters
    ----------
    outfile : str
        Output HTML file
    source_data : str or dict or None
        XDSM data in a dictionary or string
    data_file : str or None
        Output HTML file
    embeddable : bool, optional
        If True, gives a single HTML file that doesn't have the <html>, <DOCTYPE>, <body>
        and <head> tags. If False, gives a single, standalone HTML file for viewing.
    char_set : str, optional
        HTML character set.
    """
    code = xdsmjs.bundlejs()
    xdsm_bundle = write_script(code, {"type": "text/javascript"})

    init = """
      document.addEventListener('DOMContentLoaded', function() {
      xdsmjs.XDSMjs().createXdsm();
    });
    """
    xdsm_init = write_script(init, {"type": "text/javascript"})

    xdsm_attrs = {"class": "xdsm2"}
    # grab the data
    if data_file is not None:
        # Add name of the data file
        xdsm_attrs["data-mdo-file"] = data_file
    elif source_data is not None:
        if isinstance(source_data, (dict, str)):
            data_str = str(source_data)  # dictionary converted to string
        else:
            msg = (
                "Invalid data type for source data: {} \n"
                "The source data should be a JSON file name or a dictionary."
            )
            raise ValueError(msg.format(type(source_data)))

        # Replace quote marks for the HTML syntax
        for i in ('u"', "u'", '"', "'"):  # quote marks and unicode prefixes
            data_str = data_str.replace(i, r"&quot;")
        xdsm_attrs["data-mdo"] = data_str
    else:  # both source data and data file name are None
        msg = 'Specify either "source_data" or "data_file".'
        raise ValueError(msg.format(type(source_data)))

    # grab the style
    styles_elem = write_style(xdsmjs.css())

    # put all style and JS into index
    toolbar_div = write_div(attrs={"class": "xdsm-toolbar"})
    xdsm_div = write_div(attrs=xdsm_attrs)
    body = "\n\n".join([toolbar_div, xdsm_div])

    if embeddable:
        index = "\n\n".join([styles_elem, xdsm_bundle, body])
    else:
        meta = '<meta charset="{}">'.format(char_set)
        head = "\n\n".join([meta, styles_elem, xdsm_bundle, xdsm_init])
        index = head_and_body(head, body, attrs={"class": "js", "lang": ""})

    # Embed style, scripts and data to HTML
    with open(outfile, "w") as f_out:
        f_out.write(index)


if __name__ == "__main__":
    import json

    # with JSON file name as input
    write_html(outfile="xdsmjs/xdsm_diagram.html", source_data="examples/idf.json")

    # with JSON data as input
    with open("XDSMjs/examples/idf.json") as f:
        data = json.load(f)
    write_html(outfile="xdsm_diagram_data_embedded.html", source_data=data)
