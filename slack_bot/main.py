from typing import Any, Dict, Optional
import aiohttp
import asyncio
from datetime import datetime, timedelta
import os
import time

from fastapi import FastAPI
from fastapi import Request
from slack_bolt.adapter.fastapi.async_handler import AsyncSlackRequestHandler
from slack_bolt.adapter.socket_mode.aiohttp import AsyncSocketModeHandler
from slack_bolt.async_app import AsyncApp
from slack_sdk.web.async_client import AsyncWebClient

from modules.health import healthcheck
from utils import get_logger

# Configure logging using shared utility
logger = get_logger(__name__)

# Configuration from environment variables
API_BASE_URL = (
    os.getenv("SRE_BOT_API_URL") or os.getenv("SRE_AGENT_API_URL") or "http://sre-bot-api:8000"
)
API_TIMEOUT = int(os.getenv("API_TIMEOUT", "300"))  # Default 300 seconds
SESSION_TIMEOUT_MINUTES = int(
    os.getenv("SESSION_TIMEOUT_MINUTES", "1200")
)  # Default 1200 minutes (20 hours)

# Optional upgrades (all backwards-compatible defaults)
ACK_MESSAGE_TEMPLATE = os.getenv(
    "ACK_MESSAGE_TEMPLATE",
    "I'm processing your request, <@{user}>! One moment please...",
)
DEDUP_TTL_SECONDS = int(os.getenv("DEDUP_TTL_SECONDS", "300"))  # 5 minutes
SLACK_MAX_CHARS = int(os.getenv("SLACK_MAX_CHARS", "3500"))  # safe chunk size
LOG_SLACK_EVENT_BODIES = os.getenv("LOG_SLACK_EVENT_BODIES", "false").lower() == "true"
SLACK_SOCKET_MODE = os.getenv("SLACK_SOCKET_MODE", "false").lower() == "true"

# Whitelist configuration
WHITELIST_ENABLED = os.getenv("WHITELIST_ENABLED", "false").lower() == "true"
WHITELIST_USERS = set(
    user.strip() for user in os.getenv("WHITELIST_USERS", "").split(",") if user.strip()
)

logger.info(f"API timeout configured: {API_TIMEOUT} seconds")
logger.info(f"Session timeout configured: {SESSION_TIMEOUT_MINUTES} minutes")
logger.info(f"Whitelist enabled: {WHITELIST_ENABLED}")
if WHITELIST_ENABLED:
    logger.info(f"Whitelisted users: {len(WHITELIST_USERS)} users")
    logger.info(f"Whitelisted user IDs: {list(WHITELIST_USERS)}")
else:
    logger.info("Whitelist disabled - all users allowed")


# -----------------------------
# Dedupe (prevents duplicate replies on Slack retries)
# -----------------------------
_seen_event_ids: Dict[str, float] = {}
_seen_message_keys: Dict[str, float] = {}


def _cleanup_seen_events(now: float) -> None:
    expired = [eid for eid, ts in _seen_event_ids.items() if (now - ts) > DEDUP_TTL_SECONDS]
    for eid in expired:
        _seen_event_ids.pop(eid, None)

    expired_message_keys = [
        key for key, ts in _seen_message_keys.items() if (now - ts) > DEDUP_TTL_SECONDS
    ]
    for key in expired_message_keys:
        _seen_message_keys.pop(key, None)


def is_duplicate_event(body: Dict[str, Any]) -> bool:
    """
    Slack may deliver the same event multiple times (retries).
    Dedupe on body["event_id"] with a short TTL.
    """
    event_id = body.get("event_id")
    if not event_id:
        return False

    now = time.time()
    _cleanup_seen_events(now)

    if event_id in _seen_event_ids:
        logger.warning(f"Duplicate Slack event detected, skipping: event_id={event_id}")
        return True

    _seen_event_ids[event_id] = now
    return False


def is_duplicate_message_event(event: Dict[str, Any]) -> bool:
    """
    Dedupe by Slack channel + message timestamp. This catches workspaces that
    deliver both app_mention and message events for the same user message.
    """
    channel = event.get("channel")
    ts = event.get("ts")
    if not channel or not ts:
        return False

    now = time.time()
    _cleanup_seen_events(now)

    key = f"{channel}:{ts}"
    if key in _seen_message_keys:
        logger.warning(f"Duplicate Slack message detected, skipping: {key}")
        return True

    _seen_message_keys[key] = now
    return False


def is_user_whitelisted(user_id: str) -> bool:
    """
    Check if a user is whitelisted to use the bot.

    Args:
        user_id: Slack user ID

    Returns:
        True if whitelisting is disabled OR user is in whitelist
        False if whitelisting is enabled AND user is not in whitelist
    """
    logger.debug(f"Checking whitelist for user: {user_id}")
    logger.debug(f"Whitelist enabled: {WHITELIST_ENABLED}")
    logger.debug(f"Whitelist users: {WHITELIST_USERS}")

    if not WHITELIST_ENABLED:
        logger.debug(f"Whitelist disabled, allowing user {user_id}")
        return True

    is_whitelisted = user_id in WHITELIST_USERS
    logger.debug(f"User {user_id} in whitelist: {is_whitelisted}")
    return is_whitelisted


# Initialize the Slack app
app = AsyncApp(
    token=os.getenv("SLACK_BOT_TOKEN"),
    signing_secret=os.getenv("SLACK_SIGNING_SECRET"),
)
fast_api = FastAPI()
app_handler = AsyncSlackRequestHandler(app)
socket_mode_handler: AsyncSocketModeHandler | None = None

# Global variable to store bot user ID
bot_user_id = None


async def initialize_bot_user_id():
    """Initialize the bot's user ID at startup"""
    global bot_user_id
    try:
        client = AsyncWebClient(token=os.getenv("SLACK_BOT_TOKEN"))
        auth_response = await client.auth_test()
        if auth_response.get("ok"):
            bot_user_id = auth_response.get("user_id")
            logger.info(f"Bot initialized with user ID: {bot_user_id}")
        else:
            logger.error(f"Failed to get bot user ID at startup: {auth_response}")
    except Exception as e:
        logger.error(f"Error initializing bot user ID: {e}", exc_info=True)


def strip_bot_mention(text: str) -> str:
    """
    Remove the bot mention token (<@BOTID>) from the text before sending to API.
    If stripping results in empty text, return original.
    """
    t = (text or "").strip()
    if not t or not bot_user_id:
        return t
    cleaned = t.replace(f"<@{bot_user_id}>", "").strip()
    return cleaned if cleaned else t


def chunk_text(text: str, max_chars: int) -> list[str]:
    """
    Split long output into Slack-safe chunks.
    Only used when responses are huge; normal responses remain single-message.
    """
    text = (text or "").strip()
    if len(text) <= max_chars:
        return [text]

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + max_chars)

        split_at = text.rfind("\n", start, end)
        if split_at == -1:
            split_at = text.rfind(" ", start, end)
        if split_at == -1 or split_at <= start:
            split_at = end

        chunks.append(text[start:split_at].strip())
        start = split_at

    return [c for c in chunks if c]


# Session management
class ConversationSession:
    def __init__(self, channel: str, user: str, thread_ts: str | None = None):
        self.channel = channel
        self.user = user  # Original user who started the session
        self.current_user = user  # Current user interacting (can change in threads)
        self.thread_ts = thread_ts
        # Use thread_ts in the session_id if available for continuity
        thread_id = thread_ts if thread_ts else f"{datetime.now().timestamp()}"
        self.session_id = f"s_{channel}_{thread_id}"
        self.last_activity = datetime.now()
        self.user_id = f"u_{user}"  # Unique user ID for the API

    def update_activity(self):
        self.last_activity = datetime.now()

    def is_expired(self, timeout_minutes: Optional[int] = None) -> bool:
        if timeout_minutes is None:
            timeout_minutes = SESSION_TIMEOUT_MINUTES
        return datetime.now() - self.last_activity > timedelta(minutes=timeout_minutes)


# Global session manager
class SessionManager:
    def __init__(self):
        self.sessions: Dict[str, ConversationSession] = {}
        self.cleanup_interval = SESSION_TIMEOUT_MINUTES * 60
        self.thread_session_map: Dict[str, str] = {}

    def update_session_thread(self, session: ConversationSession, new_thread_ts: str):
        """Update an existing session with a new thread_ts (for thread creation)"""
        old_key = (
            f"{session.channel}_{session.user}_{session.thread_ts if session.thread_ts else 'main'}"
        )

        session.thread_ts = new_thread_ts
        session.session_id = f"s_{session.channel}_{new_thread_ts}"
        session.update_activity()

        new_key = f"{session.channel}_{session.user}_{new_thread_ts}"

        if old_key in self.sessions:
            self.sessions[new_key] = self.sessions[old_key]
            del self.sessions[old_key]
            logger.info(f"Migrated session from {old_key} to {new_key}")

        thread_key = f"{session.channel}_{new_thread_ts}"
        self.thread_session_map[thread_key] = new_key

        return session

    def get_session(
        self, channel: str, user: str, thread_ts: str | None = None
    ) -> ConversationSession:
        self._cleanup_expired_sessions()

        if thread_ts:
            thread_key = f"{channel}_{thread_ts}"
            if thread_key in self.thread_session_map:
                existing_session_key = self.thread_session_map[thread_key]
                if (
                    existing_session_key in self.sessions
                    and not self.sessions[existing_session_key].is_expired()
                ):
                    logger.info(
                        f"Reusing existing thread session {existing_session_key} for thread {thread_ts} (current user: {user})"
                    )
                    session = self.sessions[existing_session_key]
                    session.update_activity()
                    session.current_user = user
                    return session

        key = f"{channel}_{user}_{thread_ts if thread_ts else 'main'}"

        if key not in self.sessions or self.sessions[key].is_expired():
            self.sessions[key] = ConversationSession(channel, user, thread_ts)
            if thread_ts:
                self.thread_session_map[f"{channel}_{thread_ts}"] = key
                logger.info(f"Created new session for thread {thread_ts}: {key}")
        else:
            self.sessions[key].update_activity()
            logger.info(f"Using existing session: {key}")

        return self.sessions[key]

    def _cleanup_expired_sessions(self):
        expired_keys = [k for k, v in self.sessions.items() if v.is_expired()]

        for k in expired_keys:
            expired_session = self.sessions[k]
            if expired_session.thread_ts:
                thread_key = f"{expired_session.channel}_{expired_session.thread_ts}"
                if thread_key in self.thread_session_map:
                    del self.thread_session_map[thread_key]
            del self.sessions[k]
            logger.info(f"Cleaned up expired session: {k}")


session_manager = SessionManager()


async def send_acknowledgment_message(
    client: AsyncWebClient, channel: str, user: str, thread_ts: str = None
) -> bool:
    try:
        location = f"thread {thread_ts}" if thread_ts else "channel"
        logger.info(f"Sending acknowledgment message to {location} for user {user}")

        response = await client.chat_postMessage(
            channel=channel,
            thread_ts=thread_ts,
            text=ACK_MESSAGE_TEMPLATE.format(user=user),
        )

        if response.get("ok"):
            logger.info(f"✅ Successfully sent acknowledgment message to {location}")
            return True
        logger.error(f"Failed to send acknowledgment message: {response}")
        return False

    except Exception as ack_error:
        logger.error(f"Exception sending acknowledgment message: {ack_error}", exc_info=True)
        return False


async def post_response_to_slack(
    client: AsyncWebClient, channel: str, thread_ts: str | None, text: str
) -> None:
    parts = chunk_text(text, SLACK_MAX_CHARS)
    for part in parts:
        await client.chat_postMessage(channel=channel, text=part, thread_ts=thread_ts)


async def fetch_parent_message_content(
    client: AsyncWebClient, channel: str, thread_ts: str
) -> Dict[str, Any]:
    try:
        logger.info(f"Fetching parent message content for thread {thread_ts} in channel {channel}")

        response = await client.conversations_replies(
            channel=channel,
            ts=thread_ts,
            limit=10,
        )

        if not response.get("ok"):
            error = response.get("error", "Unknown error")
            logger.warning(f"Failed to fetch thread messages: {error}")
            return {"error": f"Slack API error: {error}"}

        messages = response.get("messages", [])
        if not messages:
            logger.warning("No messages found in thread response")
            return {"error": "No messages found in thread"}

        parent_message = messages[0]

        if not parent_message.get("ts") == thread_ts:
            logger.warning(
                f"Parent message timestamp {parent_message.get('ts')} doesn't match thread_ts {thread_ts}"
            )
            return {"error": "Parent message timestamp mismatch"}

        parent_content = {
            "text": parent_message.get("text", ""),
            "user": parent_message.get("user"),
            "timestamp": parent_message.get("ts"),
            "user_profile": {},
        }

        try:
            user_info = await client.users_info(user=parent_message.get("user"))
            if user_info.get("ok"):
                user_profile = user_info.get("user", {}).get("profile", {})
                parent_content["user_profile"] = {
                    "display_name": user_profile.get("display_name", ""),
                    "real_name": user_profile.get("real_name", ""),
                }
        except Exception as e:
            logger.warning(f"Could not fetch user info: {e}")

        thread_context = []
        for msg in messages[1:]:
            if not msg.get("bot_id"):
                thread_context.append(
                    {
                        "text": msg.get("text", ""),
                        "user": msg.get("user"),
                        "timestamp": msg.get("ts"),
                    }
                )

        return {
            "parent_message": parent_content,
            "thread_context": thread_context,
            "thread_length": len(messages),
            "channel": channel,
        }

    except Exception as e:
        logger.error(f"Error fetching parent message content: {e}", exc_info=True)
        return {"error": f"Failed to fetch thread content: {str(e)}"}


async def create_api_session(
    session: ConversationSession, parent_thread_data: Dict[str, Any] = None
) -> bool:
    """Create a new session with the sre-bot-api, or handle case where session already exists"""
    async with aiohttp.ClientSession() as client:
        try:
            url = f"{API_BASE_URL}/apps/sre_agent/users/{session.user_id}/sessions/{session.session_id}"
            payload = {
                "state": {
                    "channel": session.channel,
                    "thread_ts": session.thread_ts,
                    "slack_user": session.current_user,
                    "original_user": session.user,
                    "thread_context": parent_thread_data if parent_thread_data else {},
                    "has_thread_context": bool(parent_thread_data),
                    "session_created_at": datetime.now().isoformat(),
                }
            }
            logger.info(f"Creating API session at URL: {url}")

            for attempt in range(1, 4):
                try:
                    async with client.post(url, json=payload, timeout=10) as response:
                        response_text = await response.text()
                        logger.info(
                            f"API Response Status: {response.status}, Body: {response_text[:200]}"
                        )

                        if response.status == 200:
                            logger.info(f"Successfully created session {session.session_id}")
                            return True
                        if response.status == 400 and "already exists" in response_text:
                            logger.info(
                                f"Session {session.session_id} already exists, proceeding anyway"
                            )
                            return True

                        logger.error(
                            f"Failed to create session. Status: {response.status}, Response: {response_text}"
                        )
                        return False
                except asyncio.TimeoutError:
                    logger.error(
                        f"Connection timeout when trying to connect to sre-bot-api (attempt {attempt}/3)"
                    )
                except aiohttp.ClientConnectorError as conn_err:
                    logger.error(
                        f"Connection error to sre-bot-api (attempt {attempt}/3): {conn_err}"
                    )

                if attempt < 3:
                    await asyncio.sleep(2)

            return False

        except Exception as e:
            logger.error(f"Error creating API session: {e}", exc_info=True)
            return False


async def send_message_to_api(session: ConversationSession, message: str) -> str:
    """Send a message to the sre-bot-api and get the response"""
    async with aiohttp.ClientSession() as client:
        try:
            url = f"{API_BASE_URL}/run"

            payload = {
                "app_name": "sre_agent",
                "user_id": session.user_id,
                "session_id": session.session_id,
                "new_message": {"role": "user", "parts": [{"text": message}]},
            }

            logger.info(f"Sending message to API at URL: {url}")

            start_time = time.time()
            async with client.post(url, json=payload, timeout=API_TIMEOUT) as response:
                response_time_ms = (time.time() - start_time) * 1000
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(
                        f"API returned status {response.status}: {error_text[:200]}, Response time: {response_time_ms:.2f}ms"
                    )
                    return f"Error: API returned status {response.status}"

                logger.info(
                    f"API call successful - Status: {response.status}, Response time: {response_time_ms:.2f}ms"
                )

                try:
                    data = await response.json()
                except Exception as json_err:
                    logger.error(f"Failed to parse JSON response: {json_err}")
                    data_text = await response.text()
                    return f"Got non-JSON response: {data_text[:200]}..."

                api_response = ""

                # ADK event structure in list response. Scan from the end
                # because tool/action events can follow the final text event.
                if isinstance(data, list):
                    for event in reversed([item for item in data if isinstance(item, dict)]):
                        content = event.get("content")
                        if isinstance(content, dict) and "parts" in content:
                            parts = content.get("parts", [])
                            if (
                                isinstance(parts, list)
                                and parts
                                and isinstance(parts[0], dict)
                                and "text" in parts[0]
                            ):
                                return parts[0]["text"]

                # state_delta["kubernetes_agent_output"] (appears in logs)
                if isinstance(data, list) and data and isinstance(data[-1], dict):
                    event = data[-1]
                    actions = event.get("actions")
                    if isinstance(actions, dict):
                        state_delta = actions.get("state_delta")
                        if (
                            isinstance(state_delta, dict)
                            and "kubernetes_agent_output" in state_delta
                        ):
                            out = state_delta.get("kubernetes_agent_output")
                            if isinstance(out, str):
                                return out

                if isinstance(data, dict):
                    for key in [
                        "response",
                        "text",
                        "content",
                        "message",
                        "answer",
                        "result",
                        "output",
                    ]:
                        if key in data and data[key]:
                            val = data[key]
                            if isinstance(val, str):
                                api_response = val
                                break
                            if isinstance(val, dict) and "text" in val:
                                api_response = val["text"]
                                break
                            if isinstance(val, dict) and "content" in val:
                                api_response = val["content"]
                                break

                    if (
                        not api_response
                        and "candidates" in data
                        and isinstance(data["candidates"], list)
                        and data["candidates"]
                    ):
                        candidate = data["candidates"][0]
                        if isinstance(candidate, dict):
                            content = candidate.get("content")
                            if isinstance(content, dict) and "parts" in content:
                                parts = content.get("parts", [])
                                if (
                                    isinstance(parts, list)
                                    and parts
                                    and isinstance(parts[0], dict)
                                    and "text" in parts[0]
                                ):
                                    api_response = parts[0]["text"]

                    if api_response:
                        return (
                            api_response.strip()
                            if isinstance(api_response, str)
                            else str(api_response)
                        )

                elif isinstance(data, list):
                    if data and isinstance(data[0], dict):
                        for key in ["text", "content", "message", "response"]:
                            if key in data[0]:
                                api_response = data[0][key]
                                break
                    elif data and isinstance(data[0], str):
                        api_response = data[0]

                elif isinstance(data, str):
                    api_response = data

                if not api_response:
                    logger.warning(
                        "Could not extract structured response, using string representation"
                    )
                    api_response = str(data)

                return api_response.strip() if isinstance(api_response, str) else str(api_response)

        except Exception as e:
            logger.error(f"Error sending message to API: {e}", exc_info=True)
            return f"Error communicating with API: {str(e)}"


async def process_message_with_api(
    client: AsyncWebClient,
    channel: str,
    thread_ts: str | None,
    user: str,
    message: str,
    original_message_ts: str | None = None,
):
    """Process the message using the API and send response"""
    try:
        if thread_ts:
            await send_acknowledgment_message(client, channel, user, thread_ts)

        if not thread_ts and original_message_ts:
            thread_ts = original_message_ts
            ack_sent = await send_acknowledgment_message(client, channel, user, thread_ts)

            if ack_sent:
                session = session_manager.get_session(channel, user, None)
                session = session_manager.update_session_thread(session, thread_ts)
            else:
                session = session_manager.get_session(channel, user, None)
        elif not thread_ts and not original_message_ts:
            session = session_manager.get_session(channel, user, None)
            await send_acknowledgment_message(client, channel, user)
        else:
            session = session_manager.get_session(channel, user, thread_ts)

        parent_thread_data = None
        thread_just_created = (
            session.thread_ts == original_message_ts and original_message_ts is not None
        )

        if session.thread_ts and not thread_just_created:
            parent_thread_data = await fetch_parent_message_content(
                client, channel, session.thread_ts
            )
            if parent_thread_data.get("error"):
                parent_thread_data = None

        session_created = await create_api_session(session, parent_thread_data)
        if not session_created:
            error_message = (
                "I couldn't establish a connection with the sre-bot-api service. This could be because:\n"
                "1. The API service is not running\n"
                "2. There's a network issue between services\n"
                "3. The API endpoint is incorrect\n\n"
                "Please check the logs for more details."
            )
            await client.chat_postMessage(
                channel=channel,
                text=f"Sorry <@{user}>, {error_message}",
                thread_ts=thread_ts,
            )
            return

        # Clean user message before sending to API (safer inputs)
        clean_message = strip_bot_mention(message)

        enhanced_message = clean_message
        if parent_thread_data and not parent_thread_data.get("error"):
            parent_msg = parent_thread_data.get("parent_message", {})
            parent_text = (parent_msg.get("text", "") or "").strip()

            if parent_text:
                author_name = "Unknown"
                user_profile = parent_msg.get("user_profile", {})
                if user_profile.get("display_name"):
                    author_name = user_profile["display_name"]
                elif user_profile.get("real_name"):
                    author_name = user_profile["real_name"]
                elif parent_msg.get("user"):
                    author_name = f"User {parent_msg['user']}"

                thread_length = parent_thread_data.get("thread_length", 1)

                enhanced_message = f"""User message: {clean_message}

Thread Context:
- Original message: "{parent_text}"
- Original author: {author_name}
- Thread length: {thread_length} messages
- Context: This message is part of an ongoing thread discussion

Please consider this thread context when responding to provide relevant and coherent assistance."""

        response = await send_message_to_api(session, enhanced_message)

        await post_response_to_slack(
            client=client,
            channel=channel,
            thread_ts=session.thread_ts,
            text=response,
        )

    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        await client.chat_postMessage(
            channel=channel,
            text=f"Sorry <@{user}>, something went wrong while processing your request.",
            thread_ts=session.thread_ts if "session" in locals() else thread_ts,
        )


@app.event("app_mention")
async def handle_app_mention_events(body, say, client, logger):
    """Handle app mentions (when someone @mentions the bot)"""
    if is_duplicate_event(body):
        return

    event = body.get("event", {})
    if LOG_SLACK_EVENT_BODIES:
        logger.info(body)
    else:
        logger.info(
            f"App mention received: event_id={body.get('event_id')} user={event.get('user')} channel={event.get('channel')}"
        )

    if event.get("type") == "app_mention" and "text" in event:
        user = event.get("user")
        text = event.get("text")
        channel = event.get("channel")
        thread_ts = event.get("thread_ts", event.get("ts"))

        if user:
            if not is_user_whitelisted(user):
                try:
                    await say(
                        text=f"Hi <@{user}>! 👋 Thanks for your interest in the SRE bot. "
                        "This bot is currently in limited preview and will be available "
                        "to all users when it reaches general availability (GA). "
                        "Stay tuned for updates! 🚀",
                        thread_ts=thread_ts,
                    )
                except Exception as e:
                    logger.error(f"Error sending whitelist message: {e}", exc_info=True)
                return

            try:
                if is_duplicate_message_event(event):
                    return

                original_message_ts = event.get("ts") if not event.get("thread_ts") else None

                asyncio.create_task(
                    process_message_with_api(
                        client=client,
                        channel=channel,
                        thread_ts=thread_ts,
                        user=user,
                        message=text,
                        original_message_ts=original_message_ts,
                    )
                )
            except Exception as e:
                logger.error(f"Error handling app mention: {str(e)}", exc_info=True)
                await say(
                    text=f"Sorry <@{user}>, something went wrong while processing your request.",
                    thread_ts=thread_ts,
                )


@app.event("message")
async def handle_message_events(body, say, client, logger):
    """Handle all message events"""
    if is_duplicate_event(body):
        return

    event = body.get("event", {})
    if LOG_SLACK_EVENT_BODIES:
        logger.info(body)
    else:
        logger.info(
            f"Message event: event_id={body.get('event_id')} user={event.get('user')} channel={event.get('channel')} thread_ts={event.get('thread_ts')}"
        )

    if event.get("type") == "message" and "text" in event:
        user = event.get("user")
        text = event.get("text")
        channel = event.get("channel")
        thread_ts = event.get("thread_ts")

        if not event.get("bot_id") and user:
            global bot_user_id
            if bot_user_id is None:
                await initialize_bot_user_id()

            if not is_user_whitelisted(user):
                is_bot_mentioned = bot_user_id and text and f"<@{bot_user_id}>" in text
                if is_bot_mentioned:
                    try:
                        await say(
                            {
                                "text": f"Hi <@{user}>! 👋 Thanks for your interest in the SRE bot. "
                                "This bot is currently in limited preview and will be available "
                                "to all users when it reaches general availability (GA). "
                                "Stay tuned for updates! 🚀",
                                "thread_ts": thread_ts,
                            }
                        )
                    except Exception as e:
                        logger.error(f"Error sending whitelist message: {e}", exc_info=True)
                return

            is_direct_mention = bot_user_id and text and f"<@{bot_user_id}>" in text
            if not is_direct_mention:
                return

            try:
                if is_duplicate_message_event(event):
                    return

                original_message_ts = event.get("ts") if not thread_ts else None

                asyncio.create_task(
                    process_message_with_api(
                        client=client,
                        channel=channel,
                        thread_ts=thread_ts,
                        user=user,
                        message=text,
                        original_message_ts=original_message_ts,
                    )
                )

            except Exception as e:
                logger.error(f"Error in message handler: {e}", exc_info=True)
                await say(
                    {
                        "text": f"Sorry <@{user}>, something went wrong!",
                        "thread_ts": thread_ts,
                    }
                )


@fast_api.get("/health", status_code=200)
async def health() -> dict[str, Any]:
    """Health check endpoint"""
    return healthcheck()


@fast_api.on_event("startup")
async def startup_event():
    """Initialize bot when FastAPI starts"""
    global socket_mode_handler
    await initialize_bot_user_id()

    if SLACK_SOCKET_MODE:
        app_token = os.getenv("SLACK_APP_TOKEN")
        if not app_token:
            logger.error("SLACK_SOCKET_MODE=true but SLACK_APP_TOKEN is not set")
            return

        logger.info("Starting Slack Socket Mode handler")
        socket_mode_handler = AsyncSocketModeHandler(app, app_token)
        asyncio.create_task(socket_mode_handler.start_async())


@fast_api.on_event("shutdown")
async def shutdown_event():
    """Stop Socket Mode cleanly when the service shuts down."""
    if socket_mode_handler:
        await socket_mode_handler.close_async()


@fast_api.post("/slack/events")
async def slack_events(req: Request) -> Any:
    """Handle incoming Slack events"""
    return await app_handler.handle(req)


@app.error
async def custom_error_handler(error, body, logger):
    logger.exception(f"Error: {error}")
    logger.info(f"Request body: {body}")
