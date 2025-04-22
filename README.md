# 🧙‍♂️ Sage
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

An interactive AI assistant powered by Anthropic's Claude that performs file operations on your local system through natural language commands.

## 📋 Overview
Sage bridges the gap between AI capabilities and local file system operations. With a simple chat interface, you can ask Sage to read files, create new code, modify existing files, and navigate your filesystem—all using natural language instructions.

### Why Sage?
- **Simplified Development Workflow**: Perform common file operations without leaving your terminal
- **Natural Language Interface**: No need to remember complex command syntax
- **Powered by Claude**: Leverage advanced AI understanding for accurate and helpful responses

## ✨ Features
- **Interactive Chat Interface**: Communicate with Anthropic Claude models conversationally
- **File System Operations**:
  - Read file contents (code, text, configuration files)
  - List and navigate directories
  - Edit existing files with precise text replacements
  - Create new files with AI-generated content
- **Smart Configuration**:
  - Environment-based setup
  - Automatic virtual environment management
  - Model selection through environment variables

## 🔧 Prerequisites
- Python 3.11 or higher
- An Anthropic API key ([Get one here](https://console.anthropic.com/))
- Linux/macOS/WSL terminal environment

## 📦 Installation
1. Clone this repository:
   ```bash
   git clone https://github.com/ecelab-org/sage.git
   cd sage
   ```

2. Create a `.env` file in the root directory:
   ```bash
   # Add your Anthropic API key and preferred model
   echo "ANTHROPIC_API_KEY=your-anthropic-api-key" > .env
   echo "ANTHROPIC_MODEL=claude-3-5-haiku-20241022" >> .env
   ```

3. Run the provided setup and start script:
   ```bash
   ./runme.sh
   ```

The script automatically:
- Creates a virtual environment if one doesn't exist
- Installs all required dependencies from requirements.txt
- Runs the application

## 🚀 Usage
1. Start Sage:
   ```bash
   ./runme.sh
   ```

2. Chat with Sage using natural language. Examples:
   ```
   List all Python files in the src directory
   ```
   ```
   Create a new file called hello.py that prints "Hello, World!" and accepts a name parameter
   ```
   ```
   Guide me through the contents of main.py and explain what it does
   ```
   ```
   Find and fix syntax errors in app.js
   ```

3. Press `Ctrl+C` to exit the application.

## 🛠️ Available Tools
Sage comes with several built-in tools to interact with your file system:

### `read_file`
Reads the contents of a file at a specified path.

**Example:** "Show me what's in requirements.txt"

### `list_files`
Lists all files and directories at a given path.

**Example:** "List all files in the project" or "Show me all Python files in the src directory"

### `edit_file`
Makes changes to text files by replacing specified content. Can also create new files.

**Example:** "Create a new file called app.py with a Flask hello world app" or "In main.py, replace the print statement with a logging statement"

## 📁 Project Structure
```
sage/
├── main.py                # Main application code with agent implementation
├── runme.sh               # Setup and run script
├── requirements.txt       # Python dependencies
├── requirements_dev.txt   # Development dependencies
└── .env                   # Environment variables (not checked into git)
```

## 💻 Development
### Setting Up Development Environment
1. Install development tools:
   ```bash
   pip install -r requirements_dev.txt
   ```

2. Development tools included:
   - **mypy**: Static type checking
   - **black**: Code formatting

### Adding New Tools
You can extend Sage with new tools by following the pattern in `main.py`:

1. Create a function that implements your tool logic
2. Use the `@register_tool` decorator to define the tool's name, description, and input schema
3. Return results as a tuple of (result_string, optional_exception)

## 🔍 Troubleshooting
- **API Key Issues**: Ensure your Anthropic API key is correctly set in the `.env` file
- **Python Version**: Verify you're using Python 3.11+ with `python --version`
- **Permission Denied**: Make sure `runme.sh` is executable (`chmod +x runme.sh`)

## 🚧 Roadmap
- Web UI interface
- Support for more complex file operations
- Integration with version control systems
- Expanded tool catalog

## 📄 License
This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
