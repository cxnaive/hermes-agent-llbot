"""Session-key-scoped Mem0 memory provider.

Same engine as the bundled mem0 provider (server-side fact extraction +
semantic search + reranking), but scopes memory by ``gateway_session_key``
(per-chat) instead of ``user_id`` (per-person).

Isolation behavior depends on ``group_sessions_per_user``:

- ``group_sessions_per_user: true`` (default):
    session_key = ``group:<gid>:<uid>`` → **per-user-per-group**. Each person
    in each group has independent memory, AND it doesn't bleed across groups
    (Alice in group A ≠ Alice in group B ≠ Bob in group A).

- ``group_sessions_per_user: false``:
    session_key = ``group:<gid>`` → **per-group collective**. The whole group
    shares one memory domain (a group knowledge base); cross-group isolated.

The mem0 ``user_id`` is set to ``gateway_session_key`` in ``initialize()``,
so all mem0 operations (sync_turn / prefetch / tools) inherit that scoping
automatically. Falls back to ``user_id`` (per-person) for CLI/non-gateway
sessions where no gateway_session_key is present.

Config: same as mem0 — ``MEM0_API_KEY`` (required), ``MEM0_AGENT_ID``
(optional, default "hermes"), ``$HERMES_HOME/mem0.json`` overrides.
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from typing import Any, Dict, List

from agent.memory_provider import MemoryProvider
from tools.registry import tool_error

logger = logging.getLogger(__name__)

# Circuit breaker: after N consecutive failures, pause API calls.
_BREAKER_THRESHOLD = 5
_BREAKER_COOLDOWN_SECS = 120


def _load_config() -> dict:
    """Load config from env + $HERMES_HOME/mem0.json (same as mem0 provider)."""
    from hermes_constants import get_hermes_home

    config = {
        "api_key": os.environ.get("MEM0_API_KEY", ""),
        "agent_id": os.environ.get("MEM0_AGENT_ID", "hermes"),
        "rerank": True,
    }
    config_path = get_hermes_home() / "mem0.json"
    if config_path.exists():
        try:
            file_cfg = json.loads(config_path.read_text(encoding="utf-8"))
            config.update({k: v for k, v in file_cfg.items()
                           if v is not None and v != ""})
        except Exception:
            pass
    return config


# ---------------------------------------------------------------------------
# Tool schemas — scoped to this chat via _read_filters/_write_filters.
# ---------------------------------------------------------------------------

PROFILE_SCHEMA = {
    "name": "mem0_profile",
    "description": "Retrieve all stored memories for this chat. Fast, no reranking.",
    "parameters": {"type": "object", "properties": {}, "required": []},
}

SEARCH_SCHEMA = {
    "name": "mem0_search",
    "description": "Search this chat's memories by meaning. Ranked by similarity.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "What to search for."},
            "rerank": {"type": "boolean", "description": "Enable reranking (default false)."},
            "top_k": {"type": "integer", "description": "Max results (default 10, max 50)."},
        },
        "required": ["query"],
    },
}

CONCLUDE_SCHEMA = {
    "name": "mem0_conclude",
    "description": "Store a durable fact scoped to this chat.",
    "parameters": {
        "type": "object",
        "properties": {
            "conclusion": {"type": "string", "description": "The fact to store."},
        },
        "required": ["conclusion"],
    },
}


# ---------------------------------------------------------------------------
# MemoryProvider implementation
# ---------------------------------------------------------------------------

class SessionKeyMem0Provider(MemoryProvider):
    """Mem0 Platform memory scoped by gateway_session_key (per-chat)."""

    def __init__(self):
        self._config = None
        self._client = None
        self._client_lock = threading.Lock()
        self._api_key = ""
        self._scope_id = "default"  # gateway_session_key (the mem0 user_id)
        self._agent_id = "hermes"
        self._rerank = True
        self._prefetch_result = ""
        self._prefetch_lock = threading.Lock()
        self._prefetch_thread = None
        self._sync_thread = None
        self._consecutive_failures = 0
        self._breaker_open_until = 0.0

    @property
    def name(self) -> str:
        return "session-key-mem0"

    def is_available(self) -> bool:
        return bool(os.environ.get("MEM0_API_KEY"))

    def _get_client(self):
        """Thread-safe mem0 client accessor with lazy init."""
        with self._client_lock:
            if self._client is not None:
                return self._client
            try:
                from mem0 import MemoryClient
                self._client = MemoryClient(api_key=self._api_key)
                return self._client
            except ImportError:
                raise RuntimeError("mem0 package not installed. Run: pip install mem0ai")

    # ── Circuit breaker ──────────────────────────────────────────────────

    def _is_breaker_open(self) -> bool:
        if self._consecutive_failures < _BREAKER_THRESHOLD:
            return False
        if time.monotonic() >= self._breaker_open_until:
            self._consecutive_failures = 0
            return False
        return True

    def _record_success(self):
        self._consecutive_failures = 0

    def _record_failure(self):
        self._consecutive_failures += 1
        if self._consecutive_failures >= _BREAKER_THRESHOLD:
            self._breaker_open_until = time.monotonic() + _BREAKER_COOLDOWN_SECS
            logger.warning(
                "Session-key-mem0 circuit breaker tripped after %d failures. "
                "Pausing %ds.", self._consecutive_failures, _BREAKER_COOLDOWN_SECS,
            )

    # ── Lifecycle ────────────────────────────────────────────────────────

    def initialize(self, session_id: str, **kwargs) -> None:
        self._config = _load_config()
        self._api_key = self._config.get("api_key", "")
        self._agent_id = self._config.get("agent_id", "hermes")
        self._rerank = self._config.get("rerank", True)
        # ★ session-key isolation: use gateway_session_key as mem0's user_id.
        # This makes every mem0 call (sync/prefetch/tools) scoped to the chat.
        # Falls back to user_id for CLI/non-gateway (no session_key).
        self._scope_id = (
            kwargs.get("gateway_session_key")
            or kwargs.get("user_id")
            or "default"
        )

    def _read_filters(self) -> Dict[str, Any]:
        """Search/get_all filters — scoped to this chat."""
        return {"user_id": self._scope_id}

    def _write_filters(self) -> Dict[str, Any]:
        """Add filters — scoped to this chat + agent attribution."""
        return {"user_id": self._scope_id, "agent_id": self._agent_id}

    @staticmethod
    def _unwrap_results(response: Any) -> list:
        """Normalize mem0 API response (v2 wraps in {"results": [...]})."""
        if isinstance(response, dict):
            return response.get("results", [])
        if isinstance(response, list):
            return response
        return []

    # ── System prompt + prefetch ─────────────────────────────────────────

    def system_prompt_block(self) -> str:
        return (
            "# Mem0 Memory (session-key scoped)\n"
            f"Active. Chat scope: {self._scope_id}.\n"
            "Use mem0_search to find memories, mem0_conclude to store facts, "
            "mem0_profile for a full overview."
        )

    def prefetch(self, query: str, *, session_id: str = "") -> str:
        if self._prefetch_thread and self._prefetch_thread.is_alive():
            self._prefetch_thread.join(timeout=3.0)
        with self._prefetch_lock:
            result = self._prefetch_result
            self._prefetch_result = ""
        if not result:
            return ""
        return f"## Mem0 Memory\n{result}"

    def queue_prefetch(self, query: str, *, session_id: str = "") -> None:
        if self._is_breaker_open():
            return

        def _run():
            try:
                client = self._get_client()
                results = self._unwrap_results(client.search(
                    query=query,
                    filters=self._read_filters(),
                    rerank=self._rerank,
                    top_k=5,
                ))
                if results:
                    lines = [r.get("memory", "") for r in results if r.get("memory")]
                    with self._prefetch_lock:
                        self._prefetch_result = "\n".join(f"- {l}" for l in lines)
                self._record_success()
            except Exception as e:
                self._record_failure()
                logger.debug("Session-key-mem0 prefetch failed: %s", e)

        self._prefetch_thread = threading.Thread(target=_run, daemon=True, name="skmem0-prefetch")
        self._prefetch_thread.start()

    # ── Sync (write) ─────────────────────────────────────────────────────

    def sync_turn(self, user_content: str, assistant_content: str, *, session_id: str = "") -> None:
        """Send the turn to mem0 for server-side fact extraction (non-blocking)."""
        if self._is_breaker_open():
            return

        def _sync():
            try:
                client = self._get_client()
                messages = [
                    {"role": "user", "content": user_content},
                    {"role": "assistant", "content": assistant_content},
                ]
                client.add(messages, **self._write_filters())
                self._record_success()
            except Exception as e:
                self._record_failure()
                logger.warning("Session-key-mem0 sync failed: %s", e)

        if self._sync_thread and self._sync_thread.is_alive():
            self._sync_thread.join(timeout=5.0)
        self._sync_thread = threading.Thread(target=_sync, daemon=True, name="skmem0-sync")
        self._sync_thread.start()

    # ── Tools (agent-initiated) ──────────────────────────────────────────

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        return [PROFILE_SCHEMA, SEARCH_SCHEMA, CONCLUDE_SCHEMA]

    def handle_tool_call(self, tool_name: str, args: dict, **kwargs) -> str:
        if self._is_breaker_open():
            return json.dumps({
                "error": "Mem0 API temporarily unavailable (circuit breaker). Will retry."
            })
        try:
            client = self._get_client()
        except Exception as e:
            return tool_error(str(e))

        if tool_name == "mem0_profile":
            try:
                memories = self._unwrap_results(client.get_all(filters=self._read_filters()))
                self._record_success()
                if not memories:
                    return json.dumps({"result": "No memories stored yet for this chat."})
                lines = [m.get("memory", "") for m in memories if m.get("memory")]
                return json.dumps({"result": "\n".join(lines), "count": len(lines)})
            except Exception as e:
                self._record_failure()
                return tool_error(f"Failed to fetch profile: {e}")

        elif tool_name == "mem0_search":
            query = args.get("query", "")
            if not query:
                return tool_error("Missing required parameter: query")
            rerank = args.get("rerank", False)
            top_k = min(int(args.get("top_k", 10)), 50)
            try:
                results = self._unwrap_results(client.search(
                    query=query,
                    filters=self._read_filters(),
                    rerank=rerank,
                    top_k=top_k,
                ))
                self._record_success()
                if not results:
                    return json.dumps({"result": "No relevant memories found for this chat."})
                items = [{"memory": r.get("memory", ""), "score": r.get("score", 0)} for r in results]
                return json.dumps({"results": items, "count": len(items)})
            except Exception as e:
                self._record_failure()
                return tool_error(f"Search failed: {e}")

        elif tool_name == "mem0_conclude":
            conclusion = args.get("conclusion", "")
            if not conclusion:
                return tool_error("Missing required parameter: conclusion")
            try:
                client.add(
                    [{"role": "user", "content": conclusion}],
                    **self._write_filters(),
                    infer=False,
                )
                self._record_success()
                return json.dumps({"result": "Fact stored for this chat."})
            except Exception as e:
                self._record_failure()
                return tool_error(f"Failed to store: {e}")

        return tool_error(f"Unknown tool: {tool_name}")

    def shutdown(self) -> None:
        for t in (self._prefetch_thread, self._sync_thread):
            if t and t.is_alive():
                t.join(timeout=5.0)
        with self._client_lock:
            self._client = None


def register(ctx) -> None:
    """Register session-key-mem0 as a memory provider plugin."""
    ctx.register_memory_provider(SessionKeyMem0Provider())
