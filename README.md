# Telegram AI E-commerce Assistant

An Arabic-language Telegram bot for interacting with an e-commerce catalog and managing customer orders. The bot uses a locally hosted Ollama model to interpret messages, an MCP server to expose store operations, and PostgreSQL to store products and orders.

## Features

- Search the product catalog using Arabic or English queries.
- Create orders using a product SKU.
- Check order status and cancel eligible orders.
- List orders associated with a Telegram user.
- Run language-model inference locally through Ollama.

## Architecture

```text
Telegram user
    │
    ▼
Telegram bot ──► Ollama (llama3)
    │
    ▼
MCP server ──► PostgreSQL
```

The Telegram client starts the MCP server as a subprocess. The server provides the store tools and reads database and Telegram configuration from environment variables.

## Tech Stack

- Python 3.14
- [uv](https://docs.astral.sh/uv/) for Python project and dependency management
- [python-telegram-bot](https://python-telegram-bot.org/)
- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)
- [Ollama](https://ollama.com/) with the `llama3` model
- PostgreSQL

## Requirements

Before running the project, install or configure:

- Python 3.14
- `uv`
- PostgreSQL, with a database user that can create the project database during initial setup
- Ollama, with the `llama3` model available locally
- A Telegram bot token created through [BotFather](https://t.me/BotFather)

## Getting Started

### 1. Clone the repository

```bash
git clone <repository-url>
cd <repository-directory>
```

### 2. Install dependencies

```bash
uv sync
```

### 3. Download the Ollama model

```bash
ollama pull llama3
```

Ensure the Ollama service is running before starting the bot.

### 4. Configure environment variables

Create a `.env` file in the project root:

```dotenv
DB_USER=your_postgres_user
DB_PASSWORD=your_postgres_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ecommerce
TELEGRAM_TOKEN=your_telegram_bot_token
```

Use your own PostgreSQL credentials and Telegram token. The `.env` file is excluded from Git; never commit secrets or production credentials.

### 5. Initialize the database and sample catalog

```bash
uv run python db_functions_test.py
```

This script creates the configured database and tables, then inserts sample products. Run it with a PostgreSQL account that has permission to create the database.

### 6. Start the bot

```bash
uv run python ecommerce_Telegram_client.py
```

The bot starts polling for text messages and launches the MCP server when it handles requests. Press `Ctrl+C` to stop the process.

## Example Requests

Try sending messages such as:

- “Show me Samsung phones.”
- “I want to order product SAM-S24-BLK.”
- “What is the status of order ORD-2026-00001?”
- “Cancel order ORD-2026-00001.”
- “Show me my orders.”

## Project Structure

| File | Description |
|---|---|
| `ecommerce_Telegram_client.py` | Telegram bot entry point and integration with Ollama and the MCP server. |
| `ecommerce_server.py` | MCP server, store resources, and product and order tools. |
| `db_functions.py` | PostgreSQL database, table, and product initialization helpers. |
| `db_functions_test.py` | Database setup script and sample product data. |
| `ecommerce_data.txt` | Store information included in bot responses. |

## Configuration and Security

- Keep PostgreSQL and Ollama available while the bot is running.
- Treat the sample catalog as development data; replace it with your own catalog before deployment.
- Keep `.env` out of version control and use appropriately restricted PostgreSQL credentials.
- Do not expose your Telegram bot token in logs, screenshots, or public repositories.
