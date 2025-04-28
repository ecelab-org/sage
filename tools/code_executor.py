"""
Code execution tool for the Sage assistant.
Provides functionality to run Python code in a sandboxed environment.
"""

import os
import subprocess
import sys
import tempfile
from typing import (
    Any,
    Dict,
    Optional,
    Tuple,
)


def execute_code(input_data: Dict[str, Any]) -> Tuple[str, Optional[Exception]]:
    """
    Execute Python code in a sandboxed environment and return the results.

    Args:
        input_data: Dictionary containing:
            - code: Python code to execute
            - timeout: Maximum execution time in seconds (default: 20, max: 40)
            - save_plots: Whether to save matplotlib plots (default: True)

    Returns:
        Tuple of (result_content, exception)
    """
    # Extract parameters
    code = input_data.get("code", "").strip()
    timeout = min(float(input_data.get("timeout", 20)), 40)
    save_plots = input_data.get("save_plots", True)

    if not code:
        return "Error: No code provided to execute.", None

    # Create temporary files for the script and output
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            # Write the sandbox script with user code
            with open(os.path.join(temp_dir, "sandbox_script.py"), "wb") as script_file:
                # Write the sandbox script with user code
                script_file.write(_create_sandbox_script(code, save_plots).encode("utf-8"))
                script_file.flush()

            # Create an empty __init__.py file
            with open(os.path.join(temp_dir, "__init__.py"), "w", encoding="utf-8") as _init_file:
                pass

            # Get the module name without extension
            module_name = os.path.basename(script_file.name).removesuffix(".py")

            try:
                # Execute the code with timeout
                result = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        f"{module_name}",
                    ],
                    env={
                        "PYTHONPATH": temp_dir,
                        "PYTHONUNBUFFERED": "1",
                    },
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    check=False,
                )

                # Process the execution result
                if result.stdout:
                    output = result.stdout.strip()
                else:
                    output = "(No output)"

                if result.stderr:
                    output += f"\n\nErrors:\n{result.stderr.strip()}"

                # Check for saved plots if requested
                if save_plots:
                    plot_files = [
                        f for f in os.listdir(".") if f.startswith("plot_") and f.endswith(".png")
                    ]
                    if plot_files:
                        output += f"\n\n{len(plot_files)} plot(s) were generated."

            finally:
                pass

        # Limit output size to prevent overwhelming responses
        if len(output) > 10000:
            output = output[:10000] + "\n... (output truncated, exceeded 10000 characters)"

        return output, None

    except subprocess.TimeoutExpired:
        return "Error: Code execution timed out.", None

    except Exception as e:  # pylint: disable=broad-except
        return "", Exception(f"Error executing code: {str(e)}")


def _create_sandbox_script(code: str, save_plots: bool) -> str:
    """
    Create a Python script that will execute the user's code in a sandboxed environment.
    """
    # Define commonly used data science modules that are always allowed
    allowed_modules_and_packages = {
        "abc",  # Abstract Base Classes for defining interfaces
        "api",  # Generic API access libraries
        "astroid",  # Python abstract syntax tree library used by pylint
        "asttokens",  # Annotate AST trees with source code positions
        "babel",  # Internationalization library for Python
        "backports_abc",  # Backport of ABC features to older Python versions
        "brotli",  # Compression algorithm library
        "brotlicffi",  # CFFI-based bindings for the Brotli compression library
        "certifi",  # Mozilla's CA Bundle for SSL certificate verification
        "chardet",  # Character encoding detection
        "charset_normalizer",  # Character set detection and normalization
        "codecs",  # Encoders and decoders for various character formats
        "collections",  # Container datatypes (dict, list, set, deque, etc)
        "colorama",  # Cross-platform colored terminal text
        "comm",  # Jupyter kernel communication protocol
        "cPickle",  # C implementation of pickle (faster but legacy Python 2)
        "ctags",  # Source code indexing and tag generation
        "cycler",  # Composable style cycles for matplotlib
        "cython",  # C-Extensions for Python, optimizes Python code
        "Cython",  # Alternative import name for Cython
        "datetime",  # Date and time handling utilities
        "dateutil",  # Extensions to the standard datetime module
        "decorator",  # Decorator utilities for Python
        "defusedxml",  # XML parsing libraries that prevent vulnerabilities
        "docrepr",  # Documentation representation utilities
        "docutils",  # Documentation utilities for text processing
        "executing",  # Access to information about the currently executing frame
        "fontTools",  # Library for manipulating font files
        "functools",  # Higher-order functions and operations on callable objects
        "genericpath",  # OS-independent path operations
        "geopandas",  # Geospatial data analysis library
        "gi",  # GObject Introspection bindings for Python
        "idna",  # Internationalized Domain Names in Applications support
        "importlib",  # Implementation of the import statement
        "io",  # Core tools for working with streams
        "IPython",  # Interactive computing environment
        "ipywidgets",  # Interactive widgets for Jupyter notebooks
        "jedi",  # Autocompletion and static analysis for Python
        "jinja2",  # Template engine for Python
        "json",  # JSON encoder and decoder
        "kiwisolver",  # Fast implementation of the Cassowary constraint solver
        "Levenshtein",  # String similarity and edit distance metrics
        "logging",  # Python's built-in logging facility
        "markupsafe",  # String handling for HTML/XML, escapes unsafe characters
        "matplotlib",  # Comprehensive visualization library
        "mimetypes",  # Mapping of filenames to MIME types
        "mpl_toolkits",  # Matplotlib toolkits for specialized plotting
        "mpl_toolkits.basemap",  # Matplotlib toolkit for geographic plotting
        "msvcrt",  # MS Visual C++ Runtime services (Windows-specific)
        "networkx",  # Graph theory and complex network analysis
        "nt",  # Windows-specific OS functionality (Windows only)
        "ntpath",  # Windows-specific path operations (NT-style)
        "numpy",  # Numerical computing with multi-dimensional arrays
        "openpyxl",  # Reading/writing Excel 2010+ files
        "os",  # OS interface for file operations and environment vars
        "packaging",  # Core utilities for Python packages
        "pandas",  # Data analysis and manipulation library
        "parso",  # Python parser library used by Jedi
        "pathlib",  # Object-oriented filesystem paths
        "patsy",  # Statistical models description language
        "PIL",  # Python Imaging Library (Pillow)
        "pickle5",  # Backport of the Python 3.8 pickle module
        "plotly",  # Interactive, browser-based graphing library
        "png",  # Portable Network Graphics format
        "posixpath",  # POSIX-style pathname manipulation
        "prompt_toolkit",  # Library for interactive command lines
        "pure_eval",  # Safely evaluate Python expressions
        "pyarrow",  # Python bindings for Apache Arrow (columnar memory format)
        "pydantic",  # Data validation using Python type hints
        "pygments",  # Syntax highlighting for code
        "pyparsing",  # Parsing framework for Python
        "pyproj",  # Python interface to PROJ (cartographic projections)
        "PyQt5",  # Python bindings for the Qt application framework
        "PyQt6",  # Python bindings for the Qt application framework
        "PySide2",  # Python bindings for the Qt application framework
        "PySide6",  # Python bindings for the Qt application framework
        "pytz",  # Time zone calculations and definitions
        "qrcode",  # QR code generation
        "random",  # Random number generation
        "rapidfuzz",  # Fuzzy string matching and edit distances
        "re",  # Regular expressions
        "requests",  # HTTP client library
        "runpy",  # Locating and running Python modules
        "scikits",  # SciPy toolkits namespace
        "scipy",  # Scientific computing library
        "seaborn",  # Statistical data visualization based on matplotlib
        "shapely",  # Geometric objects and operations
        "simplejson",  # JSON encoder and decoder (faster alternative to json)
        "six",  # Python 2/3 compatibility library
        "sklearn",  # Machine learning library (scikit-learn)
        "sksparse",  # Sparse matrix extensions for SciPy
        "socks",  # SOCKS proxy client module
        "sphinx",  # Documentation generator
        "stack_data",  # Extract data from Python stack frames
        "stat",  # Utilities for interpreting os.stat() results
        "statsmodels",  # Statistical modeling and econometrics
        "svgwrite",  # SVG drawing library
        "sympy",  # Symbolic mathematics
        "tabulate",  # Pretty-print tabular data
        "textwrap",  # Text wrapping and filling
        "tkinter",  # Standard GUI toolkit for Python
        "tqdm",  # Progress bar for loops and iterations
        "traitlets",  # Configuration system for applications
        "typing",  # Support for type hints
        "typing_extensions",  # Backported and experimental type hints
        "uarray",  # Universal array interface for NumPy-like libraries
        "urllib2",  # Python 2.x module for URL handling (not available in Python 3)
        "urllib3",  # HTTP client library (used by requests)
        "wcwidth",  # Measures width of unicode strings in terminals
        "weakref",  # Weak references to objects
        "winreg",  # Windows registry access (Windows-specific)
        "wx",  # Cross-platform GUI toolkit
        "zipimport",  # Import modules from ZIP archives
        "zlib",  # Compression compatible with gzip
        "zstandard",  # Fast lossless compression algorithm (Zstd)
    }

    # Enable or disable file writing
    enable_file_write = True

    # Create sandbox header with auto-installation capability
    sandbox_header = f"""
import builtins
import importlib.util
import os
import subprocess
import sys
import traceback

# Define standard library modules and their path
STANDARD_LIB_MODULES = sys.builtin_module_names
STDLIB_PATH = os.path.dirname(os.__file__)

# Enable or disable file writing
ENABLE_FILE_WRITE = {enable_file_write}

# Whitelisted top-level packages (allowing all their submodules too)
ALLOWED_PACKAGES = {repr(allowed_modules_and_packages)}

# Store the original import function
original_import = builtins.__import__


def is_standard_library(package_name: str) -> bool:
    \"""
    Heuristically determine if a module is part of the standard library.
    \"""
    if package_name.startswith("_"):
        return True  # Allow underscore modules
    if package_name in STANDARD_LIB_MODULES:
        return True
    try:
        spec = importlib.util.find_spec(package_name)
        if not spec or not spec.origin:
            return False
        return (
            spec.origin.startswith(STDLIB_PATH)
            or spec.origin == "built-in"
            or (
                "site-packages" not in spec.origin
                and "dist-packages" not in spec.origin
                and "/lib/python" in spec.origin
            )
        )
    except ModuleNotFoundError:
        pass
    return False


def install_package(name: str, alt_name: str) -> bool:
    \"""
    Attempt to install a package using pip.
    \"""
    env = os.environ.copy()  # inherit current shell environment
    try:
        print(f"Installing {{name}}... This may take a moment.")
        cmd = [sys.executable, "-m", "pip", "install", "--no-cache-dir", "--quiet", name]
        subprocess.check_call(cmd, env=env)
        print(f"Successfully installed {{name}}")
        return True
    except Exception as e:
        print(f"\033[31mFailed to install '{{name}}'\033[0m: {{e}}")
        if name != alt_name:
            print(f"Trying to install as {{alt_name}}... This may take a moment.")
            try:
                cmd = [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "--no-cache-dir",
                    "--quiet",
                    alt_name,
                ]
                subprocess.check_call(cmd, env=env)
                print(f"Successfully installed {{alt_name}}")
                return True
            except Exception as embedded_e:
                print(f"\033[31mFailed to install '{{alt_name}}'\033[0m: {{embedded_e}}")
        return False


# Known manual mappings if top-level module != pip package name
PACKAGE_NAME_OVERRIDES = {{
    "bs4": "beautifulsoup4",
    "PIL": "Pillow",
    "yaml": "PyYAML",
    "scikits.umfpack": "scikit-umfpack",
    "sksparse.cholmod": "scikit-sparse",
    "png": "pypng",
    "mpl_toolkits.basemap": "basemap",
    "mpl_toolkits": "matplotlib",
}}


def get_top_level_package(name) -> str:
    \"""Extract the top-level package from a module name.\"""
    # Handle special cases for top-level packages
    if name.startswith("mpl_toolkits.basemap"):
        return "mpl_toolkits.basemap"
    if name.startswith("mpl_toolkits"):
        return "matplotlib"
    # Remove any submodules or classes
    return name.split(".")[0]


def is_package_installed(package_name):
    \"""Check if a top-level package is already installed.\"""
    try:
        spec = importlib.util.find_spec(package_name)
        return spec is not None
    except ModuleNotFoundError:
        return False


# Main secure import function
def secure_import(
    name: str, globals_dict: dict[str, str] | None = None, locals_dict=None, fromlist=(), level=0
):
    \"""
    Custom import function to restrict imports based on security policies.
    \"""
    if globals_dict is None:
        globals_dict = {{}}
    globals_dict = dict(globals_dict)
    # Handle relative imports (level > 0)
    rel_import_name = name
    if level > 0 and globals_dict and "__package__" in globals_dict:
        pkg = globals_dict["__package__"]
        if pkg:
            # Absolute package path for relative import
            rel_import_name = pkg.rsplit(".", level - 1)[0] + "." + name
    # Get the top-level package name
    package_name = get_top_level_package(rel_import_name)

    # Override if needed
    pip_package_name = PACKAGE_NAME_OVERRIDES.get(package_name, package_name)
    pip_full_name = PACKAGE_NAME_OVERRIDES.get(name, name)

    if not package_name:
        print(
            f"Import warning: Empty package name detected in import. Globals dict: {{globals_dict}}"
        )
        return None

    # Always allow built-in modules
    if is_standard_library(package_name):
        return original_import(name, globals_dict, locals_dict, fromlist, level)

    # Allow anything under explicitly whitelisted packages
    if package_name in ALLOWED_PACKAGES:
        # Auto-install if needed
        exceptions = [
            "nt",  # Windows-specific module
            "winreg",  # Windows-specific module
            "msvcrt",  # Windows-specific module
            "cPickle",  # Not available in Python 3 - use 'pickle' instead
            "pickle5",  # Not needed in Python 3.11 - use 'pickle' instead
            "urllib2",  # Not available in Python 3 - use 'urllib' instead
            "scikits",  # Temporarily disable until dockerization
            "sksparse",  # Temporarily disable until dockerization
        ]
        if not is_package_installed(package_name) and package_name not in exceptions:
            print(f"Package '{{package_name}}' not found. Attempting to install...")
            # Attempt to install the package
            success = install_package(pip_package_name, "-".join(pip_full_name.split(".")[:2]))
            if not success:
                print(f"Package '{{pip_package_name}}' is not available and couldn't be installed.")
        return original_import(name, globals_dict, locals_dict, fromlist, level)

    # Special handling for known problematic imports
    if name == "org.python.core":
        # This is a Jython-specific module that might be requested but isn't needed
        return None

    print(f"SecurityError: Import of '{{package_name}}' (from '{{name}}') is not allowed")
    raise ImportError(f"Blocked import: '{{package_name}}' (from '{{name}}')")


# Activate the custom import hook
builtins.__import__ = secure_import


import io

# Redirect stdout and stderr to capture output
original_stdout = sys.stdout
original_stderr = sys.stderr
sys.stdout = io.StringIO()
sys.stderr = io.StringIO()

# Override the built-in open function to restrict file operations, if needed
original_open = builtins.open


def safe_open(file, mode, *args, **kwargs):
    \"""
    Custom open function to restrict file write operations.
    \"""
    if mode and ("w" in mode or "a" in mode or "+" in mode):
        print("SecurityError: Writing to files is not allowed")
        return None
    return original_open(file, mode, *args, **kwargs)


if not ENABLE_FILE_WRITE:
    # Override the built-in open function to restrict file write operations
    builtins.open = safe_open
"""

    # Add matplotlib setup if plots are enabled
    if save_plots:
        sandbox_header += """

# Set up matplotlib for non-interactive backend
try:
    # First import all critical dependencies directly to prevent proxy import issues
    import atexit
    import importlib
    import sys

    # Special handling for matplotlib setup
    import matplotlib

    matplotlib.use("Agg")  # Non-interactive backend

    # Force load critical matplotlib modules in the correct order
    # Additional modules
    import matplotlib.axes
    import matplotlib.backends
    import matplotlib.cbook
    import matplotlib.cm
    import matplotlib.colors
    import matplotlib.figure
    import matplotlib.lines
    import matplotlib.patches
    import matplotlib.pyplot

    # Common matplotlib.pyplot alias
    plt = matplotlib.pyplot

    # Add plt to builtins for easier access
    builtins.plt = plt

    PLOT_ENABLED = True
    print("Matplotlib initialized successfully in non-interactive mode.")
except ImportError as e:
    print(f"Warning: Matplotlib setup failed: {e}")
    PLOT_ENABLED = False
except Exception as e:
    print(f"Warning: Error during matplotlib initialization: {e}")
    PLOT_ENABLED = False


def save_current_figures():
    if not PLOT_ENABLED:
        return []

    saved_files = []
    try:
        for i, fignum in enumerate(plt.get_fignums()):
            try:
                fig = plt.figure(fignum)
                filename = f"plot_{i}.png"
                fig.savefig(filename, bbox_inches="tight")
                saved_files.append(filename)
            except Exception as e:
                print(f"Error saving figure {fignum}: {e}")

        # Close all figures to free memory
        plt.close("all")
    except Exception as e:
        print(f"Error in save_current_figures: {e}")

    return saved_files
"""

    # Wrap code in try/except and add plot handling
    sandbox_body = """

def main():
    \"""Main function to execute user code in a sandboxed environment.\"""
    try:
{user_code}
    except Exception as e:
        print(f"Error: {{type(e).__name__}}: {{str(e)}}")
        traceback.print_exc(file=sys.stderr)
"""

    # Add plot saving code if enabled
    if save_plots:
        sandbox_body += """
    try:
        saved_plots = save_current_figures()
        if saved_plots:
            print("\\nPlots saved to files: " + ", ".join(saved_plots))
    except Exception as plot_e:
        print(f"Error saving plots: {{str(plot_e)}}")
"""

    # Add output capture and cleanup
    sandbox_footer = """
    # Get captured output
    output = sys.stdout.getvalue()
    error = sys.stderr.getvalue()

    # Restore original environment
    sys.stdout = original_stdout
    sys.stderr = original_stderr
    builtins.__import__ = original_import
    builtins.open = original_open

    # Print output
    print(output)
    if error:
        print(error)

# Run the main function if this script is executed directly
if __name__ == "__main__":
    main()
"""

    # Indent the user code for the try block
    indented_code = "\n".join(f"        {line}" for line in code.splitlines())

    # Combine all parts and return the final script
    return sandbox_header + sandbox_body.format(user_code=indented_code) + sandbox_footer
