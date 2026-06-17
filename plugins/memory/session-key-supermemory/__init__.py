"""Session-key-scoped Supermemory memory provider.

Subclasses the bundled ``supermemory`` provider and inherits ALL of its
behavior — tools (supermemory-search/save/forget/profile), prefetch recall,
turn capture, full-session ingest, multi-container mode, circuit handling,
config schema. The ONLY override is ``initialize()``, which derives
``container_tag`` from ``gateway_session_key`` instead of the ``{identity}``
template.

Why subclass + container_tag: Supermemory isolates by ``container_tag`` (its
multi-tenant partition — the knob the wiki calls "per-context isolation").
The bundled provider binds that tag to ``{identity}`` (per-profile). Binding
it to the gateway session key gives per-chat memory instead:

- ``group_sessions_per_user: true`` (default): session_key =
  ``agent:main:<platform>:group:<gid>:<uid>`` → **per-user-per-group**.
  Each person in each group has independent memory, AND it does not bleed
  across groups or DMs.
- ``group_sessions_per_user: false``: session_key =
  ``agent:main:<platform>:group:<gid>`` → **per-group collective**. The whole
  group shares one container; cross-group isolated.

Falls back gracefully when no ``gateway_session_key`` is present (CLI, cron,
subagent): keeps the parent's ``{identity}``-scoped tag, so the same provider
works in and out of the gateway.

Config: identical to bundled supermemory (``$HERMES_HOME/supermemory.json`` +
``SUPERMEMORY_API_KEY`` env), PLUS one optional key:

    ``tag_template`` (str, default ``"{session_key}"``)
        Template for the per-chat container_tag. Placeholders (all sanitized
        to ``[a-zA-Z0-9_]``):
          {session_key}  full gateway session key (default; unique per chat)
          {platform}     e.g. llbot, discord, telegram
          {chat_type}    group | dm | private
          {chat_id}      group/private id (e.g. QQ number)
          {user_id}      sender id (set only in per-user-per-group mode)
          {identity}     active Hermes profile name
        Examples:
          "{session_key}"                    (default; full per-chat isolation)
          "{chat_type}-{chat_id}"            (per-chat-id, cross-platform)
          "{identity}-{chat_id}"             (per-profile-per-chat)
          "{platform}-{chat_type}-{chat_id}" (platform-scoped per-chat)
"""

from __future__ import annotations

import logging
from typing import Any, Dict

# Import the bundled provider as a real module. The memory-plugin loader
# registers ``plugins.memory`` as a package (submodule_search_locations
# pointing at this dir) before exec'ing any provider module, so this resolves
# whether or not the parent was loaded first.
from plugins.memory.supermemory import (
    _DEFAULT_CONTAINER_TAG,
    _SupermemoryClient,
    _sanitize_tag,
    SupermemoryMemoryProvider,
)

logger = logging.getLogger(__name__)


def _decompose_session_key(session_key: str) -> Dict[str, str]:
    """Split ``agent:main:<platform>:<chat_type>:<chat_id>[:<user_id>]``.

    Best-effort field extraction for template placeholders. Returns "" for
    any missing segment so templates never KeyError on shape.
    """
    parts = (session_key or "").split(":")
    return {
        "platform": parts[2] if len(parts) > 2 else "",
        "chat_type": parts[3] if len(parts) > 3 else "",
        "chat_id": parts[4] if len(parts) > 4 else "",
        "user_id": parts[5] if len(parts) > 5 else "",
    }


class SessionKeySupermemoryProvider(SupermemoryMemoryProvider):
    """Supermemory with container_tag bound to the gateway session key."""

    @property
    def name(self) -> str:
        return "session-key-supermemory"

    def _resolve_session_tag(self, session_key: str, kwargs: dict) -> str:
        """Render the per-chat container_tag from the configured template."""
        template = str(self._config.get("tag_template") or "").strip() or "{session_key}"

        decomp = _decompose_session_key(session_key)
        # agent_init passes chat_type/chat_id/user_id as authoritative kwargs;
        # fall back to decomposing the session key when they are absent.
        platform = decomp["platform"]
        chat_type = str(kwargs.get("chat_type") or decomp["chat_type"] or "")
        chat_id = str(kwargs.get("chat_id") or decomp["chat_id"] or "")
        user_id = str(kwargs.get("user_id") or decomp["user_id"] or "")
        identity = str(kwargs.get("agent_identity") or "default")

        try:
            resolved = template.format(
                session_key=_sanitize_tag(session_key),
                platform=_sanitize_tag(platform),
                chat_type=_sanitize_tag(chat_type),
                chat_id=_sanitize_tag(chat_id),
                user_id=_sanitize_tag(user_id),
                identity=_sanitize_tag(identity),
            )
        except (KeyError, IndexError, ValueError):
            # Unknown/odd placeholder in the user's template → safe fallback.
            resolved = _sanitize_tag(session_key)

        return _sanitize_tag(resolved) or _DEFAULT_CONTAINER_TAG

    def initialize(self, session_id: str, **kwargs) -> None:
        # Parent does the full setup: loads config, resolves the {identity} tag,
        # builds the client, sets _active/_api_key/_search_mode, etc.
        super().initialize(session_id, **kwargs)

        session_key = str(kwargs.get("gateway_session_key") or "").strip()
        if not session_key:
            # CLI / cron / subagent — no chat scope. Keep parent's identity tag.
            return

        self._container_tag = self._resolve_session_tag(session_key, kwargs)

        # The parent already constructed self._client with the {identity} tag
        # baked in (the client's container_tag is a constructor default, not a
        # per-call field). Rebuild it so every inherited call (prefetch,
        # sync_turn, ingest, tools) targets the session-scoped container.
        if self._active:
            try:
                self._client = _SupermemoryClient(
                    api_key=self._api_key,
                    timeout=self._api_timeout,
                    container_tag=self._container_tag,
                    search_mode=self._search_mode,
                )
            except Exception:
                logger.warning(
                    "session-key-supermemory: client rebuild failed for "
                    "container '%s'; deactivating.", self._container_tag,
                    exc_info=True,
                )
                self._active = False
                self._client = None

        # Refresh the multi-container whitelist so the session tag is the
        # primary allowed container (custom containers stay appended).
        self._allowed_containers = [self._container_tag] + list(self._custom_containers)

        logger.debug(
            "session-key-supermemory scoped to container '%s' (session=%s)",
            self._container_tag, session_key,
        )

    def system_prompt_block(self) -> str:
        block = super().system_prompt_block()
        if block and self._active:
            # Make per-chat scoping explicit; the parent block already shows the
            # resolved container tag, so the agent sees which chat it is in.
            block = block.replace("# Supermemory\n", "# Supermemory (session-key scoped)\n", 1)
        return block


def register(ctx) -> None:
    """Register session-key-supermemory as a memory provider plugin."""
    ctx.register_memory_provider(SessionKeySupermemoryProvider())
