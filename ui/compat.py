"""
Streamlit compatibility layer.

Provides fallbacks for Streamlit features that may not be available
in all versions or may change between releases.
"""

import streamlit as st
from functools import wraps


def safe_dialog(title):
    """
    Decorator for dialog functions with fallback to expander.

    Usage:
        @safe_dialog("My Dialog")
        def my_dialog():
            st.write("Content")
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # Try using st.dialog (Streamlit >= 1.35.0)
                dialog_decorator = st.dialog(title)
                return dialog_decorator(func)(*args, **kwargs)
            except AttributeError:
                # Fallback: use expander
                with st.expander(title, expanded=True):
                    return func(*args, **kwargs)
        return wrapper
    return decorator


def safe_toast(message, icon=None):
    """
    Show a toast notification with fallback to info box.

    Args:
        message: Toast message
        icon: Optional emoji icon (ignored in fallback)
    """
    try:
        if icon:
            st.toast(message, icon=icon)
        else:
            st.toast(message)
    except (AttributeError, Exception):
        # Fallback: use st.success which is always available
        st.success(message)


def safe_status(label, expanded=True):
    """
    Create a status container with fallback to spinner.

    Usage:
        with safe_status("Processing...") as status:
            # do work
            status.update(label="Done!", state="complete")
    """
    try:
        return st.status(label, expanded=expanded)
    except AttributeError:
        # Fallback: return a mock status object with spinner
        return _MockStatus(label)


class _MockStatus:
    """Mock status object for older Streamlit versions."""

    def __init__(self, label):
        self.label = label
        self._spinner = None

    def __enter__(self):
        self._spinner = st.spinner(self.label)
        self._spinner.__enter__()
        return self

    def __exit__(self, *args):
        if self._spinner:
            self._spinner.__exit__(*args)

    def update(self, label=None, state=None):
        """Update is a no-op in fallback mode."""
        pass


def safe_link_button(label, url, **kwargs):
    """
    Create a link button with fallback to markdown link.

    Args:
        label: Button label
        url: URL to link to
        **kwargs: Additional arguments (ignored in fallback)
    """
    try:
        st.link_button(label, url, **kwargs)
    except AttributeError:
        # Fallback: use markdown link
        st.markdown(f"[{label}]({url})")


def safe_fragment(func):
    """
    Decorator for fragment functions with fallback to regular function.

    Fragments allow partial reruns in Streamlit >= 1.33.0.
    In older versions, the function runs normally.
    """
    try:
        return st.fragment(func)
    except AttributeError:
        # Fallback: return function as-is
        return func
