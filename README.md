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
- **Code Execution**:
  - Run Python code in a sandboxed environment
  - Support for popular data science libraries (numpy, pandas, matplotlib, etc.)
  - Execute and test code snippets with visual outputs
- **Smart Configuration**:
  - Environment-based setup
  - Automatic virtual environment management
  - Model selection through environment variables
- **Workarea Management**:
  - Dedicated workspace for generated files
  - Optional cleanup of old files
  - Isolated environment for project operations

## 🔧 Prerequisites
- Python 3.11 or higher (specifically checks for Python 3.11)
- pip package manager
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
- Sets up a workarea directory for generated files
- Runs the application

## 🚀 Usage
1. Start Sage with optional flags:
   ```bash
   ./runme.sh                # Run with default settings
   ./runme.sh --keep-files   # Run without deleting old files
   ./runme.sh --help         # View all command options
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
<pre>🧑 <span style="color:blue;"><b>You:</b></span> What is the current price of VTI ETF?

🤖 <span style="color:yellow;"><b>Claude:</b></span> I'll help you find the current price of the VTI ETF (Vanguard Total Stock Market ETF). Let me retrieve this information from a financial website.

🔧 <span style="color:green;"><b>tool:</b></span> web_scraper({"url": "https://finance.yahoo.com/quote/VTI"})

🔧 <span style="color:green;"><b>tool execution result:</b></span>
[Page text content - omitted for brevity]

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

### `code_executor`
Executes Python code in a sandboxed environment and returns the results. Supports common data science libraries like numpy, pandas, matplotlib, and scipy.

**Example:** "Make a histogram from my data in myfile.csv" or "Plot the locations of the world's 20 most populated cities on a map with population indicators"

**Real-world Example 1:**
<pre>🧑 <span style="color:blue;"><b>You:</b></span> Generate a simple plot of sine and cosine waves

🤖 <span style="color:yellow;"><b>Claude:</b></span> I'll create a simple plot of sine and cosine waves using matplotlib. Let me execute the code for you.

🔧 <span style="color:green;"><b>tool:</b></span> code_executor({
  "code": "import numpy as np
import matplotlib.pyplot as plt

# Generate data points
x = np.linspace(0, 2*np.pi, 100)
y_sin = np.sin(x)
y_cos = np.cos(x)

# Create the plot
plt.figure(figsize=(10, 6))
plt.plot(x, y_sin, label='sin(x)', color='blue')
plt.plot(x, y_cos, label='cos(x)', color='red')

# Add labels and title
plt.xlabel('x')
plt.ylabel('y')
plt.title('Sine and Cosine Functions')
plt.legend()
plt.grid(True)

# Display the plot
plt.tight_layout()"
})

🔧 <span style="color:green;"><b>tool execution result:</b></span>
Matplotlib initialized successfully in non-interactive mode.

Plots saved to files: plot_0.png

1 plot(s) were generated.

🤖 <span style="color:yellow;"><b>Claude:</b></span> I've created a simple plot showing sine and cosine waves. The plot displays one complete cycle of both functions from 0 to 2π.

The graph shows:
- The sine wave (in blue) which starts at 0, rises to 1, falls to -1, and returns to 0
- The cosine wave (in red) which starts at 1, falls to -1, and rises back to 1

The plot includes proper labeling (x and y axes), a title, a legend identifying each function, and a grid for easier reading.

The plot has been saved as "plot_0.png" in your current directory. You can view it or use it in any documentation you're creating.

Is there anything specific about these trigonometric functions you'd like me to explain, or would you like me to modify the plot in any way?</pre>

**Real-world Example 2:**
<pre>🧑 <span style="color:blue;"><b>You:</b></span> Plot the locations of the world's 20 most populated cities on a map with population indicators

🤖 <span style="color:yellow;"><b>Claude:</b></span> I'll create a world map showing the 20 most populated cities with indicators for their populations. Let me write and execute the code for this visualization.

🔧 <span style="color:green;"><b>tool:</b></span> code_executor({
  "code": [Omitted for brevity]
})

🔧 <span style="color:green;"><b>tool execution result:</b></span>
Matplotlib initialized successfully in non-interactive mode.

Plots saved to files: plot_0.png

1 plot(s) were generated.

🤖 <span style="color:yellow;"><b>Claude:</b></span> The map has been successfully created. Let me explain what the visualization shows:

### World's 20 Most Populated Cities Map Visualization

I've created a world map displaying the locations of the 20 most populated cities in the world with population indicators. Here's what the visualization includes:

1. **Base Map**: A global map with continents in light gray and oceans in light blue. Country borders and coastlines are displayed for better geographical context.

2. **City Markers**: Each city is represented by a red circle whose size is proportional to its population - larger circles indicate larger populations.

3. **City Labels**: Each city is clearly labeled with its name.

4. **Population Indicators**: Below each city name, the population is shown in millions (e.g., "37.4 M" for Tokyo).

5. **Legend**: A legend in the lower left corner of the map indicates what marker sizes correspond to different population levels.

6. **Title**: The map is titled "World's 20 Most Populated Cities by Population (in millions)".

### Featured Cities and Their Populations

The map displays these major urban centers with their approximate populations in millions:

1. Tokyo, Japan (37.4 million)
2. Delhi, India (31.1 million)
3. Shanghai, China (27.1 million)
4. São Paulo, Brazil (22.0 million)
5. Mexico City, Mexico (21.8 million)
6. Cairo, Egypt (21.3 million)
7. Mumbai, India (20.7 million)
8. Beijing, China (20.5 million)
9. Dhaka, Bangladesh (20.3 million)
10. Osaka, Japan (19.2 million)
11. New York, United States (18.8 million)
12. Karachi, Pakistan (16.1 million)
13. Chongqing, China (15.9 million)
14. Istanbul, Turkey (15.2 million)
15. Buenos Aires, Argentina (15.1 million)
16. Kolkata, India (14.9 million)
17. Lagos, Nigeria (14.4 million)
18. Manila, Philippines (14.0 million)
19. Guangzhou, China (13.6 million)
20. Rio de Janeiro, Brazil (13.6 million)

The visualization offers a clear global perspective on where the world's largest urban populations are concentrated, with particular density in Asia (especially East and South Asia), followed by significant population centers in the Americas, Africa, and Europe.</pre>

### Embedded Tools
Sage also leverages Claude's built-in capabilities with embedded tools:

### `str_replace_editor`
A powerful embedded text editor tool available with Claude 3.5 Sonnet and newer models.

**Example:** "Create a complete React component with state management in src/components/Counter.jsx"

## 🌟 Demonstration: AI-Generated Examples
Included in this repository is an interactive HTML documentation file for the `runme.sh` script and a world map visualization. These examples were entirely generated by Sage itself with simple prompts like: "Create an interactive HTML documentation file for runme.sh" and "Plot the locations of the world's 20 most populated cities on a map with population indicators". This demonstrates how easily Sage can create production-ready artifacts from natural language instructions.

To view the examples:
```bash
# Open HTML documentation in default browser
xdg-open examples/runme_documentation.html  # Linux
open examples/runme_documentation.html      # macOS

# Open world map visualization in default image viewer
xdg-open examples/world_most_populated_cities.png  # Linux
open examples/world_most_populated_cities.png      # macOS
```

These examples demonstrate how Sage can create complex, well-designed files from simple natural language requests.

## 📁 Project Structure
```
sage/
├── examples/                            # Example files generated by Sage
│   ├── runme_documentation.html         # Sage-generated interactive documentation
│   └── world_most_populated_cities.png  # Sage-generated map of most populated cities
├── tools/                               # Tool implementations
│   ├── __init__.py                      # Package initializer for tools module
│   ├── code_executor.py                 # Python code execution in sandbox
│   └── web_scraper.py                   # Web scraping functionality
├── workarea/                            # Directory for generated files and workspace
├── .env                                 # Environment variables (not checked into git)
├── .gitignore                           # Git ignore configuration
├── common.py                            # Common utility functions (colored text output)
├── LICENSE                              # MIT license file
├── main.py                              # Main application code with agent implementation
├── README.md                            # Project documentation (this file)
├── requirements_dev.txt                 # Development dependencies
├── requirements.txt                     # Python dependencies
└── runme.sh                             # Setup and run script
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

### Understanding the Workarea
The workarea directory is where Sage:
- Runs the main program
- Stores generated files
- Maintains workspace isolation
- Can clean up old files automatically (files older than 7 days)

This directory is also exposed to the Python environment as the `SAGE_WORKAREA` environment variable.

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
