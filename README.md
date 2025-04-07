# KitchenSage

KitchenSage is a recipe and meal planning application that demonstrates how to build an AI agent using the Model Context Protocol (MCP) and fast-agent framework. This project provides a complete example of a recipe management system with a SQLite database backend and an AI agent interface.

## Overview

KitchenSage serves as a practical example of how to implement an MCP server that enables AI agents to interact with a structured database. The project includes:

- A SQLite database for storing recipes, ingredients, and meal plans
- An MCP server that exposes database operations as tools for AI agents
- A fast-agent implementation that uses these tools to provide recipe and meal planning assistance

## Features

- Recipe management with ingredients, directions, and categories
- Meal planning with consolidated shopping lists
- Flexible search capabilities for recipes and meal plans
- AI agent interface for natural language interaction

## Installation

### Prerequisites

- Python 3.10+
- uv package manager

### Setup

1. Clone the repository:

```bash
git clone https://github.com/yourusername/KitchenSagePy.git
cd KitchenSagePy
```

2. Create and activate a virtual environment:

```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

3. Install dependencies using uv:

```bash
pip install uv
uv pip install -r requirements.txt
```

## Project Structure

```
KitchenSagePy/
├── app/                    # Main application code
│   ├── mcp/                # MCP server implementation
│   │   ├── server.py       # MCP server definition
│   │   └── mcp_models.py   # Pydantic models for MCP
│   ├── models.py           # SQLAlchemy database models
│   ├── crud.py             # Database operations
│   ├── schemas.py          # Pydantic models for API
│   └── database.py         # Database connection
├── agent/                  # AI agent implementation
│   ├── agent.py            # fast-agent definition
│   └── fastagent.config.yaml  # Agent configuration
└── requirements.txt        # Project dependencies
```

## Running the MCP Server

The MCP server provides the interface between the AI agent and the database. To run the server:

```bash
cd app/mcp
uv run server.py
```

This will start the MCP server on the default transport (stdio).

## Running the AI Agent

The AI agent uses the fast-agent framework to interact with the MCP server. To run the agent:

```bash
cd agent
python agent.py
```

By default, the agent uses the Anthropic Claude Haiku model. You can specify a different model using the command line:

```bash
python agent.py --model=sonnet
```

Available model aliases include:
- Anthropic: haiku, haiku3, sonnet, sonnet35, opus, opus3
- OpenAI: gpt-4o-mini, gpt-4o, o1, o1-mini, o3-mini

## Agent Configuration

The agent is configured in `agent/fastagent.config.yaml`. This file specifies:

- The default AI model to use
- Logging configuration
- MCP server configuration

You can modify this file to change the agent's behavior or to add additional MCP servers.

## Example Usage

Once the agent is running, you can interact with it using natural language. Here are some example queries:

- "Find recipes that contain chicken and take less than 30 minutes to prepare."
- "Create a meal plan for the week with vegetarian dinners."
- "What ingredients do I need for my 'Weekly Dinner' meal plan?"
- "Add a new recipe for chocolate chip cookies."

## Extending the Project

### Adding New Recipe Tools

To add new functionality to the MCP server:

1. Define any necessary request/response models in `app/mcp/mcp_models.py`
2. Implement the tool function in `app/mcp/server.py` with the `@mcp.tool()` decorator
3. Document the tool in the MCP README

### Customizing the Agent

To customize the agent's behavior:

1. Modify the agent instruction in `agent/agent.py`
2. Add additional servers or change the configuration in `agent/fastagent.config.yaml`

## Resources

- [fast-agent Documentation](https://github.com/evalstate/fast-agent)
- [Model Context Protocol (MCP) Specification](https://github.com/mcp-lang/mcp)

## License

This project is licensed under the MIT License - see the LICENSE file for details.