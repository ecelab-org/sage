"""
An interactive AI assistant with file system capabilities.

This program integrates with Anthropic's Claude AI to provide a conversational
interface that can perform file system operations such as reading files,
listing directories, and editing text files.

The agent uses a tool-based architecture that allows easy extension with
additional capabilities by registering new tool functions.
"""

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    Union,
)

import anthropic
from anthropic.types import (
    MessageParam,
    ToolParam,
)
from dotenv import load_dotenv

from tools.web_scraper import scrape_website

# Load environment variables from .env file (containing API keys)
load_dotenv()

# Default model to use if not specified in .env
DEFAULT_MODEL = "claude-3-5-haiku-20241022"


@dataclass(frozen=True)
class ToolDefinition:
    """
    Defines a tool that can be used by an AI agent to interact with external systems.
    A tool represents an action that an AI can take in the world. Each tool consists of
    a name, description, input schema, and an implementation function that executes
    the actual operation when called by the AI.
    Attributes:
        name (str): Name of the tool, used by the AI to invoke it.
        description (str): Human-readable description of what the tool does.
        input_schema (Dict[str, Any]): JSON schema defining expected inputs and their types.
        function (Callable[[Dict[str, Any]], Tuple[str, Optional[Exception]]]):
            Implementation function to be called when the tool is invoked.
            Takes input parameters as a dictionary and returns a tuple of:
            - A string containing the result or error message
            - An optional Exception object if an error occurred
        is_embedded (bool): Flag indicating if this is an Anthropic-defined embedded tool.
            Defaults to False.
        embedded_type (Optional[str]): Type of the embedded tool, if applicable.
            Required if is_embedded is True.
        compatible_models (Optional[Sequence[str]]): List of model identifiers that can use this tool.
            If None, all models can use it. Required if is_embedded is True.
    Note:
        This class serves as a contract between the AI's intentions and the actual
        system functionality, ensuring inputs are properly validated and outputs
        are correctly formatted.
    Raises:
        ValueError: If an embedded tool is missing embedded_type or compatible_models.
    Defines a tool that the AI agent can use to interact with the system.
    """

    name: str  # Name of the tool, used by the AI to invoke it
    description: str  # Human-readable description of what the tool does
    input_schema: Dict[str, Any]  # JSON schema defining expected inputs
    function: Callable[
        [Dict[str, Any]], Tuple[str, Optional[Exception]]
    ]  # Actual implementation function to be called
    is_embedded: bool = False  # Flag indicating if this is an Anthropic-defined embedded tool
    embedded_type: Optional[str] = None  # Type of the embedded tool, if applicable
    compatible_models: Optional[Sequence[str]] = (
        None  # Models that can use this tool - if None, all models can use it
    )

    def __post_init__(self):
        """
        Validate that embedded tools have an embedded type and compatible models specified.
        """
        if self.is_embedded and self.embedded_type is None:
            raise ValueError("Embedded tools must have an embedded_type specified")

        if self.is_embedded and self.compatible_models is None:
            raise ValueError("Embedded tools must have compatible_models specified")


class ToolRegistry:
    """
    Central registry that maintains all available tools.

    This registry allows tools to be dynamically registered and accessed
    by the agent without hardcoding references to specific tools.
    """

    def __init__(self):
        self.tools = {}  # Dictionary to store tools by name

    def register(self, tool_def: ToolDefinition) -> None:
        """
        Register a tool in the registry.

        Args:
            tool_def: The tool definition to register
        """
        self.tools[tool_def.name] = tool_def

    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """
        Get a tool by name.

        Args:
            name: The name of the tool to retrieve

        Returns:
            The tool definition if found, None otherwise
        """
        return self.tools.get(name)

    def get_all_tools(self) -> List[ToolDefinition]:
        """
        Get all registered tools.

        Returns:
            List of all tool definitions in the registry
        """
        return list(self.tools.values())


# Create a global tool registry
tool_registry = ToolRegistry()


def register_tool(
    name: str,
    description: str,
    input_schema: Dict[str, Any],
    is_embedded: bool = False,
    embedded_type: Optional[str] = None,
    compatible_models: Optional[Sequence[str]] = None,
) -> Callable[[Callable], Callable]:
    """
    Decorator to register a function as a tool.

    This decorator simplifies tool registration by automatically creating
    a ToolDefinition object and adding it to the registry.

    Args:
        name: The name of the tool
        description: A human-readable description of what the tool does
        input_schema: JSON schema defining the expected inputs and required fields.
                     Should include a "properties" dict and a "required" list.
        is_embedded: Flag indicating if this is an Anthropic-defined embedded tool
        embedded_type: Type of the embedded tool, if applicable
        compatible_models: Models that can use this tool

    Returns:
        A decorator function that registers the decorated function as a tool
    """

    def decorator(func):
        # Extract properties and required fields from the schema
        properties = input_schema.get("properties", {})
        required = input_schema.get("required", [])

        # Create a ToolDefinition object and register it
        tool_def = ToolDefinition(
            name=name,
            description=description,
            input_schema={"properties": properties, "required": required},
            function=func,
            is_embedded=is_embedded,
            embedded_type=embedded_type,
            compatible_models=compatible_models,
        )
        tool_registry.register(tool_def)
        return func

    return decorator


class Agent:
    """
    The main agent class that orchestrates interactions between the user, AI model,
    and registered tools.

    This class handles the conversation flow, processes user inputs, executes
    AI inferences, and runs tools when requested by the AI.
    """

    def __init__(
        self,
        client: anthropic.Anthropic,
        input_handler: Callable[[], Tuple[str, bool]],
        registry: ToolRegistry,
    ):
        """
        Initialize the agent with required components.

        Args:
            client: Anthropic API client
            input_handler: Function to get user input
            registry: Registry containing available tools
        """
        self.client = client
        self.input_handler = input_handler
        self.tool_registry = registry

    def run(self):
        """
        Run the main agent loop that handles the conversation flow.

        This method continuously processes user inputs, sends them to the AI,
        displays AI responses, and executes tools when requested by the AI.
        """
        conversation = []  # Stores the entire conversation history

        print("Chat with Claude (use 'ctrl-c' to quit)")

        read_user_input = True
        while True:
            # Get user input if needed
            if read_user_input:
                print("\n\U0001f9d1 \033[94mYou\033[0m: ", end="")
                user_input, ok = self.input_handler()
                if not ok:
                    break  # Exit if user input couldn't be retrieved (e.g., Ctrl+C)

                # Format user message for the conversation history
                user_message = {
                    "role": "user",
                    "content": [{"type": "text", "text": user_input}],
                }
                conversation.append(user_message)

            # Get AI response based on conversation history
            message = self.run_inference(conversation)
            conversation.append(message)

            # Process AI response content
            tool_results = []
            for content in message.get("content", []):
                content_type = content.get("type")
                if content_type == "text":
                    # Display text responses from the AI
                    print(f"\U0001f916 \033[93mClaude\033[0m: {content.get('text', '')}")
                elif content_type == "tool_use":
                    # Execute tools requested by the AI
                    result = self.execute_tool(
                        content.get("id", ""),
                        content.get("name", ""),
                        content.get("input", {}),
                    )
                    # Always include tool results to satisfy the API requirement
                    tool_results.append(result)

            # Determine whether to get more user input or continue with tool results
            if not tool_results:
                read_user_input = True
                continue

            # If tools were executed, add their results to the conversation
            # instead of getting new user input
            read_user_input = False

            # Create a well-formed content message with tool results
            conversation.append({"role": "user", "content": tool_results})

    def execute_tool(self, id_str: str, name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool requested by the AI.

        Args:
            id_str: Unique identifier for this tool use
            name: Name of the tool to execute
            input_data: Input parameters for the tool

        Returns:
            A dictionary containing the tool result
        """
        # Find the requested tool in the registry
        tool_def = self.tool_registry.get_tool(name)

        if not tool_def:
            return {
                "type": "tool_result",
                "tool_use_id": id_str,
                "content": "tool not found",
            }

        # Log tool execution
        print(f"\U0001f527 \033[92mtool\033[0m: {name}({json.dumps(input_data)})")

        # Execute the tool function
        response, err = tool_def.function(input_data)
        if err:
            error_msg = str(err)
            return {
                "type": "tool_result",
                "tool_use_id": id_str,
                "content": error_msg,
            }

        return {"type": "tool_result", "tool_use_id": id_str, "content": response}

    def run_inference(self, conversation: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Send the conversation history to the AI and get a response.

        This method formats the conversation and available tools for the Anthropic API,
        handles the API call, and processes the response.

        Args:
            conversation: The conversation history

        Returns:
            The AI's response message
        """
        # Format messages for the API
        messages: List[MessageParam] = [
            {"role": msg["role"], "content": msg["content"]} for msg in conversation
        ]

        # Create a list of tools to be passed to the API
        tools: List[Union[ToolParam, Mapping[str, str]]] = []

        # Get model from environment variable or use default
        model = os.environ.get("ANTHROPIC_MODEL", DEFAULT_MODEL)

        # Add tools from registry
        # Filter tools based on model compatibility
        # If a tool has no compatible models, it is available to all models
        model_compatible_tools = [
            tool
            for tool in self.tool_registry.get_all_tools()
            if not tool.compatible_models
            or any(compatible_model in model for compatible_model in tool.compatible_models)
        ]

        # Add each tool to the tools list
        for tool in model_compatible_tools:
            # If it's a custom tool, add it with its input schema
            if not tool.is_embedded:
                tools.append(
                    ToolParam(
                        name=tool.name,
                        description=tool.description,
                        input_schema={
                            "type": "object",
                            "properties": tool.input_schema.get("properties", {}),
                            "required": tool.input_schema.get("required", []),
                        },
                    )
                )
            else:
                ## If it's an embedded tool, add it with its type
                embedded_type = tool.embedded_type or ""  # to help type checking
                tools.append({"name": tool.name, "type": embedded_type})

        try:
            # Call the Anthropic API
            response = self.client.messages.create(
                model=model,
                max_tokens=8192,
                messages=messages,
                tools=tools,  # type: ignore
            )
            return response.model_dump()
        except Exception as e:  # pylint: disable=broad-except
            # Handle API errors
            print(f"Error during inference: {str(e)}")
            return {
                "role": "assistant",
                "content": [{"type": "text", "text": "Error during inference."}],
            }


def get_user_message() -> Tuple[str, bool]:
    """
    Get a message from the user via standard input.

    Returns:
        Tuple of (user_input, success_flag)
        The success_flag is False if input couldn't be read (e.g., Ctrl+C)
    """
    try:
        user_input = input()
        return user_input, True
    except EOFError:
        return "", False


def _read_file(file_path: Path) -> Tuple[str, Optional[Exception]]:
    """
    Read the contents of a file.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
        return content, None
    except Exception as e:  # pylint: disable=broad-except
        return "", e


def create_new_file(file_path: Path, content: str) -> Tuple[str, Optional[Exception]]:
    """
    Create a new file with the specified content.

    Args:
        file_path: Path where the file should be created
        content: Content to write to the file

    Returns:
        Tuple of (success_message, None) on success or ("", error) on failure
    """
    try:
        # Create any necessary parent directories
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Write the content to the file
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(content)

        return f"Successfully created file {file_path.as_posix()}", None
    except Exception as e:  # pylint: disable=broad-except
        return "", Exception(f"Failed to create file: {str(e)}")


def _edit_file(file_path: Path, old_str: str, new_str: str) -> Tuple[str, Optional[Exception]]:
    """
    Edit a file by replacing occurrences of old_str with new_str.
    If old_str is empty, create a new file with new_str as its content.
    """
    try:
        try:
            # Try to read the existing file
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()
        except FileNotFoundError:
            return "", Exception(f"ERROR: file '{file_path.as_posix()}' not found")

        if not old_str:
            new_content = new_str
        else:
            # Replace the text
            new_content = content.replace(old_str, new_str)

            # Check if any replacements were made
            if content == new_content:
                return "", Exception(f"ERROR: '{old_str}' not found in file {file_path.as_posix()}")

        # Write the modified content
        return create_new_file(file_path=file_path, content=new_content)
    except Exception as e:  # pylint: disable=broad-except
        return "", e


# TOOL IMPLEMENTATIONS


@register_tool(
    name="str_replace_editor",
    description="Embedded tool: text editor for file operations (view, create, str_replace).",
    input_schema={
        "properties": {
            "command": {"type": "string"},
            "path": {"type": "string"},
            "old_str": {"type": "string"},
            "new_str": {"type": "string"},
            "file_text": {"type": "string"},
        },
        "required": ["command", "path"],
    },
    is_embedded=True,
    embedded_type="text_editor_20250124",
    # This is the type that Claude uses to identify the tool
    compatible_models=["claude-3-5-sonnet", "claude-3-7-sonnet"],
    # List of models that can use this tool
)
def str_replace_editor(input_data: Dict[str, Any]) -> Tuple[str, Optional[Exception]]:
    """
    Handle Claude's built-in text editor commands: view, create, str_replace.
    """
    command = input_data.get("command")
    path = input_data.get("path", "")

    try:
        if command == "view":
            return _read_file(file_path=Path(path))

        elif command == "create":
            file_text = input_data.get("file_text", "")
            return create_new_file(file_path=Path(path), content=file_text)

        elif command == "str_replace":
            old_str = input_data.get("old_str", "")
            new_str = input_data.get("new_str", "")
            # If old_str is empty, write new_str to the file
            if not old_str:
                return create_new_file(file_path=Path(path), content=new_str)
            ret = _edit_file(file_path=Path(path), old_str=old_str, new_str=new_str)
            # Check if the edit was successful
            if ret[0]:
                return "Text replaced successfully", None
            # If the edit failed, return the error message
            return ret
        else:
            return "", Exception(f"Unsupported command: {command}")

    except Exception as e:  # pylint: disable=broad-except
        return "", e


@register_tool(
    name="read_file",
    description=(
        "Read the contents of a given relative file path. Use this when you want to see what's "
        "inside a file. Do not use this with directory names."
    ),
    input_schema={
        "properties": {
            "path": {
                "type": "string",
                "description": "The relative path of a file in the working directory.",
            }
        },
        "required": ["path"],
    },
)
def read_file(input_data: Dict[str, Any]) -> Tuple[str, Optional[Exception]]:
    """
    Read and return the contents of a file.

    Args:
        input_data: Dictionary containing the 'path' key

    Returns:
        Tuple of (file_contents, None) on success or ("", error) on failure
    """
    path = input_data.get("path", "")

    return (
        _read_file(file_path=Path(path))
        if path
        else ("", Exception("ERROR: missing required parameter: path"))
    )


@register_tool(
    name="list_files",
    description=(
        "List files and directories at a given path. If no path is provided, lists files in the "
        "current directory."
    ),
    input_schema={
        "properties": {
            "path": {
                "type": "string",
                "description": (
                    "Optional relative path to list files from. Defaults to current directory if "
                    "not provided."
                ),
            }
        },
        "required": [],
    },
)
def list_files(input_data: Dict[str, Any]) -> Tuple[str, Optional[Exception]]:
    """
    List files and directories at a given path.

    Args:
        input_data: Dictionary containing optional 'path' key

    Returns:
        Tuple of (JSON string of files/directories, None) on success or ("", error) on failure
    """
    path = input_data.get("path", "")

    dir_path = "."  # Default to current directory
    if path:
        dir_path = path

    try:
        files = []
        # Walk the directory tree and collect all files and directories
        for root, dirs, filenames in os.walk(dir_path):
            for name in dirs + filenames:
                full_path = os.path.join(root, name)
                rel_path = os.path.relpath(full_path, dir_path)

                if rel_path != ".":
                    if os.path.isdir(full_path):
                        files.append(f"{rel_path}/")  # Add trailing slash to directories
                    else:
                        files.append(rel_path)

        return json.dumps(files), None
    except Exception as e:  # pylint: disable=broad-except
        return "", e


@register_tool(
    name="edit_file",
    description="""Make edits to a text file or create a new file.

    IMPORTANT: This tool ALWAYS requires three parameters: path, old_str, and new_str.

    For existing files:
    - Replaces 'old_str' with 'new_str' in the given file
    - 'old_str' must exist in the file and must be different from 'new_str'

    For creating new files:
    - Set 'path' to the desired file location
    - Set 'old_str' to an empty string: ""
    - Set 'new_str' to the content you want in the file

    Example to create a file:
    edit_file({"path": "example.txt", "old_str": "", "new_str": "File content here"})
    """,
    input_schema={
        "properties": {
            "path": {"type": "string", "description": "The path to the file"},
            "old_str": {
                "type": "string",
                "description": (
                    "Text to search for in existing file. Use empty string when creating new files."
                ),
            },
            "new_str": {
                "type": "string",
                "description": "Text to replace old_str with, or the content for new files.",
            },
        },
        "required": ["path", "old_str", "new_str"],
    },
)
def edit_file(input_data: Dict[str, Any]) -> Tuple[str, Optional[Exception]]:
    """
    Edit a text file by replacing text or create a new file.

    Args:
        input_data: Dictionary containing the following keys:
            - 'path': Path to the file (required)
            - 'old_str': String to be replaced (required - empty for new file creation)
            - 'new_str': Replacement string (required)

    Raises:
        Exception: If validation fails for any of the following reasons:
            - 'path' parameter is missing
            - 'old_str' parameter is missing
            - 'new_str' parameter is missing
            - 'old_str' equals 'new_str'
            - 'path' is empty

    Notes:
        If 'old_str' is empty, a new file will be created with 'new_str' as content.
        Otherwise, existing file at 'path' will be modified by replacing 'old_str' with 'new_str'.
        input_data: Dictionary containing 'path', 'old_str', and 'new_str' keys

    Returns:
        Tuple of (success_message, None) on success or ("", error) on failure
    """
    # Validate inputs
    if "path" not in input_data:  # Check if parameter exists
        return "", Exception("ERROR: missing required parameter: path")
    if "old_str" not in input_data:  # Check if parameter exists
        return "", Exception("ERROR: missing required parameter: old_str")
    if "new_str" not in input_data:  # Check if parameter exists
        return "", Exception("ERROR: missing required parameter: new_str")

    path = input_data.get("path", "")
    old_str = input_data.get("old_str", "")
    new_str = input_data.get("new_str", "")

    # Validate parameter values
    if path == "":  # Check if path is empty
        return "", Exception("ERROR: 'path' must not be empty")
    if old_str == new_str:  # Check if old_str and new_str are the same
        return "", Exception("ERROR: 'old_str' must be different from 'new_str'")

    if not old_str:
        # If old_str is empty, create a new file
        return create_new_file(file_path=Path(path), content=new_str)
    return _edit_file(file_path=Path(path), old_str=old_str, new_str=new_str)


# Register the web scraper tool
@register_tool(
    name="web_scraper",
    description=(
        "Scrape content from websites. This tool can extract text, HTML, or links from a webpage. "
        "Use it to gather information from online sources for analysis or reference."
    ),
    input_schema={
        "properties": {
            "url": {
                "type": "string",
                "description": (
                    "The complete URL of the website to scrape (must include http:// or https://)."
                ),
            },
            "params": {
                "type": "object",
                "description": "Optional parameters to customize the scraping behavior.",
                "properties": {
                    "selector": {
                        "type": "string",
                        "description": (
                            "CSS selector to target specific elements (e.g., 'div.content', 'h1', "
                            "'.main-article'). Defaults to 'body'."
                        ),
                    },
                    "extract": {
                        "type": "string",
                        "enum": ["text", "html", "links"],
                        "description": (
                            "What to extract: 'text' (plain text), 'html' (HTML markup), or "
                            "'links' (all hyperlinks). Defaults to 'text'."
                        ),
                    },
                    "timeout": {
                        "type": "number",
                        "description": "Request timeout in seconds. Defaults to 10 seconds.",
                    },
                },
            },
        },
        "required": ["url"],
        "examples": [
            {"url": "https://example.com"},
            {"url": "https://example.com", "params": {"selector": "main", "extract": "text"}},
            {"url": "https://example.com", "params": {"selector": "nav", "extract": "links"}},
        ],
    },
)
def web_scraper(input_data: Dict[str, Any]) -> Tuple[str, Optional[Exception]]:
    """
    Scrape content from a website.

    Examples:
    - Basic usage: web_scraper({"url": "https://example.com"})
    - Extract text from specific element: web_scraper({"url": "https://example.com", "params": {"selector": "main"}})
    - Extract links from navigation: web_scraper({"url": "https://example.com", "params": {"selector": "nav", "extract": "links"}})
    - Extract HTML from article: web_scraper({"url": "https://example.com", "params": {"selector": "article", "extract": "html"}})

    Returns:
        For text/html: String containing the extracted content
        For links: JSON string with an array of {text, href} objects
    """
    return scrape_website(input_data)


def main():
    """
    Main entry point of the program.

    Initializes the Anthropic client and agent, then starts the agent's main loop.
    Handles top-level exceptions to prevent crashes.
    """
    client = anthropic.Anthropic()  # Initialize the Anthropic API client

    # Create the agent with the Anthropic client, user input function, and tool registry
    agent = Agent(client, get_user_message, tool_registry)

    model = os.environ.get("ANTHROPIC_MODEL", DEFAULT_MODEL)
    model_compatible_tools = [
        tool
        for tool in tool_registry.get_all_tools()
        if not tool.compatible_models
        or any(compatible_model in model for compatible_model in tool.compatible_models)
    ]
    print(f"Using model: {model}")
    print(
        "Available embedded tools: "
        f"{[tool.name for tool in model_compatible_tools if tool.is_embedded]}"
    )
    print(
        "Available custom tools: "
        f"{[tool.name for tool in model_compatible_tools if not tool.is_embedded]}"
    )

    try:
        # Start the agent's conversation loop
        agent.run()
    except (anthropic.APIError, anthropic.APIConnectionError) as e:
        print(f"Anthropic API Error: {str(e)}")
    except (IOError, OSError) as e:
        print(f"Input/Output Error: {str(e)}")
    except KeyboardInterrupt:
        print("\nExiting due to user interrupt")
    except Exception as e:  # pylint: disable=broad-except
        print(f"Unexpected error: {str(e)}")


if __name__ == "__main__":
    main()
