"""Common utility functions for the project."""


def print_red(text: str, *args, **kwargs) -> None:
    """
    Print text in red color.

    Args:
        text: The text to print
    """
    print(f"\033[91m{text}\033[0m", *args, **kwargs)  # ANSI escape code for red text


def print_green(text: str, *args, **kwargs) -> None:
    """
    Print text in green color.

    Args:
        text: The text to print
    """
    print(f"\033[92m{text}\033[0m", *args, **kwargs)  # ANSI escape code for green text


def print_yellow(text: str, *args, **kwargs) -> None:
    """
    Print text in yellow color.

    Args:
        text: The text to print
    """
    print(f"\033[33m{text}\033[0m", *args, **kwargs)  # ANSI escape code for yellow text


def print_blue(text: str, *args, **kwargs) -> None:
    """
    Print text in blue color.

    Args:
        text: The text to print
    """
    print(f"\033[94m{text}\033[0m", *args, **kwargs)  # ANSI escape code for blue text
