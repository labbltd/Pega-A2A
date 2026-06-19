# ComplaintAssistant

A Pega A2A complaint assistant proxy agent built with Google ADK.

This repository contains a small agent that forwards user input to a Pega A2A complaint case engine and returns responses verbatim. It is designed for local CLI testing and demonstration of a Pega agent integration.

## Features

- Authenticate with Pega using OAuth2 client credentials
- Fetch Pega agent interaction metadata
- Start a complaint session with Pega
- Forward user replies to Pega and return the agent response
- CLI interface for local testing

## Project structure

- `agent.py` — main implementation, agent tools, and CLI entry point
- `__init__.py` — package initializer
- `.env` — optional environment file for secrets/configuration
- `.adk/` — Google ADK runtime metadata

## Requirements

- Python 3.10+ (recommended)
- `requests`
- `google-adk`
- `google-genai`

## Installation

```bash
cd /path/to/ComplaintAssistant
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install requests google-adk google-genai
```

> If you have a project-specific `requirements.txt`, install that instead.

## Configuration

The current implementation uses constants in `agent.py` to configure Pega endpoints and credentials.

Update the following values as needed:

- `PEGA_BASE_URL`
- `PEGA_TOKEN_URL`
- `PEGA_AGENT_CARD_URL`
- `PEGA_CLIENT_ID`
- `PEGA_CLIENT_SECRET`
- `GOOGLE_MODEL`

For better security, move credentials to environment variables or a secure secrets store.

## Usage

Run the agent locally:

```bash
python agent.py
```

Then interact with the CLI:

- Say `hello` or `hey` to start the conversation
- Request to raise or log a complaint to trigger Pega session creation
- Reply to prompts from the agent
- Type `exit`, `quit`, or `bye` to end the session

## Behavior

This agent is intentionally a pass-through proxy:

- It does not collect complaint fields itself
- It simply forwards user responses to the Pega backend
- It repeats Pega's responses verbatim to the user

## Notes

- The current code prints debug logs for token fetching, agent card retrieval, and request payloads.
- Use this repository as a starting point for a more robust integration or a web-based UI.
- Ensure Pega API credentials are kept private and not committed to version control.
- Sample env content is below
    GOOGLE_GENAI_USE_VERTEXAI=FALSE
    GOOGLE_API_KEY=AQ.Ab8RN6JjZ62-dfgsdgsgKSxXPKxstSG-xPHgQ

## License

Add license information here if needed.