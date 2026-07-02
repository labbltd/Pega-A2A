# Complaint Assistant — Pega A2A Agent

Google ADK agent that connects to Pega Case Management via the A2A protocol.

---

## Prerequisites

- Docker + Docker Compose
- A Pega instance with the A2A / IntakeAgent configured
- A Google API key with Gemini access

---

## Setup

1. **Clone / copy** the project files into a folder named `ComplaintAssistant/`.

2. **Create your `.env`** from the template:
   ```bash
   cp .env.example .env
   ```
   Then edit `.env` and fill in your values:
   ```
   PEGA_BASE_URL=https://your-pega-instance.pegalabs.io
   PEGA_AGENT_CARD_URL=https://your-pega-instance.pegalabs.io/prweb/PRAuth/app/AIR/api/agent2agent/v1/ai-agents/@BASECLASS%21INTAKEAGENT/.well-known/agent.json
   PEGA_CLIENT_ID=your_client_id
   PEGA_CLIENT_SECRET=your_client_secret
   GOOGLE_API_KEY=your_google_api_key
   ```

3. **Build and run**:
   ```bash
   docker compose up --build
   ```

4. Open the ADK web UI at **http://localhost:8000**

---

## Running in CLI mode

To run interactively in the terminal instead of the web UI, first install dependencies:

```bash
pip install -r requirements.txt
```

Then run:

```bash
python agent.py
```

---

## Project structure

```
ComplaintAssistant/
├── agent.py            # ADK agent — tools, root_agent, CLI entrypoint
├── config.py           # Reads all settings from environment variables
├── requirements.txt    # Python dependencies
├── Dockerfile          # Container image definition
├── docker-compose.yml  # One-command run with env file wiring
├── .env.example        # Template — copy to .env and fill in secrets
├── .dockerignore       # Keeps .env and cache out of the image
└── README.md           # This file
```

---

## Environment variables

| Variable              | Required | Default           | Description                                      |
|-----------------------|----------|-------------------|--------------------------------------------------|
| PEGA_BASE_URL         | ✅       | —                 | Base URL of your Pega instance                   |
| PEGA_AGENT_CARD_URL   | ✅       | —                 | Full URL to the Pega IntakeAgent agent.json card |
| PEGA_CLIENT_ID        | ✅       | —                 | OAuth2 client ID                                 |
| PEGA_CLIENT_SECRET    | ✅       | —                 | OAuth2 client secret                             |
| GOOGLE_API_KEY        | ✅       | —                 | Google API key for Gemini                        |
| GOOGLE_MODEL          | ❌       | gemini-3.5-flash  | Gemini model name                                |
| REQUEST_TIMEOUT       | ❌       | 30                | HTTP timeout in seconds                          |

---

## Pega IntakeAgent instruction

The Pega-side IntakeAgent must be configured with the following instruction for the end-to-end flow to work correctly. Without this, the Pega agent may close cases prematurely, skip screens, or ask unnecessary confirmation questions.

```
ROLE: You are a dynamic form-intake utility that processes Pega case assignments
step-by-step. You do not know the fields in advance; you must inspect the current
assignment screen metadata dynamically.

STRICT EXECUTION PROTOCOLS:

1. INSPECT SCREEN: On every user turn, dynamically read the active assignment screen
   payload. Identify all input fields presented on this specific screen.

2. FIELD COLLECT LOOP: Look at the values mapped to the current screen's fields:
   - If ANY field on the current screen is empty or missing data, you MUST stop.
     Pick the first empty field and ask the user for it using a single, clear question.
   - Do NOT submit the assignment, do NOT advance the stage, and do NOT generate a
     case confirmation reference if there are unfulfilled fields on the active screen.

3. SUBMIT GATE: You are ONLY permitted to execute a screen submission / assignment
   submit action when 100% of the data fields on the current active screen have been
   populated with user data.

4. NEXT SCREEN EVALUATION: After a valid submission, pause and immediately inspect
   the new assignment screen metadata that loads. Repeat the inspection process for
   any new fields. Keep doing this until ALL screens are complete.

5. CASE CONFIRMATION: Only share the case reference number AFTER every screen across
   the entire case flow has been submitted and there are no remaining assignment screens.

6. NO CONFIRMATION PROMPTS: Never ask the user to confirm or verify data you have
   already collected (e.g. "Does that sound right?", "Just to confirm..."). Accept
   what the user provides and move directly to the next empty field or next screen.

7. NO FILLER: Do not add conversational filler, summaries, apologies, or closing
   remarks ("Is there anything else I can help with?"). Keep responses strictly
   focused on extracting the next missing value.
```

---

## Security notes

- **Never commit `.env`** to source control — it contains your credentials.
- The Docker image itself contains no secrets; all credentials are injected at runtime via the env file.
- Add `.env` to your `.gitignore` if using a git repository.