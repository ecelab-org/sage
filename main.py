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
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Tuple,
)

import anthropic
from dotenv import load_dotenv

# Load environment variables from .env file (containing API keys)
load_dotenv()

# Default model to use if not specified in .env
DEFAULT_MODEL = "claude-3-5-haiku-20241022"


class ToolDefinition:
    """
    Defines a tool that the AI agent can use to interact with the system.

    Each tool has a name, description, input schema, and an implementation function.
    This class serves as a contract between the AI and the actual functionality.
    """

    def __init__(
        self,
        name: str,
        description: str,
        input_schema: Dict[str, Any],
        function: Callable[[Dict[str, Any]], Tuple[str, Optional[Exception]]],
    ):
        self.name = name  # Name of the tool, used by the AI to invoke it
        self.description = (
            description  # Human-readable description of what the tool does
        )
        self.input_schema = input_schema  # JSON schema defining expected inputs
        self.function = function  # Actual implementation function to be called


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


def register_tool(name: str, description: str, input_schema: Dict[str, Any]):
    """
    Decorator to register a function as a tool.

    This decorator simplifies tool registration by automatically creating
    a ToolDefinition object and adding it to the registry.

    Args:
        name: The name of the tool
        description: A human-readable description of what the tool does
        input_schema: JSON schema defining the expected inputs

    Returns:
        A decorator function that registers the decorated function as a tool
    """

    def decorator(func):
        tool_def = ToolDefinition(
            name=name, description=description, input_schema=input_schema, function=func
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
        get_user_message: Callable[[], Tuple[str, bool]],
        tool_registry: ToolRegistry,
    ):
        """
        Initialize the agent with required components.

        Args:
            client: Anthropic API client
            get_user_message: Function to get user input
            tool_registry: Registry containing available tools
        """
        self.client = client
        self.get_user_message = get_user_message
        self.tool_registry = tool_registry

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
                print("\033[94mYou\033[0m: ", end="")
                user_input, ok = self.get_user_message()
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
                    print(f"\033[93mClaude\033[0m: {content.get('text', '')}")
                elif content_type == "tool_use":
                    # Execute tools requested by the AI
                    result = self.execute_tool(
                        content.get("id", ""),
                        content.get("name", ""),
                        content.get("input", {}),
                    )
                    tool_results.append(result)

            # Determine whether to get more user input or continue with tool results
            if not tool_results:
                read_user_input = True
                continue

            # If tools were executed, add their results to the conversation
            # instead of getting new user input
            read_user_input = False
            conversation.append({"role": "user", "content": tool_results})

    def execute_tool(
        self, id_str: str, name: str, input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
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
        print(f"\033[92mtool\033[0m: {name}({json.dumps(input_data)})")

        # Execute the tool function
        response, err = tool_def.function(input_data)
        if err:
            return {"type": "tool_result", "tool_use_id": id_str, "content": str(err)}

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
        # Import necessary types for the Anthropic API
        from anthropic.types import (
            MessageParam,
            ToolParam,
        )

        # Format messages for the API
        messages: List[MessageParam] = [
            {"role": msg["role"], "content": msg["content"]} for msg in conversation
        ]

        # Format tools for the API
        anthropic_tools = []
        for tool in self.tool_registry.get_all_tools():
            anthropic_tools.append(
                ToolParam(
                    name=tool.name,
                    description=tool.description,
                    input_schema={"type": "object", "properties": tool.input_schema},
                )
            )

        # Get model from environment variable or use default
        model = os.environ.get("ANTHROPIC_MODEL", DEFAULT_MODEL)

        try:
            # Call the Anthropic API
            response = self.client.messages.create(
                model=model,
                max_tokens=1024,
                messages=messages,
                tools=anthropic_tools,
            )
            return response.model_dump()
        except Exception as e:
            # Handle API errors
            print(f"Error during inference: {str(e)}")
            return {
                "role": "assistant",
                "content": [{"type": "text", "text": "Error during inference."}],
            }


# TOOL IMPLEMENTATIONS


@register_tool(
    name="read_file",
    description="Read the contents of a given relative file path. Use this when you want to see what's inside a file. Do not use this with directory names.",
    input_schema={
        "path": {
            "type": "string",
            "description": "The relative path of a file in the working directory.",
        }
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

    try:
        with open(path, "r", encoding="utf-8") as file:
            content = file.read()
        return content, None
    except Exception as e:
        return "", e


@register_tool(
    name="list_files",
    description="List files and directories at a given path. If no path is provided, lists files in the current directory.",
    input_schema={
        "path": {
            "type": "string",
            "description": "Optional relative path to list files from. Defaults to current directory if not provided.",
        }
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
                        files.append(
                            f"{rel_path}/"
                        )  # Add trailing slash to directories
                    else:
                        files.append(rel_path)

        return json.dumps(files), None
    except Exception as e:
        return "", e


@register_tool(
    name="edit_file",
    description="""Make edits to a text file.
    Replaces 'old_str' with 'new_str' in the given file. 'old_str' and 'new_str' MUST be different from each other.
    If the file specified with path doesn't exist, it will be created.
    """,
    input_schema={
        "path": {"type": "string", "description": "The path to the file"},
        "old_str": {
            "type": "string",
            "description": "Text to search for - must match exactly and must only have one match exactly",
        },
        "new_str": {"type": "string", "description": "Text to replace old_str with"},
    },
)
def edit_file(input_data: Dict[str, Any]) -> Tuple[str, Optional[Exception]]:
    """
    Edit a text file by replacing text or create a new file.

    Args:
        input_data: Dictionary containing 'path', 'old_str', and 'new_str' keys

    Returns:
        Tuple of (success_message, None) on success or ("", error) on failure
    """
    path = input_data.get("path", "")
    old_str = input_data.get("old_str", "")
    new_str = input_data.get("new_str", "")

    # Validate inputs
    if not path or old_str == new_str:
        return "", Exception("invalid input parameters")

    try:
        try:
            # Try to read the existing file
            with open(path, "r", encoding="utf-8") as file:
                content = file.read()
        except FileNotFoundError:
            # Handle case where file doesn't exist
            if old_str == "":
                # Create a new file if old_str is empty
                return create_new_file(path, new_str)
            return "", Exception(f"File not found: {path}")

        # Replace the text
        new_content = content.replace(old_str, new_str)

        # Check if any replacements were made
        if content == new_content and old_str:
            return "", Exception("old_str not found in file")

        # Write the modified content
        with open(path, "w", encoding="utf-8") as file:
            file.write(new_content)

        return "OK", None
    except Exception as e:
        return "", e


def create_new_file(file_path: str, content: str) -> Tuple[str, Optional[Exception]]:
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
        dir_path = os.path.dirname(file_path)
        if dir_path and dir_path != ".":
            os.makedirs(dir_path, exist_ok=True)

        # Write the content to the file
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(content)

        return f"Successfully created file {file_path}", None
    except Exception as e:
        return "", Exception(f"Failed to create file: {str(e)}")


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


def main():
    """
    Main entry point of the program.

    Initializes the Anthropic client and agent, then starts the agent's main loop.
    Handles top-level exceptions to prevent crashes.
    """
    client = anthropic.Anthropic()  # Initialize the Anthropic API client

    # Create the agent with the Anthropic client, user input function, and tool registry
    agent = Agent(client, get_user_message, tool_registry)

    try:
        # Start the agent's conversation loop
        agent.run()
    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    main()
