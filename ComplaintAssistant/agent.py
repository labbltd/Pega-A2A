"""
Complaint Assistant Agent for Pega
Google ADK Agent with Pega A2A Case Management Integration

Place this file at:
  ComplaintAssistant/
      agent.py   ← this file

RUN:
    adk web          (from parent of ComplaintAssistant/)
    python agent.py  (CLI mode)
"""

import uuid
import time
import json
import requests
from google.adk.agents import Agent
from google.adk.tools import FunctionTool, ToolContext
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types


# ============================================================================
# ⚙️  CONFIGURATION
# ============================================================================

PEGA_BASE_URL       = "https://labbconsulting12.pegalabs.io"
PEGA_TOKEN_URL      = f"{PEGA_BASE_URL}/prweb/PRRestService/oauth2/v1/token"
PEGA_AGENT_CARD_URL = (
    f"{PEGA_BASE_URL}/prweb/PRAuth/app/AIR/api/agent2agent/v1"
    "/ai-agents/@BASECLASS%21INTAKEAGENT/.well-known/agent.json"
)

PEGA_CLIENT_ID     = "68771037755197166701"
PEGA_CLIENT_SECRET = "3F6F02DF5C2957D15331A77063FAE727"

GOOGLE_MODEL    = "gemini-3.5-flash"
REQUEST_TIMEOUT = 30

STATE_CONTEXT_ID = "pega_context_id"
STATE_OPENED     = "pega_session_open"


# ============================================================================
# AUTH + AGENT CARD
# ============================================================================

_cached_token:          str | None = None
_token_expiry:          float      = 0.0
_agent_interaction_url: str | None = None


def get_pega_access_token() -> str | None:
    global _cached_token, _token_expiry
    if _cached_token and time.time() < _token_expiry - 60:
        return _cached_token
    print("🔐 Fetching Pega access token...")
    try:
        r = requests.post(
            PEGA_TOKEN_URL,
            data={"grant_type": "client_credentials"},
            auth=(PEGA_CLIENT_ID, PEGA_CLIENT_SECRET),
            timeout=REQUEST_TIMEOUT,
        )
        if r.status_code == 200:
            data          = r.json()
            _cached_token = data.get("access_token")
            _token_expiry = time.time() + data.get("expires_in", 3600)
            print("✅ Token obtained")
            return _cached_token
        print(f"❌ Token failed [{r.status_code}]: {r.text}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Token exception: {e}")
        return None


def get_agent_interaction_url() -> str | None:
    global _agent_interaction_url
    if _agent_interaction_url:
        return _agent_interaction_url
    token = get_pega_access_token()
    if not token:
        return None
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    print("📋 Fetching Pega agent card...")
    try:
        r = requests.get(PEGA_AGENT_CARD_URL, headers=headers, timeout=REQUEST_TIMEOUT)
        if r.status_code == 200:
            card = r.json()
            print(f"   Agent card: {json.dumps(card, indent=2)}")
            _agent_interaction_url = card.get("url")
            if _agent_interaction_url:
                print(f"✅ Interaction URL: {_agent_interaction_url}")
                return _agent_interaction_url
            print("❌ Agent card has no 'url' field")
            return None
        print(f"❌ Agent card failed [{r.status_code}]: {r.text}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Agent card exception: {e}")
        return None


# ============================================================================
# LOW-LEVEL A2A SEND
# ============================================================================

def _a2a_send(message: str, context_id: str | None) -> dict:
    token = get_pega_access_token()
    if not token:
        return {"error": "Authentication failed"}

    interaction_url = get_agent_interaction_url()
    if not interaction_url:
        return {"error": "Could not resolve Pega interaction URL"}

    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}

    message_obj: dict = {
        "role":      "user",
        "parts":     [{"kind": "text", "text": message}],
        "messageId": str(uuid.uuid4()),
    }

    if context_id:
        message_obj["contextId"] = context_id

    params: dict = {
        "message": message_obj,
        "skill":   {"id": "@baseclass!Issue", "name": "Issue"},
    }

    if context_id:
        params["contextId"] = context_id

    if context_id:
        params["metadata"] = {"convId": context_id}

    payload = {
        "jsonrpc": "2.0",
        "id":      str(uuid.uuid4()),
        "method":  "message/send",
        "params":  params,
    }

    print(f"\n📤 A2A | context={'NEW' if not context_id else context_id}")
    print(f"   msg    : {message[:120]}")
    print(f"   payload: {json.dumps(payload, indent=2)}")

    try:
        r = requests.post(
            interaction_url, json=payload, headers=headers, timeout=REQUEST_TIMEOUT
        )
        print(f"   HTTP {r.status_code}")
        print(f"   response: {r.text[:800]}")
        if r.status_code != 200:
            return {"error": f"Pega HTTP {r.status_code}", "details": r.text}
        return _parse_response(r.json())
    except requests.exceptions.RequestException as e:
        return {"error": f"Connection error: {e}"}


def _parse_response(response: dict) -> dict:
    if "error" in response:
        return {
            "error": response["error"].get("message", "Unknown Pega error"),
            "code":  response["error"].get("code", ""),
        }

    result = response.get("result", {})
    context_id = result.get("contextId", "")

    status = result.get("status", {})
    state  = status.get("state", "")
    text   = ""
    for part in status.get("message", {}).get("parts", []):
        text += part.get("text", "")

    if not state:
        state = "working"
        if not text:
            for part in result.get("parts", []):
                text += part.get("text", "")

    if not text:
        text = str(result)

    print(f"   ↳ state={state} | ctx={context_id} | text={text[:200]}")
    return {"text": text, "context_id": context_id, "state": state}


# ============================================================================
# AGENT TOOLS
# ============================================================================

def open_pega_session(tool_context: ToolContext) -> dict:
    """
    Opens a new Pega complaint session. Call this ONCE at the very start.
    """
    print("\n🚀 open_pega_session called")
    opener = _a2a_send(message="I want to raise a complaint", context_id=None)

    if "error" in opener:
        return {"error": f"Could not open Pega session: {opener['error']}"}

    ctx = opener.get("context_id", "")
    if not ctx:
        return {"error": "Pega returned no context_id — cannot maintain session"}

    tool_context.state[STATE_CONTEXT_ID] = ctx
    tool_context.state[STATE_OPENED]     = True
    print(f"✅ Session opened | context_id={ctx}")

    return {
        "text":       opener.get("text", ""),
        "context_id": ctx,
        "state":      opener.get("state", "working"),
    }


def answer_pega(context_id: str, user_answer: str, tool_context: ToolContext) -> dict:
    """
    Sends the user's answer to Pega and returns the next screen.
    """
    print(f"\n📨 answer_pega called | context_id={context_id}")

    if not context_id:
        context_id = tool_context.state.get(STATE_CONTEXT_ID, "")
        if not context_id:
            return {
                "error": "No context_id available. Initialize session first."
            }

    result = _a2a_send(message=user_answer, context_id=context_id)

    new_ctx = result.get("context_id") or context_id
    tool_context.state[STATE_CONTEXT_ID] = new_ctx

    return {
        "text":       result.get("text", ""),
        "context_id": new_ctx,
        "state":      result.get("state", "working"),
        **( {"error": result["error"]} if "error" in result else {} ),
    }


# ============================================================================
# root_agent
# ============================================================================

root_agent = Agent(
    model=GOOGLE_MODEL,
    name="complaint_assistant",
    description="Pass-through router proxy for Pega A2A backend case engine.",
    instruction="""
You are a pure pass-through execution proxy for Pega Case Management. Pega has its own highly detailed instructions for managing fields, validation, and layout rules. Your only job is to route inputs to Pega and output Pega's responses word for word.

You have access to TWO tools:
  1. open_pega_session()
  2. answer_pega(context_id, user_answer)

=== STRICT ROUTING LAWS ===

1. INITIAL CONTACT:
   - When the user first says "Hello", "Hey", or similar, respond with a clean greeting and ask how you can help. Do NOT execute any tools yet.
   - Example: "Hello! I'm your complaint assistant. How can I help you today?"

2. TARGET TRIGGER (OPEN SESSION):
   - The MOMENT the user states they want to raise, create, or log a complaint, you MUST immediately call open_pega_session().
   - Do NOT ask for details or descriptions yourself. Let Pega initialize.
   - Take the exact text returned from `result.text` and repeat it directly to the user.

3. CONVERSATION PIPE (THE LOOP):
   - For EVERY single user response after the session is open, immediately call answer_pega(context_id, user_answer).
   - `context_id`: Use the exact token returned from the previous tool response.
   - `user_answer`: Pass the user's exact input string cleanly.
   - Output `result.text` word-for-word back to the user. Do NOT add summaries, do NOT add confirmations ("Is that correct?"), and do NOT try to collect fields yourself. Trust Pega's backend agent prompt to sequence the field requests.
""",
    tools=[FunctionTool(open_pega_session), FunctionTool(answer_pega)],
)


# ============================================================================
# CLI ENTRY POINT
# ============================================================================

def main():
    print("\n" + "=" * 70)
    print("🤖  COMPLAINT ASSISTANT  (Pega A2A — Proxy Mode)")
    print("=" * 70)
    print(f"   Pega  : {PEGA_BASE_URL}")
    print(f"   Model : {GOOGLE_MODEL}")
    print("=" * 70)
    print("\nSay hello or let the agent know you want to raise a complaint to begin.")
    print("Type 'exit' to quit.\n")

    session_service = InMemorySessionService()
    session_service.create_session(
        app_name="complaint_app",
        user_id="local_user",
        session_id="session_001",
    )
    runner = Runner(
        agent=root_agent,
        app_name="complaint_app",
        session_service=session_service,
    )

    while True:
        try:
            user_input = input("You: ").strip()
            if not user_input:
                continue
            if user_input.lower() in {"exit", "quit", "bye"}:
                print("\n👋 Goodbye!")
                break

            events = runner.run(
                user_id="local_user",
                session_id="session_001",
                new_message=types.Content(
                    role="user",
                    parts=[types.Part(text=user_input)],
                ),
            )
            for event in events:
                if event.is_final_response() and event.content:
                    for part in event.content.parts:
                        if part.text:
                            print(f"\n🤖 Agent: {part.text}\n")

        except KeyboardInterrupt:
            print("\n\n👋 Interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")


if __name__ == "__main__":
    main()