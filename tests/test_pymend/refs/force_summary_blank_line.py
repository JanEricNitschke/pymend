"""Reference file for force_summary_blank_line tests."""


def short_desc_with_blank_line_no_meta():
    """Short summary.

    Long description here.
    """
    pass


def short_desc_without_blank_line_no_meta():
    """Short summary.
    Long description here.
    """
    pass


def short_desc_with_blank_line_with_meta_correct():
    """Short summary.

    Long description here.

    Parameters
    ----------
    x : int
        Some parameter.
    """
    pass


def short_desc_with_blank_line_with_meta_missing_blank():
    """Short summary.

    Long description here.
    Parameters
    ----------
    x : int
        Some parameter.
    """
    pass


def short_desc_without_blank_line_with_meta():
    """Short summary.
    Long description here.

    Parameters
    ----------
    x : int
        Some parameter.
    """
    pass
