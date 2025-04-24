# 🧙‍♂️ Sage
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

An interactive AI assistant powered by Anthropic's Claude that performs various automation tasks through natural language commands, including file operations, web scraping, and more.

## 📋 Overview
Sage bridges the gap between AI capabilities and system automation. With a simple chat interface, you can ask Sage to read and modify files, scrape web content, gather information, generate code, and perform a variety of tasks—all using natural language instructions.

## ✨ Features
- **Interactive Chat Interface**: Communicate with Anthropic Claude models conversationally
- **File System Operations**:
  - Read file contents (code, text, configuration files)
  - List and navigate directories
  - Edit existing files with precise text replacements
  - Create new files with AI-generated content
- **Web Integration**:
  - Scrape content from websites
  - Extract text, HTML, or links from web pages
  - Process online information for analysis
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
   echo "ANTHROPIC_MODEL=claude-3-7-sonnet-latest" >> .env  # Update to newest model
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

### `web_scraper`
Scrapes content from websites, with options to extract text, HTML, or links from specific page elements.

**Example:** "Scrape the main article content from this URL" or "Extract all links from the navigation menu at example.com"

**Real-world Example:**
<pre>Activating virtual environment and starting program...
Using model: claude-3-7-sonnet-latest
Available embedded tools: ['str_replace_editor']
Available custom tools: ['read_file', 'list_files', 'edit_file', 'web_scraper']
Chat with Claude (use 'ctrl-c' to quit)

🧑 <span style="color:blue;"><b>You:</b></span> what is the current price of VTI ETF?
🤖 <span style="color:yellow;"><b>Claude:</b></span> I'll help you find the current price of the VTI ETF (Vanguard Total Stock Market ETF). Let me retrieve this information from a financial website.
🔧 <span style="color:green;"><b>tool:</b></span> web_scraper({"url": "https://finance.yahoo.com/quote/VTI"})
🤖 <span style="color:yellow;"><b>Claude:</b></span> Based on the information I retrieved from Yahoo Finance, the current price of VTI (Vanguard Total Stock Market Index Fund ETF) is:

- Current price: $264.39 (after hours price as of April 23)
- Regular market close price: $263.44 (+$4.41, +1.70%)

Additional information about VTI:
- Previous close: $259.03
- Day's range: $262.60 - $268.38
- 52-week range: $236.42 - $303.39
- Volume: 6,807,935
- Expense ratio: 0.03%
- Yield: 1.36%

This is the Vanguard Total Stock Market ETF that tracks the performance of the entire U.S. stock market, including large-, mid-, small-, and micro-cap stocks.</pre>

### Embedded Tools
Sage also leverages Claude's built-in capabilities with embedded tools:

### `str_replace_editor`
A powerful embedded text editor tool available with Claude 3.5 Sonnet and newer models.

**Example:** "Create a complete React component with state management in src/components/Counter.jsx"

## 🌟 Demonstration: AI-Generated Documentation
Included in this repository is `runme_documentation.html`, an interactive HTML documentation file for the `runme.sh` script. This documentation was entirely generated by Sage itself with a simple prompt: "Create an interactive HTML documentation file for runme.sh". This demonstrates how easily Sage can create production-ready artifacts from natural language instructions.

Features of the generated documentation:
- Interactive dark/light mode toggle
- Collapsible sections with detailed explanations
- Syntax-highlighted code examples
- Visualized flowchart of the script execution
- Responsive design for all devices

To view the documentation:
```bash
# Open in default browser
xdg-open runme_documentation.html  # Linux
open runme_documentation.html      # macOS
```

This demonstrates how Sage can create complex, well-designed files from simple natural language requests.

## 📁 Project Structure
```
sage/
├── main.py                   # Main application code with agent implementation
├── tools/                    # Tool implementations
│   └── web_scraper.py        # Web scraping functionality
├── runme.sh                  # Setup and run script
├── runme_documentation.html  # AI-generated interactive documentation
├── requirements.txt          # Python dependencies
├── requirements_dev.txt      # Development dependencies
├── .gitignore                # Git ignore configuration
└── .env                      # Environment variables (not checked into git)
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

> **Pro tip:** The quality and clarity of your tool's description directly affects how effectively Claude can understand when and how to use it. More detailed descriptions lead to better tool utilization.

**Example Tool Implementation:**
```python
@register_tool(
    name="your_tool_name",
    description="Detailed description of what this tool does, when to use it, and any important considerations. The more specific and clear this description is, the better Claude will understand when and how to use this tool for appropriate tasks. Include examples of typical use cases if possible.",
    input_schema={
        "properties": {
            "param1": {
                "type": "string",
                "description": "Clear description of parameter 1's purpose and expected format"
            },
            "param2": {
                "type": "integer",
                "description": "Precise explanation of what parameter 2 represents and its valid range"
            }
        },
        "required": ["param1"]  # List parameters that are required
    },
)
def your_tool_name(input_data: Dict[str, Any]) -> Tuple[str, Optional[Exception]]:
    # Implement your tool logic here
    param1 = input_data.get("param1", "")

    try:
        # Do something useful
        result = f"Processed {param1}"
        return result, None
    except Exception as e:
        return "", e
```

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
