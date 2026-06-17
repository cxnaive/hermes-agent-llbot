"""Pure protocol helpers for the OneBot v11 wire format used by LLBot.

No I/O lives here — every function is a pure transformation so the module is
trivial to unit-test in isolation.  The adapter (``adapter.py``) owns all
network/async work and calls into here to (de)serialise messages.

OneBot v11 message representation comes in two flavours:
  * ``message_format: "array"`` — ``message`` is a list of segment dicts
    ``{"type": "text", "data": {...}}``.  LLBot (LLOneBot) uses this by default.
  * ``message_format: "string"`` — ``message``/``raw_message`` is a CQ-code
    string (``"hi [CQ:at,qq=123] [CQ:image,file=x,url=http://...]"``).

We handle both.  ``LLBOT_*`` identity fields (``self_id``, group/user ids) are
integers on the wire; Hermes ``chat_id`` is a string, so we encode the scene
into ``chat_id`` itself (``"group:<id>"`` / ``"private:<id>"``) so outbound
routing never needs an in-memory lookup table.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# chat_id encoding — keeps the scene (group vs private) inside the id string
# so both the in-process adapter and the out-of-process standalone sender can
# route without sharing state.
# ---------------------------------------------------------------------------

GROUP_PREFIX = "group:"
PRIVATE_PREFIX = "private:"


def encode_chat_id(message_type: str, raw_id: Any) -> str:
    """Map a OneBot ``message_type`` + raw id to a Hermes chat_id string.

    ``message_type`` is the OneBot field (``"group"`` or ``"private"``); the
    returned chat_id carries the scene so ``send``/``standalone_send`` can pick
    ``send_group_msg`` vs ``send_private_msg`` from the id alone.
    """
    if message_type == "group":
        return f"group:{raw_id}"
    return f"private:{raw_id}"


def parse_chat_id(chat_id: str) -> Tuple[str, int]:
    """Split a Hermes chat_id into ``(scene, numeric_id)``.

    ``scene`` is ``"group"`` or ``"private"``; ``numeric_id`` is the int OneBot
    expects in ``send_group_msg``/``send_private_msg`` params.  Raises
    ``ValueError`` on a malformed id so callers fail loudly rather than sending
    to the wrong target.
    """
    if not isinstance(chat_id, str):
        raise ValueError(f"chat_id must be a string, got {type(chat_id).__name__}")
    text = chat_id.strip()
    if text.startswith(GROUP_PREFIX):
        scene = "group"
        raw = text[len(GROUP_PREFIX):]
    elif text.startswith(PRIVATE_PREFIX):
        scene = "private"
        raw = text[len(PRIVATE_PREFIX):]
    elif text.isdigit():
        # Bare numeric id — assume private (user QQ). Agents sometimes pass
        # the raw QQ without the "private:" prefix; default to DM. Group ids
        # must be explicitly "group:<id>" to avoid ambiguity.
        return "private", int(text)
    else:
        raise ValueError(
            f"Malformed LLBot chat_id {chat_id!r}: expected 'group:<id>' or 'private:<id>'"
        )
    try:
        return scene, int(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"LLBot chat_id {chat_id!r} has a non-numeric id part") from exc


def chat_id_to_chat_type(chat_id: str) -> str:
    """Return the Hermes ``chat_type`` (``'group'`` or ``'dm'``) for a chat_id."""
    scene, _ = parse_chat_id(chat_id)
    return "group" if scene == "group" else "dm"


# ---------------------------------------------------------------------------
# Outbound segment construction
# ---------------------------------------------------------------------------

def text_segment(text: str) -> dict:
    """OneBot ``text`` message segment."""
    return {"type": "text", "data": {"text": text}}


def reply_segment(message_id: Any) -> dict:
    """OneBot ``reply`` segment — must be the FIRST element of the message array."""
    return {"type": "reply", "data": {"id": str(message_id)}}


def at_segment(qq: Any) -> dict:
    """OneBot ``at`` segment.  ``qq`` may be a user id int/str or ``"all"``."""
    return {"type": "at", "data": {"qq": str(qq)}}


def image_segment(file_ref: str, **extra: Any) -> dict:
    """OneBot ``image`` segment.

    ``file_ref`` is one of the OneBot file reference forms:
    ``file://<path>``, ``http(s)://<url>``, or ``base64://<data>``.
    """
    data: Dict[str, Any] = {"file": file_ref}
    data.update({k: v for k, v in extra.items() if v is not None})
    return {"type": "image", "data": data}


def record_segment(file_ref: str, **extra: Any) -> dict:
    """OneBot ``record`` (voice) segment.  Same ``file_ref`` forms as image."""
    data: Dict[str, Any] = {"file": file_ref}
    data.update({k: v for k, v in extra.items() if v is not None})
    return {"type": "record", "data": data}


def file_segment(file_ref: str, name: Optional[str] = None, **extra: Any) -> dict:
    """OneBot ``file`` segment."""
    data: Dict[str, Any] = {"file": file_ref}
    if name:
        data["name"] = name
    data.update({k: v for k, v in extra.items() if v is not None})
    return {"type": "file", "data": data}


def build_send_segments(text: str, reply_to: Optional[str] = None) -> List[dict]:
    """Build the OneBot ``message`` array for an outbound text send.

    A ``reply`` segment (when ``reply_to`` is set) is placed FIRST per the
    OneBot v11 convention, followed by the text body.  Empty text after a
    reply still produces a valid one-element reply-only message.
    """
    segments: List[dict] = []
    if reply_to:
        segments.append(reply_segment(reply_to))
    if text:
        segments.append(text_segment(text))
    if not segments:
        # Degenerate input — emit a single empty text so the action payload is
        # never an empty array (some OneBot impls reject []).
        segments.append(text_segment(""))
    return segments


def build_file_ref(local_path: str) -> str:
    """Wrap a local filesystem path as a OneBot ``file://`` reference."""
    # Normalise to an absolute path without the leading slash doubling up.
    return "file://" + str(local_path).replace("file://", "", 1)


# ---------------------------------------------------------------------------
# Forward bundles (合并转发)
# ---------------------------------------------------------------------------

def _last_sentence_end(region: str) -> int:
    """Offset *just past* the last sentence-ending period in ``region``.

    Returns 0 when the region contains no usable sentence end.  ``。`` always
    counts; ``.`` counts only when the following char is whitespace/newline or
    absent — this keeps ``3.14``, ``example.com``, ``e.g.`` and ``file.txt``
    from being mistaken for sentence boundaries.
    """
    for i in range(len(region) - 1, -1, -1):
        ch = region[i]
        if ch == "。":
            return i + 1
        if ch == ".":
            nxt = region[i + 1] if i + 1 < len(region) else ""
            if nxt == "" or nxt.isspace():
                return i + 1
    return 0


def split_text_by_sentences(text: str, limit: int = 800) -> List[str]:
    """Split ``text`` into chunks of at most ``limit`` chars.

    The split greedily lands on the **last** sentence-ending period that still
    fits within ``limit`` (so each chunk is as large as possible without
    exceeding the cap).  Sentence endings: Chinese ``。`` (always) and ASCII
    ``.`` (only when followed by whitespace/newline/EOL).  When no period fits
    in the current ``limit``-sized window, the cut falls back to the last
    newline, then the last space, then a hard break at ``limit``.  Chunks are
    stripped; the trailing remainder (when non-empty) is the final chunk.
    Returns ``[text]`` unchanged when it already fits.
    """
    if limit < 1:
        limit = 1
    text = "" if text is None else text
    if len(text) <= limit:
        return [text]

    chunks: List[str] = []
    remaining = text
    while len(remaining) > limit:
        region = remaining[:limit]
        cut = _last_sentence_end(region)
        if cut < 1:
            # No sentence end in this window — fall back to softer boundaries.
            nl = region.rfind("\n")
            sp = region.rfind(" ")
            cut = max(nl, sp)
            if cut < 1:
                cut = limit
        piece = remaining[:cut].strip()
        if piece:
            chunks.append(piece)
        remaining = remaining[cut:]
    if remaining.strip():
        chunks.append(remaining.strip())
    return chunks


def forward_node(content, *, uin: Any = "", name: str = "Hermes") -> dict:
    """Build a custom ``node`` segment for a 合并转发 (forward) bundle.

    ``content`` is a message-segment array (e.g. ``[text_segment(...)]``).  The
    node schema also accepts a plain string for ``content``, but the array form
    is the portable one across LLOneBot/NapCat/go-cqhttp.  ``uin``/``name`` are
    the (fake) sender identity shown on the node — pass the bot's own ``self_id``
    and a display label.
    """
    data: Dict[str, Any] = {"name": name, "content": content}
    if uin:
        data["uin"] = uin
    return {"type": "node", "data": data}


# ---------------------------------------------------------------------------
# Action / envelope helpers
# ---------------------------------------------------------------------------

def build_action(action: str, params: Dict[str, Any], echo: str) -> str:
    """Serialise an OneBot action call to a JSON string for ``ws.send_str``.

    Returns a string (not a dict) so the adapter can hand it straight to
    ``ws.send_str`` without an extra ``json.dumps`` at the call site.
    """
    import json

    return json.dumps(
        {"action": action, "params": params, "echo": echo},
        ensure_ascii=False,
    )


def auth_headers(access_token: Optional[str]) -> Dict[str, str]:
    """OneBot v11 access-token auth headers (empty when no token is configured)."""
    if not access_token:
        return {}
    return {"Authorization": f"Bearer {access_token}"}


def action_url(access_token: Optional[str], base: str) -> str:
    """Append ``?access_token=`` to an HTTP action URL when a token is set.

    WebSocket auth goes through :func:`auth_headers`; this covers the HTTP API
    and reverse-WS query-param form as a defensive fallback (LLBot's docs only
    document the ``Authorization`` header, but the standard query-param form is
    widely accepted by OneBot implementations).
    """
    if not access_token:
        return base
    sep = "&" if "?" in base else "?"
    return f"{base}{sep}access_token={access_token}"


def is_response(payload: dict) -> bool:
    """True when an inbound WS frame is an action *response* (not an event).

    OneBot responses carry an ``echo`` field echoing the request's correlation
    id; events carry ``post_type`` instead.
    """
    return isinstance(payload, dict) and "echo" in payload and "post_type" not in payload


def response_ok(payload: dict) -> bool:
    """OneBot response success: ``status == "ok"`` or ``retcode == 0``."""
    if not isinstance(payload, dict):
        return False
    if payload.get("status") == "ok":
        return True
    return payload.get("retcode") == 0


# ---------------------------------------------------------------------------
# Inbound message parsing
# ---------------------------------------------------------------------------

@dataclass
class ParsedMessage:
    """Result of parsing an inbound OneBot message into Hermes-friendly fields.

    ``images`` / ``records`` / ``files`` hold the raw segment ``data`` dicts so
    the adapter can resolve them (via ``get_image``/``get_record``/``get_file``
    or a direct URL download) without this module doing any I/O.
    """

    text: str = ""
    reply_to_message_id: Optional[str] = None
    mentioned_self: bool = False
    mentioned_all: bool = False
    images: List[dict] = field(default_factory=list)
    records: List[dict] = field(default_factory=list)
    files: List[dict] = field(default_factory=list)


# Matches a CQ-code: [CQ:type,k=v,k2=v2,...] (type and keys are non-greedy,
# values run up to the next comma or closing bracket).
_CQ_RE = re.compile(r"\[CQ:([a-zA-Z_]+)((?:,[^,\]]*)*?)\]")


def _split_cq_params(params_str: str) -> Dict[str, str]:
    """Parse the ``,k=v,k2=v2`` tail of a CQ code into a dict."""
    out: Dict[str, str] = {}
    for chunk in params_str.split(","):
        chunk = chunk.strip()
        if not chunk or "=" not in chunk:
            continue
        key, _, value = chunk.partition("=")
        # OneBot CQ values can be XML/HTML-entity escaped (&amp;); unescape the
        # common ones so image URLs etc. come back usable.
        value = (value.replace("&amp;", "&")
                      .replace("&#44;", ",")
                      .replace("&#91;", "[")
                      .replace("&#93;", "]"))
        out[key.strip()] = value
    return out


def _parse_cq_string(message: str, self_id: Any) -> ParsedMessage:
    """Parse a ``message_format: "string"`` CQ-code message into ParsedMessage.

    Best-effort: extracts text, @-mentions, reply, image, record, file from the
    CQ codes.  LLBot defaults to the array form; this path covers the string
    form for completeness.
    """
    result = ParsedMessage()
    self_id_str = str(self_id) if self_id is not None else ""
    cursor = 0
    text_parts: List[str] = []

    for match in _CQ_RE.finditer(message):
        # Capture the literal text before this CQ code.
        if match.start() > cursor:
            text_parts.append(message[cursor:match.start()])
        cursor = match.end()

        cq_type = match.group(1)
        data = _split_cq_params(match.group(2))
        _fold_segment(result, cq_type, data, self_id_str, text_parts)

    # Trailing literal text after the last CQ code.
    if cursor < len(message):
        text_parts.append(message[cursor:])

    result.text = "".join(text_parts).strip()
    return result


def _fold_segment(
    result: ParsedMessage,
    seg_type: str,
    data: Dict[str, Any],
    self_id_str: str,
    text_parts: List[str],
) -> None:
    """Fold a single parsed segment (array or CQ-string form) into ``result``."""
    if seg_type == "text":
        text_parts.append(str(data.get("text", "")))
    elif seg_type == "at":
        qq = str(data.get("qq", "")).strip()
        if qq.lower() == "all":
            # @全体成员 is a mention trigger, not message content — don't
            # pollute the text (mentioned_all carries the signal).
            result.mentioned_all = True
        elif qq and qq == self_id_str:
            # @bot is a trigger handled by the require_mention gate; keep the
            # agent-facing text clean.
            result.mentioned_self = True
        else:
            # @another user — preserve so the agent can see who was mentioned.
            name = data.get("name") or qq
            text_parts.append(f"@{name} ")
    elif seg_type == "reply":
        rid = data.get("id")
        if rid:
            result.reply_to_message_id = str(rid)
    elif seg_type == "image":
        result.images.append(data)
    elif seg_type == "record":
        result.records.append(data)
    elif seg_type == "file":
        result.files.append(data)
    # face/mface/json/markdown/forward/etc. — out of scope for v1; ignored.


def parse_message(message: Any, self_id: Any) -> ParsedMessage:
    """Parse an inbound OneBot ``message`` field into :class:`ParsedMessage`.

    ``message`` may be a list of segment dicts (``message_format: "array"``) or
    a CQ-code string (``message_format: "string"``).  ``self_id`` is the bot's
    own QQ id, used to detect self-mentions.
    """
    self_id_str = str(self_id) if self_id is not None else ""

    if isinstance(message, str):
        return _parse_cq_string(message, self_id_str)

    result = ParsedMessage()
    if not isinstance(message, list):
        return result

    text_parts: List[str] = []
    for segment in message:
        if not isinstance(segment, dict):
            continue
        seg_type = segment.get("type")
        data = segment.get("data") or {}
        if not isinstance(data, dict):
            data = {}
        _fold_segment(result, seg_type, data, self_id_str, text_parts)

    result.text = "".join(text_parts).strip()
    return result


def _iter_cq_string(message: str) -> List[Tuple[str, Dict[str, Any]]]:
    """Parse a CQ-code string into ordered ``[(type, data), ...]`` segments."""
    out: List[Tuple[str, Dict[str, Any]]] = []
    cursor = 0
    for match in _CQ_RE.finditer(message):
        if match.start() > cursor:
            out.append(("text", {"text": message[cursor:match.start()]}))
        cursor = match.end()
        out.append((match.group(1), _split_cq_params(match.group(2))))
    if cursor < len(message):
        out.append(("text", {"text": message[cursor:]}))
    return out


def iter_message_segments(message: Any) -> List[Tuple[str, Dict[str, Any]]]:
    """Return a message's segments as an ordered ``[(type, data), ...]`` list.

    Unlike :func:`parse_message` — which buckets text/images/records/files into
    separate fields and so loses their interleaving — this preserves the
    original order. A caller can therefore render text and media inline to
    faithfully reproduce a message, e.g. quoting a replied-to message as
    ``"看这张图 [图片1] 然后看 [图片2]"`` instead of a flattened text blob plus
    unordered attachments. Handles the array (``message_format: "array"``) and
    CQ-string forms; non-dict entries are skipped.
    """
    if isinstance(message, str):
        return _iter_cq_string(message)
    if not isinstance(message, list):
        return []
    out: List[Tuple[str, Dict[str, Any]]] = []
    for seg in message:
        if not isinstance(seg, dict):
            continue
        data = seg.get("data") or {}
        if not isinstance(data, dict):
            data = {}
        out.append((str(seg.get("type")), data))
    return out


def poke_notice_to_text(user_name: str) -> str:
    """Render a poke (戳一戳) notice as an agent-facing message string."""
    who = user_name or "有人"
    return f"[戳一戳] {who} 戳了戳你"


def best_file_ref(segment_data: dict) -> Optional[str]:
    """Pick the most useful file reference from an image/record/file segment.

    Order: a usable ``url`` (http/https) → ``base64`` payload → ``file`` name.
    Returns ``None`` when nothing resolvable is present (the adapter then falls
    back to the ``get_image``/``get_record``/``get_file`` action with ``file``).
    """
    url = str(segment_data.get("url") or "").strip()
    if url.startswith(("http://", "https://")):
        return url
    b64 = str(segment_data.get("base64") or "").strip()
    if b64:
        return "base64://" + b64
    f = str(segment_data.get("file") or "").strip()
    if f:
        # A bare filename/hash needs resolving through get_*; surface it so the
        # adapter can decide.  ``file://``/``http://``/``base64://`` pass through.
        return f
    return None
