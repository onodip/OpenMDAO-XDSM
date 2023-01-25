"""
Functions to write HTML elements.

This function were part of OpenMDAO until version 3.20.
"""
import os

_IND = 4  # indentation (spaces)


def head_and_body(head, body, attrs=None):
    """
    Make an html element from a head and body.
    Parameters
    ----------
    head : str
        Head of HTML.
    body : str
        Body of the HTML.
    attrs : dict or None
        Attributes of the html element.
        Defaults to None.
    Returns
    -------
    str
        HTML element.
    """
    # Wraps the head and body in tags
    doc_type = '<!doctype html>'
    head_elem = write_tags(tag='head', content=head, new_lines=True)
    body_elem = write_tags(tag='body', content=body, new_lines=True)
    content = '\n\n'.join([head_elem, body_elem])
    index = write_tags(tag='html', content=content, attrs=attrs, new_lines=True)
    return doc_type + '\n' + index


def write_tags(tag, content='', attrs=None, cls_attr=None, uid=None, new_lines=False, indent=0,
               **kwargs):
    """
    Write an HTML element enclosed in tags.
    Parameters
    ----------
    tag : str
        Name of the tag.
    content : str or list(str)
        This goes into the body of the element.
    attrs : dict or None
        Attributes of the element.
        Defaults to None.
    cls_attr : str or None
        The "class" attribute of the element.
    uid : str or None
        The "id" attribute of the element.
    new_lines : bool
        Make new line after tags.
    indent : int
        Indentation expressed in spaces.
        Defaults to 0.
    **kwargs : dict
        Alternative way to add element attributes. Use with attention, can overwrite some in-built
        python names as "class" or "id" if misused.
    Returns
    -------
    str
        HTML element enclosed in tags.
    """
    # Writes an HTML tag with element content and element attributes (given as a dictionary)
    line_sep = '\n' if new_lines else ''
    spaces = ' ' * indent
    template = '{spaces}<{tag} {attributes}>{ls}{content}{ls}</{tag}>\n'
    if attrs is None:
        attrs = {}
    attrs.update(kwargs)
    if cls_attr is not None:
        attrs['class'] = cls_attr
    if uid is not None:
        attrs['id'] = uid
    attrs = ' '.join(['{}="{}"'.format(k, v) for k, v in attrs.items()])
    if isinstance(content, list):  # Convert iterable to string
        content = '\n'.join(content)
    return template.format(tag=tag, content=content, attributes=attrs, ls=line_sep, spaces=spaces)


def write_div(content='', attrs=None, cls_attr=None, uid=None, indent=0, **kwargs):
    """
    Write an HTML div.
    Parameters
    ----------
    content : str or list(str)
        This goes into the body of the element.
    attrs : dict
        Attributes of the element.
    cls_attr : str or None
        The "class" attribute of the element.
    uid : str or None
        The "id" attribute of the element.
    indent : int
        Indentation expressed in spaces.
    **kwargs : dict
        Alternative way to add element attributes. Use with attention, can overwrite some in-bult
        python names as "class" or "id" if misused.
    Returns
    -------
    str
        HTML element enclosed in tags.
    """
    return write_tags('div', content=content, attrs=attrs, cls_attr=cls_attr, uid=uid,
                      new_lines=False, indent=indent, **kwargs)


def write_style(content='', attrs=None, indent=0, **kwargs):
    """
    Write CSS.
    Parameters
    ----------
    content : str or list(str)
        This goes into the body of the element.
    attrs : dict or None
        Attributes of the element.
        Defaults to None.
    indent : int
        Indentation expressed in spaces.
        Defaults to 0.
    **kwargs : dict
        Alternative way to add element attributes. Use with attention, can overwrite some in-built
        python names as "class" or "id" if misused.
    Returns
    -------
    str
        HTML for this CSS element.
    """
    default = {'type': "text/css"}
    if attrs is None:
        attrs = default
    else:
        attrs = default.update(attrs)
    return write_tags('style', content, attrs=attrs, new_lines=True, indent=indent, **kwargs)


def write_script(content='', attrs=None, indent=0, **kwargs):
    """
    Write JavaScript.
    Parameters
    ----------
    content : str or list(str)
        This goes into the body of the element.
    attrs : dict or None
        Attributes of the element.
        Defaults to None.
    indent : int
        Indentation expressed in spaces.
        Defaults to 0.
    **kwargs : dict
        Alternative way to add element attributes. Use with attention, can overwrite some in-built
        python names as "class" or "id" if misused.
    Returns
    -------
    str
        HTML for this JavaScript element.
    """
    default = {'type': "text/javascript"}
    if attrs is None:
        attrs = default
    else:
        attrs = default.update(attrs)
    return write_tags('script', content, attrs=attrs, new_lines=True, indent=indent, **kwargs)





