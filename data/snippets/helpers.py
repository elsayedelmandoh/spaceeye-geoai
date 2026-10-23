"""Small helpers for the Oasis labs. They are not the learning point, so learners import them instead of typing them.

    from snippets.helpers import ar

Synthetic data — for training only.
"""
import matplotlib


def ar(text: str) -> str:
    """Arabic text for matplotlib titles and labels.

    matplotlib 3.11 and later shapes Arabic itself; older versions (Colab may have one) need the letters joined
    and ordered right to left first, with arabic-reshaper and python-bidi (Cell 1a installs both).
    """
    version = tuple(int(x) for x in matplotlib.__version__.split(".")[:2])
    if version >= (3, 11):
        return text
    import arabic_reshaper
    from bidi.algorithm import get_display
    return get_display(arabic_reshaper.reshape(text))
