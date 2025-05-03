"""
Web interface for Sage assistant using Flask and WebSockets.
"""

import json
import os
import tempfile
import threading
import uuid
from pathlib import Path
from queue import Queue
from typing import Dict

import anthropic
from dotenv import load_dotenv
from flask import (
    Flask,
    render_template,
    request,
)
from flask_socketio import (
    SocketIO,
    emit,
)

from common import (
    print_blue,
    print_green,
    print_red,
)

# Import from existing Sage modules
from main import (
    DEFAULT_MODEL,
    Agent,
    tool_registry,
)

# Load environment variables
load_dotenv()

# Store active sessions
active_sessions: Dict[str, "WebAgent"] = {}


class WebAgent(Agent):
    """Modified Agent for web interface that sends output via WebSockets"""

    def __init__(self, client, session_id, registry, socketio_instance):
        """Initialize the WebAgent with a client, session ID, and tool registry"""
        super().__init__(client=client, input_handler=session_id, registry=tool_registry)
        self.session_id = session_id
        self.output_queue = Queue()
        self.conversation = []
        self.client = client
        self.tool_registry = registry
        self.socketio = socketio_instance

    def send_message(self, message_type, content):
        """Send a message to the client via WebSockets"""
        # Use the instance's socketio reference
        self.socketio.emit(
            event="message", data={"type": message_type, "content": content}, to=self.session_id
        )

    def process_user_message(self, user_input):
        """Process a message from the user"""
        # Format user message for the conversation history
        user_message = {
            "role": "user",
            "content": [{"type": "text", "text": user_input}],
        }
        self.conversation.append(user_message)

        # Process the message and get AI responses
        self.process_conversation()

    def process_conversation(self):
        """Process the current conversation state"""
        # Get AI response based on conversation history
        message = self.run_inference(conversation=self.conversation)
        self.conversation.append(message)

        # Process AI response content
        tool_results = []
        for content in message.get("content", []):
            content_type = content.get("type")
            if content_type == "text":
                # Send text responses from the AI to the client
                self.send_message(message_type="assistant", content=content.get("text", ""))
            elif content_type == "tool_use":
                # Execute tools requested by the AI
                tool_name = content.get("name", "")
                input_data = content.get("input", {})

                # Send tool execution notification
                self.send_message(
                    message_type="tool_start",
                    content={
                        "name": tool_name,
                        "input": json.dumps(input_data, indent=2, ensure_ascii=False),
                    },
                )

                # Execute the tool
                result = self.execute_tool(
                    id_str=content.get("id", ""),
                    name=tool_name,
                    input_data=input_data,
                )

                # Send tool results to the client
                self.send_message(message_type="tool_result", content=result.get("content", ""))

                # Always include tool results to satisfy the API requirement
                tool_results.append(result)

        # If tools were executed, continue processing with tool results
        if tool_results:
            # Create a well-formed content message with tool results
            self.conversation.append({"role": "user", "content": tool_results})
            # Continue processing
            self.process_conversation()

    # Override execute_tool to send notifications via WebSockets
    def execute_tool(self, id_str, name, input_data):
        result = super().execute_tool(id_str=id_str, name=name, input_data=input_data)
        return result


def create_index_html(path: Path) -> bool:
    """Create the index.html file for the web interface"""
    try:
        with open(file=path, mode="w", encoding="utf-8") as f:
            f.write(
                """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sage AI Assistant</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f8f9fa;
        }
        .chat-container {
            height: calc(100vh - 180px);
            overflow-y: auto;
            padding: 20px;
            background-color: white;
            border-radius: 10px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }
        .user-message {
            background-color: #e3f2fd;
            padding: 10px 15px;
            border-radius: 15px;
            margin-bottom: 10px;
            max-width: 80%;
            margin-left: auto;
            text-align: right;
        }
        .assistant-message {
            background-color: #f0f4c3;
            padding: 10px 15px;
            border-radius: 15px;
            margin-bottom: 10px;
            max-width: 80%;
        }
        .tool-message {
            background-color: #e8eaf6;
            padding: 10px 15px;
            border-radius: 15px;
            margin-bottom: 10px;
            max-width: 80%;
            font-family: monospace;
        }
        .tool-result-message {
            background-color: #e0f2f1;
            padding: 10px 15px;
            border-radius: 15px;
            margin-bottom: 10px;
            max-width: 80%;
            font-family: monospace;
            white-space: pre-wrap;
        }
        .input-group {
            margin-top: 20px;
        }
        pre {
            white-space: pre-wrap;
        }
    </style>
</head>
<body>
    <div class="container mt-4">
        <h1 class="text-center mb-4">🧙‍♂️ Sage AI Assistant</h1>
        <div class="row">
            <div class="col-md-12">
                <div class="chat-container" id="chat-container">
                    <div class="assistant-message">
                        Hello! I'm Sage, your AI assistant. How can I help you today?
                    </div>
                </div>
                <div class="input-group">
                    <input type="text" class="form-control" placeholder="Type your message here..." id="user-input">
                    <button class="btn btn-primary" id="send-btn">Send</button>
                </div>
                <div class="mt-2">
                    <span class="badge bg-secondary" id="model-info"></span>
                    <span id="typing-indicator" class="d-none">
                        <span class="spinner-grow spinner-grow-sm"></span> Thinking...
                    </span>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.socket.io/4.4.1/socket.io.min.js"></script>
    <script>
        const socket = io();
        const chatContainer = document.getElementById('chat-container');
        const userInput = document.getElementById('user-input');
        const sendButton = document.getElementById('send-btn');
        const typingIndicator = document.getElementById('typing-indicator');
        const modelInfo = document.getElementById('model-info');

        // Handle session initialization
        socket.on('session_init', function(data) {
            console.log('Session initialized:', data);
            modelInfo.textContent = `Model: ${data.model}`;
        });

        // Handle incoming messages
        socket.on('message', function(data) {
            typingIndicator.classList.add('d-none');

            let messageDiv = document.createElement('div');

            switch(data.type) {
                case 'assistant':
                    messageDiv.className = 'assistant-message';
                    messageDiv.textContent = data.content;
                    break;

                case 'tool_start':
                    messageDiv.className = 'tool-message';
                    messageDiv.innerHTML = `<strong>Tool:</strong> ${data.content.name}<br><pre>${data.content.input}</pre>`;
                    break;

                case 'tool_result':
                    messageDiv.className = 'tool-result-message';
                    messageDiv.innerHTML = `<strong>Tool Result:</strong><br><pre>${data.content}</pre>`;
                    break;

                default:
                    messageDiv.className = 'system-message';
                    messageDiv.textContent = JSON.stringify(data);
            }

            chatContainer.appendChild(messageDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        });

        // Send message function
        function sendMessage() {
            const message = userInput.value.trim();
            if (message) {
                // Add user message to chat
                let userMessageDiv = document.createElement('div');
                userMessageDiv.className = 'user-message';
                userMessageDiv.textContent = message;
                chatContainer.appendChild(userMessageDiv);

                // Show typing indicator
                typingIndicator.classList.remove('d-none');

                // Send message to server
                socket.emit('message', {message: message});

                // Clear input field
                userInput.value = '';

                // Scroll to bottom
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }
        }

        // Event listeners
        sendButton.addEventListener('click', sendMessage);
        userInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    </script>
</body>
</html>
              """
            )
    except Exception as e:  # pylint: disable=broad-except
        print_red(f"Error creating index.html: {e}")
        return False
    return True


def init_routes(app, socketio):
    """Initialize routes and socket handlers after app is created"""

    @app.route("/")
    def index():
        """Render the main page"""
        return render_template(template_name_or_list="index.html")

    @socketio.on("connect")
    def handle_connect():
        """Handle client connection"""
        session_id = request.sid  # type: ignore
        # Initialize Anthropic client
        client = anthropic.Anthropic()
        # Create new agent for this session
        active_sessions[session_id] = WebAgent(
            client=client, session_id=session_id, registry=tool_registry, socketio_instance=socketio
        )
        # Notify client of available tools
        model = os.environ.get("ANTHROPIC_MODEL", DEFAULT_MODEL)
        model_compatible_tools = [
            tool.name
            for tool in tool_registry.get_all_tools()
            if not tool.compatible_models
            or any(compatible_model in model for compatible_model in tool.compatible_models)
        ]
        emit(
            "session_init",
            {
                "session_id": session_id,
                "model": model,
                "tools": model_compatible_tools,
            },
        )

    @socketio.on("disconnect")
    def handle_disconnect():
        """Handle client disconnection"""
        session_id = request.sid  # type: ignore
        if session_id in active_sessions:
            del active_sessions[session_id]

    @socketio.on("message")
    def handle_message(data):
        """Handle incoming messages from the client"""
        session_id = request.sid  # type: ignore
        agent = active_sessions.get(session_id)
        if agent:
            user_input = data.get("message", "")
            # Process in a separate thread to avoid blocking
            threading.Thread(target=agent.process_user_message, args=(user_input,)).start()


def main() -> None:
    """Main function to run the web interface"""

    # Create a temporary directory for the web interface
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create templates directory
        templates_dir = Path(temp_dir) / "templates"
        templates_dir.mkdir(exist_ok=True)

        index_path = templates_dir / "index.html"

        # Create the index.html file
        if not create_index_html(path=index_path):
            print_red("Failed to create index.html")
            exit()
        print_blue(f"Web interface files created at {temp_dir}")

        # Initialize Flask app with the temporary directory
        app = Flask(__name__, template_folder=templates_dir)
        app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY") or str(uuid.uuid4())
        socketio = SocketIO(app=app, cors_allowed_origins="*")

        # Initialize routes after app is created
        init_routes(app=app, socketio=socketio)

        # Start the Flask app with Socket.IO
        print_green("\nWeb interface running at http://localhost:5000")
        socketio.run(app=app, host="0.0.0.0", port=5000, debug=False)


if __name__ == "__main__":
    main()
