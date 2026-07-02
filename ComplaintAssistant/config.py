
# ============================================================================
# ⚙️  CONFIGURATION
# ============================================================================

import os
from dotenv import load_dotenv

load_dotenv()  # loads .env when running locally; no-op in Docker (env vars already set)

PEGA_BASE_URL       = os.environ["PEGA_BASE_URL"]
PEGA_TOKEN_URL      = f"{PEGA_BASE_URL}/prweb/PRRestService/oauth2/v1/token"
PEGA_AGENT_CARD_URL = os.environ["PEGA_AGENT_CARD_URL"]

PEGA_CLIENT_ID     = os.environ["PEGA_CLIENT_ID"]
PEGA_CLIENT_SECRET = os.environ["PEGA_CLIENT_SECRET"]

GOOGLE_MODEL    = os.environ.get("GOOGLE_MODEL", "gemini-3.5-flash")
REQUEST_TIMEOUT = int(os.environ.get("REQUEST_TIMEOUT", "30"))

STATE_CONTEXT_ID = "pega_context_id"
STATE_OPENED     = "pega_session_open"