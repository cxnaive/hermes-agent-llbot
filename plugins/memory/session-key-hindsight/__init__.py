"""Session-key-scoped Hindsight memory provider.

Subclasses the bundled ``hindsight`` provider and inherits ALL of its
behavior — knowledge-graph retain/recall/reflect, multi-strategy retrieval,
entity resolution, retain-every-N-turns buffering, explicit tools, and the
``on_session_end`` hook. The ONLY override is ``initialize()``, which derives
``bank_id`` from ``gateway_session_key``.

Why subclass + bank_id: Hindsight isolates by ``bank_id`` (its partition).
The bundled provider's ``_resolve_bank_id_template`` only supports
``{profile}`` / ``{workspace}`` / ``{platform}`` / ``{user}`` / ``{session}``
— **not** ``{chat_id}`` or ``{session_key}``. So per-chat isolation isn't
possible out of the box (``{user}`` is per-person, ``{session}`` is unstable
across /new). This subclass adds a ``session_key_bank_template`` config and
resolves ``{session_key}`` / ``{chat_id}`` / ``{chat_type}`` / ... to set
``bank_id``, giving per-chat banks:

- ``group_sessions_per_user: true`` (default): session_key includes the user
  id → **per-user-per-group** banks.
- ``group_sessions_per_user: false``: session_key = ``group:<gid>`` →
  **per-group collective** bank (the whole group shares one bank,
  cross-group isolated).

``bank_id`` is a **per-call argument** in every Hindsight API call
(``aretain_batch`` / ``arecall`` / ``areflect`` / tools), not baked into the
client at construction. So overriding ``self._bank_id`` after
``super().initialize()`` reroutes every subsequent call — no client rebuild
needed (unlike the supermemory subclass).

``document_id`` is left untouched: the parent sets it to
``{session_id}-{timestamp}`` (per-process), so within one bank you get one
document per process lifecycle, all filterable under the same chat-scoped
bank. Cross-chat isolation comes from the bank.

Falls back to the parent's ``bank_id`` when no ``gateway_session_key`` is
present (CLI, cron, subagent).

Config: identical to bundled hindsight (``$HERMES_HOME/hindsight/config.json``
+ ``HINDSIGHT_*`` env), PLUS one optional key:

    ``session_key_bank_template`` (str, default ``"{session_key}"``)
        Placeholders (each sanitized to ``[a-zA-Z0-9-]``, runs collapsed):
          {session_key}  full gateway session key (default; unique per chat)
          {platform}     llbot, discord, telegram, ...
          {chat_type}    group | dm | private
          {chat_id}      group/private id (e.g. QQ number)
          {user_id}      sender id (set only in per-user-per-group mode)
          {identity}     active Hermes profile name
        Examples:
          "{session_key}"                       (default; full per-chat bank)
          "{platform}-{chat_type}-{chat_id}"    (platform-scoped per-chat)
          "{chat_type}-{chat_id}"               (per-chat-id, cross-platform)
"""

from __future__ import annotations

import logging
from typing import Any, Dict

# Import the bundled provider as a real module. The memory-plugin loader
# registers ``plugins.memory`` as a package before exec'ing any provider, so
# this resolves whether or not the parent was loaded first.
from plugins.memory.hindsight import (
    HindsightMemoryProvider,
    _sanitize_bank_segment,
)

logger = logging.getLogger(__name__)

_DEFAULT_BANK = "hermes"


def _decompose_session_key(session_key: str) -> Dict[str, str]:
    """Split ``agent:main:<platform>:<chat_type>:<chat_id>[:<user_id>]``."""
    parts = (session_key or "").split(":")
    return {
        "platform": parts[2] if len(parts) > 2 else "",
        "chat_type": parts[3] if len(parts) > 3 else "",
        "chat_id": parts[4] if len(parts) > 4 else "",
        "user_id": parts[5] if len(parts) > 5 else "",
    }


def _collapse(s: str) -> str:
    """Collapse runs of dashes/underscores and trim edges (mirrors hindsight)."""
    while "--" in s:
        s = s.replace("--", "-")
    while "__" in s:
        s = s.replace("__", "_")
    return s.strip("-_")


class SessionKeyHindsightProvider(HindsightMemoryProvider):
    """Hindsight with ``bank_id`` bound to the gateway session key."""

    @property
    def name(self) -> str:
        return "session-key-hindsight"

    def _resolve_session_bank(self, session_key: str, kwargs: dict) -> str:
        """Render the per-chat ``bank_id`` from the configured template."""
        template = str(self._config.get("session_key_bank_template") or "").strip() or "{session_key}"

        decomp = _decompose_session_key(session_key)
        # agent_init passes chat_type/chat_id/user_id as authoritative kwargs;
        # fall back to decomposing the session key when they are absent.
        vals = {
            "session_key": session_key,
            "platform": decomp["platform"],
            "chat_type": str(kwargs.get("chat_type") or decomp["chat_type"] or ""),
            "chat_id": str(kwargs.get("chat_id") or decomp["chat_id"] or ""),
            "user_id": str(kwargs.get("user_id") or decomp["user_id"] or ""),
            "identity": str(kwargs.get("agent_identity") or "default"),
        }
        sanitized = {k: _sanitize_bank_segment(v) for k, v in vals.items()}

        try:
            rendered = template.format(**sanitized)
        except (KeyError, IndexError, ValueError):
            # Unknown/odd placeholder in the user's template → safe fallback.
            rendered = _sanitize_bank_segment(session_key)

        rendered = _collapse(rendered)
        return rendered or _DEFAULT_BANK

    def initialize(self, session_id: str, **kwargs) -> None:
        # Parent does the full setup: loads config, resolves bank via the
        # limited template (no chat/session_key placeholder), builds the
        # (lazy) client, sets document_id, starts the embedded daemon in
        # local mode. We only re-point bank_id afterward.
        super().initialize(session_id, **kwargs)

        session_key = str(kwargs.get("gateway_session_key") or "").strip()
        if not session_key:
            # CLI / cron / subagent — no chat scope. Keep parent's bank.
            return

        self._bank_id = self._resolve_session_bank(session_key, kwargs)
        logger.info(
            "session-key-hindsight: bank=%s (session_key=%s)",
            self._bank_id, session_key,
        )

    def system_prompt_block(self) -> str:
        # Parent block already shows "Bank: <bank_id>"; the session-derived
        # bank is self-evident. Inherit unchanged.
        return super().system_prompt_block()


def register(ctx) -> None:
    """Register session-key-hindsight as a memory provider plugin."""
    ctx.register_memory_provider(SessionKeyHindsightProvider())
