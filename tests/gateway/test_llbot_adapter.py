"""Tests for the LLBot (OneBot v11) platform plugin.

Loads the adapter in isolation via the shared plugin-adapter loader (no
``sys.path`` tricks — see ``tests/gateway/conftest.py``) and exercises the
protocol helpers, inbound dispatch, mention gate, and outbound send routing.
Async logic runs through ``asyncio.run`` so the suite does not depend on a
particular pytest-asyncio mode.
"""

import asyncio
import os
from unittest.mock import AsyncMock

import pytest

from tests.gateway._plugin_adapter_loader import load_plugin_adapter

_mod = load_plugin_adapter("llbot")
LLBotAdapter = _mod.LLBotAdapter
register = _mod.register
onebot = _mod.onebot


@pytest.fixture(autouse=True)
def _clean_llbot_env(monkeypatch):
    for key in (
        "LLBOT_WS_URL", "LLBOT_ACCESS_TOKEN", "LLBOT_REQUIRE_MENTION",
        "LLBOT_HOME_CHANNEL", "LLBOT_ALLOWED_USERS", "LLBOT_ALLOW_ALL_USERS",
    ):
        monkeypatch.delenv(key, raising=False)


def _make_adapter(**extra):
    from gateway.config import PlatformConfig

    cfg = PlatformConfig(enabled=True, extra={"ws_url": "ws://127.0.0.1:3001", **extra})
    return LLBotAdapter(cfg)


def _run(coro):
    return asyncio.run(coro)


def _capture(adapter):
    """Mock handle_message + media resolvers so we can assert on the event."""
    adapter.handle_message = AsyncMock()
    adapter._resolve_image = AsyncMock(return_value=None)
    adapter._resolve_record = AsyncMock(return_value=None)
    adapter._resolve_file = AsyncMock(return_value=None)
    adapter._self_id = "111"
    return adapter


def _connected(adapter):
    """Mark the adapter connected + stub _call_action for outbound tests."""
    adapter._running = True
    adapter._call_action = AsyncMock(
        return_value={"status": "ok", "retcode": 0, "data": {"message_id": 42}}
    )
    return adapter


# ── requirements / config / env enablement ──────────────────────────────


def test_check_requirements_reflects_aiohttp_dep():
    # check_fn gates only on the aiohttp dependency; ws_url is validate_config's
    # job (so a config.yaml-only setup with ws_url in extra isn't rejected here).
    assert _mod.check_requirements() is True  # aiohttp available in test env


def test_validate_config_accepts_env(monkeypatch):
    monkeypatch.setenv("LLBOT_WS_URL", "ws://x:1")
    from gateway.config import PlatformConfig
    assert _mod.validate_config(PlatformConfig(enabled=True, extra={})) is True


def test_validate_config_accepts_extra(monkeypatch):
    monkeypatch.delenv("LLBOT_WS_URL", raising=False)
    from gateway.config import PlatformConfig
    cfg = PlatformConfig(enabled=True, extra={"ws_url": "ws://127.0.0.1:3001"})
    assert _mod.validate_config(cfg) is True


def test_validate_config_rejects_empty(monkeypatch):
    monkeypatch.delenv("LLBOT_WS_URL", raising=False)
    from gateway.config import PlatformConfig
    assert _mod.validate_config(PlatformConfig(enabled=True, extra={})) is False


def test_validate_config_from_extra():
    assert _mod.validate_config(_make_adapter().config) is True


def test_env_enablement_seeds_extra(monkeypatch):
    monkeypatch.setenv("LLBOT_WS_URL", "ws://h:1")
    monkeypatch.setenv("LLBOT_ACCESS_TOKEN", "tok")
    monkeypatch.setenv("LLBOT_HOME_CHANNEL", "group:5")
    seed = _mod._env_enablement()
    assert seed["ws_url"] == "ws://h:1"
    assert seed["access_token"] == "tok"
    assert seed["home_channel"] == {"chat_id": "group:5", "name": "group:5"}
    assert seed["require_mention"] is True


def test_env_enablement_none_when_unconfigured(monkeypatch):
    monkeypatch.delenv("LLBOT_WS_URL", raising=False)
    assert _mod._env_enablement() is None


def test_adapter_reads_extra_when_env_absent():
    adapter = _make_adapter(access_token="from-extra", require_mention=False)
    assert adapter.ws_url == "ws://127.0.0.1:3001"
    assert adapter.access_token == "from-extra"
    assert adapter.require_mention is False


def test_connect_accepts_is_reconnect_kwarg():
    # Upstream's base connect(*, is_reconnect=False); the gateway forwards
    # is_reconnect on reconnects. The override must accept it or the gateway
    # fails with "unexpected keyword argument 'is_reconnect'".
    import inspect
    sig = inspect.signature(LLBotAdapter.connect)
    assert "is_reconnect" in sig.parameters


# ── chat_id encoding ────────────────────────────────────────────────────


def test_chat_id_roundtrip():
    assert onebot.encode_chat_id("group", 123) == "group:123"
    assert onebot.encode_chat_id("private", 9) == "private:9"
    assert onebot.parse_chat_id("group:123") == ("group", 123)
    assert onebot.parse_chat_id("private:9") == ("private", 9)
    assert onebot.chat_id_to_chat_type("group:1") == "group"
    assert onebot.chat_id_to_chat_type("private:1") == "dm"


@pytest.mark.parametrize("bad", ["", "group:", "group:abc", "weird:1"])
def test_chat_id_malformed(bad):
    with pytest.raises(ValueError):
        onebot.parse_chat_id(bad)


def test_chat_id_bare_numeric_defaults_to_private():
    # Agents sometimes pass a raw QQ without "private:" — default to DM.
    # Group ids must stay explicitly "group:<id>" to avoid ambiguity.
    assert onebot.parse_chat_id("3883393282") == ("private", 3883393282)


# ── parse_message ───────────────────────────────────────────────────────


def test_parse_message_array_text_at_reply_media():
    msg = [
        {"type": "reply", "data": {"id": "77"}},
        {"type": "at", "data": {"qq": "111"}},
        {"type": "at", "data": {"qq": "all"}},
        {"type": "text", "data": {"text": "hello"}},
        {"type": "image", "data": {"file": "x.png", "url": "http://e/i.png"}},
        {"type": "record", "data": {"file": "v.amr"}},
        {"type": "file", "data": {"file": "d.pdf", "name": "doc.pdf"}},
    ]
    parsed = onebot.parse_message(msg, "111")
    assert parsed.mentioned_self is True
    assert parsed.mentioned_all is True
    assert parsed.reply_to_message_id == "77"
    # @self / @all are mention triggers and are stripped from the text body.
    assert parsed.text == "hello"
    assert len(parsed.images) == 1 and parsed.images[0]["url"] == "http://e/i.png"
    assert len(parsed.records) == 1
    assert len(parsed.files) == 1 and parsed.files[0]["name"] == "doc.pdf"


def test_parse_message_at_other_is_not_self():
    parsed = onebot.parse_message(
        [{"type": "at", "data": {"qq": "999"}}, {"type": "text", "data": {"text": "hi"}}],
        "111",
    )
    assert parsed.mentioned_self is False
    assert parsed.mentioned_all is False
    assert "hi" in parsed.text


def test_parse_message_cq_string():
    msg = "hi [CQ:at,qq=111] [CQ:at,qq=all] [CQ:image,file=x,url=http://e/i.png] end"
    parsed = onebot.parse_message(msg, "111")
    assert parsed.mentioned_self is True
    assert parsed.mentioned_all is True
    assert "hi" in parsed.text and "end" in parsed.text
    assert len(parsed.images) == 1 and parsed.images[0]["url"] == "http://e/i.png"


def test_parse_message_cq_reply():
    parsed = onebot.parse_message("[CQ:reply,id=55] answer", "1")
    assert parsed.reply_to_message_id == "55"
    assert "answer" in parsed.text


def test_parse_message_empty_and_non_list():
    assert onebot.parse_message(None, "1").text == ""
    assert onebot.parse_message([], "1").text == ""
    assert onebot.parse_message("plain text", "1").text == "plain text"


def test_best_file_ref_prefers_url():
    assert onebot.best_file_ref({"url": "http://e/x.png"}) == "http://e/x.png"
    assert onebot.best_file_ref({"base64": "AAAA"}) == "base64://AAAA"
    assert onebot.best_file_ref({"file": "abc.hash"}) == "abc.hash"
    assert onebot.best_file_ref({}) is None


# ── inbound dispatch ────────────────────────────────────────────────────


def _group_msg(mid, text, at_self=False, at_all=False, at_other=None):
    segs = []
    if at_self:
        segs.append({"type": "at", "data": {"qq": "111"}})
    if at_all:
        segs.append({"type": "at", "data": {"qq": "all"}})
    if at_other:
        segs.append({"type": "at", "data": {"qq": str(at_other), "name": f"用户{at_other}"}})
    segs.append({"type": "text", "data": {"text": text}})
    return {
        "post_type": "message", "message_type": "group", "group_id": 5,
        "user_id": 222, "message_id": mid, "sender": {"nickname": "Alice"},
        "message": segs,
    }


def test_group_message_without_mention_dropped():
    adapter = _capture(_make_adapter())
    _run(adapter._handle_inbound_message(_group_msg("m1", "hi", at_self=False)))
    adapter.handle_message.assert_not_called()


def test_group_message_with_mention_self_passes():
    adapter = _capture(_make_adapter())
    _run(adapter._handle_inbound_message(_group_msg("m2", "hi", at_self=True)))
    event = adapter.handle_message.call_args.args[0]
    assert event.text == "[Alice (QQ 222) @你] hi"
    assert event.source.chat_id == "group:5"
    assert event.source.chat_type == "group"
    assert event.source.user_id == "222"


def test_mention_note_not_prefixed_on_slash_command():
    # @bot + /whoami → text must stay "/whoami" (no [@你] prefix) so the
    # gateway's get_command() recognizes it as a slash command.
    adapter = _capture(_make_adapter())
    _run(adapter._handle_inbound_message(_group_msg("cmd1", "/whoami", at_self=True)))
    event = adapter.handle_message.call_args.args[0]
    assert event.text == "/whoami"


def test_group_message_mention_all_marked_in_text():
    # @everyone passes the gate; the agent must see it's an @all, not a @bot.
    adapter = _capture(_make_adapter())
    _run(adapter._handle_inbound_message(_group_msg("m_all", "大家注意", at_all=True)))
    event = adapter.handle_message.call_args.args[0]
    assert event.text == "[Alice (QQ 222) @全体成员] 大家注意"


def test_group_message_mention_other_kept_inline():
    # @another user (not the bot, not everyone) stays in the body so the agent
    # sees who else was tagged; combined with @bot so it passes the gate.
    adapter = _capture(_make_adapter())
    _run(adapter._handle_inbound_message(
        _group_msg("m_o", "你看下", at_self=True, at_other=999)
    ))
    event = adapter.handle_message.call_args.args[0]
    assert event.text.startswith("[Alice (QQ 222) @你]")
    assert "@用户999" in event.text


def test_private_message_passes_without_mention():
    adapter = _capture(_make_adapter())
    payload = {
        "post_type": "message", "message_type": "private", "user_id": 333,
        "message_id": "m3", "sender": {"nickname": "Bob"},
        "message": [{"type": "text", "data": {"text": "yo"}}],
    }
    _run(adapter._handle_inbound_message(payload))
    event = adapter.handle_message.call_args.args[0]
    assert event.source.chat_id == "private:333"
    assert event.source.chat_type == "dm"
    # DM sender is labeled ``昵称 (QQ <id>)`` so the agent can match the speaker
    # against QQ-numbered identity rules (no mention note in DMs otherwise).
    assert event.text == "[Bob (QQ 333)] yo"


def test_require_mention_disabled_lets_unaddressed_through():
    adapter = _capture(_make_adapter(require_mention=False))
    _run(adapter._handle_inbound_message(_group_msg("m4", "hi", at_self=False)))
    adapter.handle_message.assert_awaited_once()


def test_message_id_dedup():
    adapter = _capture(_make_adapter())
    payload = {
        "post_type": "message", "message_type": "private", "user_id": 1,
        "message_id": "dup", "sender": {},
        "message": [{"type": "text", "data": {"text": "x"}}],
    }
    _run(adapter._handle_inbound_message(payload))
    _run(adapter._handle_inbound_message(payload))
    assert adapter.handle_message.await_count == 1


def test_message_sent_event_is_dropped():
    adapter = _capture(_make_adapter())

    async def go():
        adapter._dispatch_event({
            "post_type": "message_sent", "self_id": 111, "message_type": "group",
            "group_id": 5, "message_id": "ms1",
            "message": [{"type": "text", "data": {"text": "echo"}}],
        })
        await asyncio.sleep(0.05)

    _run(go())
    adapter.handle_message.assert_not_called()


def test_meta_event_latches_self_id():
    adapter = _make_adapter()
    assert adapter._self_id == ""
    adapter._dispatch_event({"post_type": "meta_event", "self_id": 99999})
    assert adapter._self_id == "99999"


def test_poke_notice_dispatches_as_text():
    adapter = _capture(_make_adapter())

    async def go():
        adapter._dispatch_event({
            "post_type": "notice", "notice_type": "notify", "sub_type": "poke",
            "self_id": 111, "user_id": 222, "group_id": 5,
            "sender": {"nickname": "Bob"},
        })
        await asyncio.sleep(0.05)

    _run(go())
    event = adapter.handle_message.call_args.args[0]
    # Poker is labeled with nickname AND QQ number so identity rules can key
    # off the QQ (nickname alone is spoofable).
    assert "戳" in event.text and "Bob" in event.text and "QQ 222" in event.text
    assert event.source.chat_type == "group"
    assert event.source.chat_id == "group:5"


def test_poke_targeting_bot_dispatches():
    adapter = _capture(_make_adapter())

    async def go():
        adapter._dispatch_event({
            "post_type": "notice", "notice_type": "notify", "sub_type": "poke",
            "self_id": 111, "user_id": 222, "target_id": 111, "group_id": 5,
            "sender": {"nickname": "Bob"},
        })
        await asyncio.sleep(0.05)

    _run(go())
    event = adapter.handle_message.call_args.args[0]
    assert "戳" in event.text  # bot was the target → dispatched


def test_poke_targeting_other_member_is_ignored():
    # A member poking ANOTHER member (not the bot) must not wake the agent.
    adapter = _capture(_make_adapter())

    async def go():
        adapter._dispatch_event({
            "post_type": "notice", "notice_type": "notify", "sub_type": "poke",
            "self_id": 111, "user_id": 222, "target_id": 999, "group_id": 5,
            "sender": {"nickname": "Bob"},
        })
        await asyncio.sleep(0.05)

    _run(go())
    adapter.handle_message.assert_not_called()


def test_poke_drains_observe_like_a_trigger():
    # A poke behaves like a normal trigger: drains observed chatter, carries
    # the [now:] marker, and sets channel_prompt — only the text differs.
    adapter = _observe_adapter()
    _run(adapter._handle_inbound_message(_group_msg("pk1", "闲聊", at_self=False)))

    async def go():
        adapter._dispatch_event({
            "post_type": "notice", "notice_type": "notify", "sub_type": "poke",
            "self_id": 111, "user_id": 222, "target_id": 111, "group_id": 5,
            "time": 1737000030, "sender": {"nickname": "Bob"},
        })
        await asyncio.sleep(0.05)

    _run(go())
    event = adapter.handle_message.call_args.args[0]
    assert "[戳一戳]" in event.text and "Bob" in event.text
    assert event.channel_context is not None
    assert "[now:" in event.channel_context          # [now:] marker (trigger time)
    assert "闲聊" in event.channel_context            # drained observed chatter
    assert event.channel_prompt is not None          # reply/media hint set
    assert "group:5" in event.channel_prompt
    assert "MEDIA:" in event.channel_prompt
    assert not adapter._observed.get("group:5")      # buffer cleared by drain


def test_inbound_image_attach_sets_media_and_photo_type():
    adapter = _capture(_make_adapter())
    adapter._resolve_image = AsyncMock(return_value="/tmp/cached.png")
    payload = {
        "post_type": "message", "message_type": "private", "user_id": 1,
        "message_id": "m5", "sender": {},
        "message": [
            {"type": "text", "data": {"text": "look"}},
            {"type": "image", "data": {"file": "x.png", "url": "http://e/i.png"}},
        ],
    }
    _run(adapter._handle_inbound_message(payload))
    event = adapter.handle_message.call_args.args[0]
    assert event.media_urls == ["/tmp/cached.png"]
    assert event.media_types == ["image/jpeg"]
    from gateway.platforms.base import MessageType

    assert event.message_type == MessageType.PHOTO


# ── reply / quote resolution (get_msg) ──────────────────────────────────


def _quoted_payload(mid, text, reply_id="999", at_self=True):
    segs = [{"type": "reply", "data": {"id": str(reply_id)}}]
    if at_self:
        segs.append({"type": "at", "data": {"qq": "111"}})
    segs.append({"type": "text", "data": {"text": text}})
    return {
        "post_type": "message", "message_type": "group", "group_id": 5,
        "user_id": 222, "message_id": mid, "sender": {"nickname": "Alice"},
        "message": segs,
    }


def test_iter_message_segments_preserves_order():
    segs = onebot.iter_message_segments([
        {"type": "text", "data": {"text": "A"}},
        {"type": "image", "data": {"file": "1"}},
        {"type": "text", "data": {"text": "B"}},
        {"type": "image", "data": {"file": "2"}},
    ])
    assert [t for t, _ in segs] == ["text", "image", "text", "image"]
    # CQ-string form preserves order too.
    segs2 = onebot.iter_message_segments("A[CQ:image,file=1]B")
    assert [t for t, _ in segs2] == ["text", "image", "text"]
    assert segs2[1][1].get("file") == "1"


def test_reply_quote_renders_text_and_images_in_order():
    adapter = _capture(_make_adapter())
    # Distinct cached path per image so order is observable.
    adapter._resolve_image = AsyncMock(side_effect=lambda d: f"/cache/{d.get('file')}")

    def _getmsg(action, params, **kw):
        if action == "get_msg":
            return {"status": "ok", "retcode": 0, "data": {
                "user_id": 333, "sender": {"nickname": "Bob", "card": ""},
                "message": [
                    {"type": "text", "data": {"text": "看这张图"}},
                    {"type": "image", "data": {"file": "a.jpg", "url": "http://e/a.jpg"}},
                    {"type": "text", "data": {"text": "然后这张"}},
                    {"type": "image", "data": {"file": "b.jpg", "url": "http://e/b.jpg"}},
                ],
            }}
        return {"status": "ok", "retcode": 0, "data": {}}

    adapter._call_action = AsyncMock(side_effect=_getmsg)
    _run(adapter._handle_inbound_message(_quoted_payload("q1", "这啥")))
    event = adapter.handle_message.call_args.args[0]
    assert event.reply_to_message_id == "999"
    # Quote is now a 【】 fence in channel_context (reply_to_text unset so the
    # gateway doesn't double-wrap it as [Replying to:]).
    assert event.reply_to_text is None
    assert event.channel_context is not None
    assert "【用户回复了这条消息" in event.channel_context
    assert "Bob (QQ 333)" in event.channel_context          # sender = 昵称 + qq
    # Text and image markers interleave in the ORIGINAL order — not flattened,
    # and with no added spacing (faithful to the source).
    assert "看这张图[输入图片1]然后这张[输入图片2]" in event.channel_context
    assert event.channel_context.rstrip().endswith("【引用消息结束】")
    # Images land in media_urls in the same order as their [输入图片N] markers.
    assert event.media_urls == ["/cache/a.jpg", "/cache/b.jpg"]
    assert event.media_types == ["image/jpeg", "image/jpeg"]


def test_image_markers_globally_renumbered_across_own_and_quote():
    # The trigger carries its OWN image (position 1, labeled in the body) AND
    # reply-quotes a message with one image. The quote marker must be
    # [输入图片2], not [输入图片1] — contiguous namespace, not per-message.
    adapter = _capture(_make_adapter())
    adapter._resolve_image = AsyncMock(side_effect=lambda d: f"/cache/{d.get('file')}")

    def _getmsg(action, params, **kw):
        if action == "get_msg":
            return {"status": "ok", "retcode": 0, "data": {
                "user_id": 333, "sender": {"nickname": "Bob"},
                "message": [{"type": "image", "data": {"file": "q.jpg", "url": "http://e/q.jpg"}}],
            }}
        return {"status": "ok", "retcode": 0, "data": {}}

    adapter._call_action = AsyncMock(side_effect=_getmsg)
    payload = {
        "post_type": "message", "message_type": "group", "group_id": 5,
        "user_id": 222, "message_id": "gr", "sender": {"nickname": "Alice"},
        "message": [
            {"type": "reply", "data": {"id": "999"}},
            {"type": "at", "data": {"qq": "111"}},
            {"type": "image", "data": {"file": "own.jpg", "url": "http://e/own.jpg"}},
            {"type": "text", "data": {"text": "对比下"}},
        ],
    }
    _run(adapter._handle_inbound_message(payload))
    event = adapter.handle_message.call_args.args[0]
    # Own image is attachment position 1 (labeled in the trigger body); the
    # quoted image is position 2 (labeled in the 【】 fence in channel_context).
    assert event.media_urls == ["/cache/own.jpg", "/cache/q.jpg"]
    assert "[输入图片1]" in event.text               # own image labeled in body
    ctx = event.channel_context or ""
    assert "[输入图片2]" in ctx                       # quote marker = pos 2 (after own)
    assert "[[IMG]]" not in ctx                       # placeholder fully renumbered


def test_reply_quote_text_only():
    adapter = _capture(_make_adapter())

    def _getmsg(action, params, **kw):
        if action == "get_msg":
            return {"status": "ok", "retcode": 0, "data": {
                "user_id": 333, "sender": {"card": "老板"},
                "message": [{"type": "text", "data": {"text": "明天放假"}}],
            }}
        return {"status": "ok", "retcode": 0, "data": {}}

    adapter._call_action = AsyncMock(side_effect=_getmsg)
    _run(adapter._handle_inbound_message(_quoted_payload("q2", "真的吗")))
    event = adapter.handle_message.call_args.args[0]
    # Quote content is fenced in 【】 markers in channel_context (not a directive).
    ctx = event.channel_context or ""
    assert "【用户回复了这条消息" in ctx
    assert "老板 (QQ 333): 明天放假" in ctx
    assert ctx.rstrip().endswith("【引用消息结束】")
    assert event.reply_to_text is None
    assert event.media_urls == []


def test_reply_quote_file_is_downloaded_with_path():
    # The quote carries a file. Quoted segments come from a FRESH get_msg at
    # trigger time, so the file URL is live — download it and surface the
    # cached path inline so the agent can read the file the user replied to.
    adapter = _capture(_make_adapter())
    adapter._resolve_file = AsyncMock(return_value="/cache/documents/doc_x_报告.pdf")

    def _getmsg(action, params, **kw):
        if action == "get_msg":
            return {"status": "ok", "retcode": 0, "data": {
                "user_id": 333, "sender": {"nickname": "Bob"},
                "message": [
                    {"type": "text", "data": {"text": "看下这个"}},
                    {"type": "file", "data": {"file": "abc.hash", "name": "报告.pdf", "url": "http://e/f"}},
                ],
            }}
        return {"status": "ok", "retcode": 0, "data": {}}

    adapter._call_action = AsyncMock(side_effect=_getmsg)
    _run(adapter._handle_inbound_message(_quoted_payload("qf", "帮我总结")))
    event = adapter.handle_message.call_args.args[0]
    ctx = event.channel_context or ""
    # _resolve_file was called with the quoted file segment (downloaded now).
    adapter._resolve_file.assert_awaited_once()
    seg = adapter._resolve_file.await_args.args[0]
    assert seg.get("name") == "报告.pdf"
    # Marker carries the cached path inline in the quote fence.
    assert "看下这个[文件:报告.pdf → /cache/documents/doc_x_报告.pdf]" in ctx
    # A quoted FILE is referenced by path, not attached as an image.
    assert event.media_urls == []


# ── group files via get_group_file_url ───────────────────────────────────
# A QQ group-file segment is elementType 3, which LLOneBot's get_file REJECTS
# ("不支持的文件类型: 3"). The adapter must instead call get_group_file_url with
# (group_id, file_id) to get a real download URL. DM files still use get_file.


def _group_file_payload(mid, text, at_self=True):
    segs = []
    if at_self:
        segs.append({"type": "at", "data": {"qq": "111"}})
    segs.append({"type": "text", "data": {"text": text}})
    segs.append({"type": "file", "data": {
        "file": "报告.pdf", "url": "", "file_id": "/abc-def", "file_size": "100",
    }})
    return {
        "post_type": "message", "message_type": "group", "group_id": 5,
        "user_id": 222, "message_id": mid, "sender": {"nickname": "Alice"},
        "message": segs,
    }


def _real_file_adapter():
    """_capture mocks _resolve_file away; these tests exercise the REAL one."""
    adapter = _capture(_make_adapter())
    adapter._resolve_file = type(adapter)._resolve_file.__get__(adapter, type(adapter))
    return adapter


def test_own_group_file_uses_get_group_file_url():
    # Direct group message with a file + @bot. Must resolve via get_group_file_url
    # (NOT get_file) and surface the cached path in the body.
    adapter = _real_file_adapter()
    adapter._download_bytes = AsyncMock(return_value=b"%PDF-1.4 data")
    calls = []

    def _action(action, params, **kw):
        calls.append(action)
        if action == "get_group_file_url":
            return {"status": "ok", "retcode": 0, "data": {"url": "http://e/file"}}
        return {"status": "ok", "retcode": 0, "data": {}}

    adapter._call_action = AsyncMock(side_effect=_action)
    _run(adapter._handle_inbound_message(_group_file_payload("gf1", "看下")))
    event = adapter.handle_message.call_args.args[0]
    # get_group_file_url used; get_file NOT used (group file).
    assert "get_group_file_url" in calls
    assert "get_file" not in calls
    # Cached path surfaced inline (real cache_document_from_bytes path). The
    # OWN-trigger file marker is `[file: <name> (<path>)]` (adapter.py:706).
    import re
    m = re.search(r"\[file: 报告\.pdf \(([^)]*cache/documents/[^)]*报告\.pdf)\)\]", event.text)
    assert m, f"no cached path in body: {event.text!r}"
    assert os.path.isfile(m.group(1))


def test_group_file_url_failure_falls_back_to_get_file():
    # get_group_file_url fails → fall back to the generic get_file path.
    adapter = _real_file_adapter()
    adapter._download_bytes = AsyncMock(return_value=b"bytes")
    calls = []

    def _action(action, params, **kw):
        calls.append(action)
        if action == "get_group_file_url":
            return {"status": "failed", "retcode": 1200, "wording": "不支持的文件类型: 3"}
        if action == "get_file":
            return {"status": "ok", "retcode": 0, "data": {"url": "http://e/fb"}}
        return {"status": "ok", "retcode": 0, "data": {}}

    adapter._call_action = AsyncMock(side_effect=_action)
    _run(adapter._handle_inbound_message(_group_file_payload("gf2", "看")))
    # Both attempted: group-url first (failed), then get_file fallback.
    assert "get_group_file_url" in calls and "get_file" in calls
    event = adapter.handle_message.call_args.args[0]
    assert "[file: 报告.pdf (" in event.text  # resolved via fallback → has path


def test_dm_file_does_not_use_get_group_file_url():
    # DM file: no group_id → get_group_file_url never called, get_file path used.
    adapter = _real_file_adapter()
    adapter._download_bytes = AsyncMock(return_value=b"bytes")
    calls = []

    def _action(action, params, **kw):
        calls.append(action)
        if action == "get_file":
            return {"status": "ok", "retcode": 0, "data": {"url": "http://e/dm"}}
        return {"status": "ok", "retcode": 0, "data": {}}

    adapter._call_action = AsyncMock(side_effect=_action)
    payload = {
        "post_type": "message", "message_type": "private", "user_id": 222,
        "message_id": "dm1", "sender": {"nickname": "Alice"},
        "message": [
            {"type": "text", "data": {"text": "给"}},
            {"type": "file", "data": {"file": "私.pdf", "file_id": "/x", "url": ""}},
        ],
    }
    _run(adapter._handle_inbound_message(payload))
    assert "get_group_file_url" not in calls
    assert "get_file" in calls


def test_quoted_group_file_resolves_with_path():
    # Reply-quote a GROUP file: resolve_files=True + group_id → get_group_file_url.
    adapter = _real_file_adapter()
    adapter._download_bytes = AsyncMock(return_value=b"%PDF-1.4 q")
    calls = []

    def _action(action, params, **kw):
        calls.append(action)
        if action == "get_msg":
            return {"status": "ok", "retcode": 0, "data": {
                "user_id": 333, "sender": {"nickname": "Bob"},
                "message": [
                    {"type": "text", "data": {"text": "看这个"}},
                    {"type": "file", "data": {"file": "题.pdf", "url": "", "file_id": "/q-1"}},
                ],
            }}
        if action == "get_group_file_url":
            return {"status": "ok", "retcode": 0, "data": {"url": "http://e/qf"}}
        return {"status": "ok", "retcode": 0, "data": {}}

    adapter._call_action = AsyncMock(side_effect=_action)
    _run(adapter._handle_inbound_message(_quoted_payload("gf3", "总结下")))
    assert "get_group_file_url" in calls
    ctx = adapter.handle_message.call_args.args[0].channel_context or ""
    import re
    assert re.search(r"看这个\[文件:题\.pdf → [^]]*cache/documents/[^]]*题\.pdf\]", ctx), ctx



def test_reply_quote_file_download_failure_falls_back_to_name():
    # If the quoted file can't be resolved, degrade to the bare name (no crash).
    adapter = _capture(_make_adapter())
    adapter._resolve_file = AsyncMock(return_value=None)

    def _getmsg(action, params, **kw):
        if action == "get_msg":
            return {"status": "ok", "retcode": 0, "data": {
                "user_id": 333, "sender": {"nickname": "Bob"},
                "message": [{"type": "file", "data": {"file": "x.hash", "name": "报告.pdf"}}],
            }}
        return {"status": "ok", "retcode": 0, "data": {}}

    adapter._call_action = AsyncMock(side_effect=_getmsg)
    _run(adapter._handle_inbound_message(_quoted_payload("qf2", "看")))
    ctx = adapter.handle_message.call_args.args[0].channel_context or ""
    assert "[文件:报告.pdf]" in ctx
    assert "→" not in ctx


def test_reply_quote_record_is_downloaded_with_path():
    # Same treatment for a quoted VOICE segment: fresh URL → download → path.
    adapter = _capture(_make_adapter())
    adapter._resolve_record = AsyncMock(return_value="/cache/audio/rec_abc.ogg")

    def _getmsg(action, params, **kw):
        if action == "get_msg":
            return {"status": "ok", "retcode": 0, "data": {
                "user_id": 333, "sender": {"nickname": "Bob"},
                "message": [
                    {"type": "text", "data": {"text": "听"}},
                    {"type": "record", "data": {"file": "r.hash", "url": "http://e/r"}},
                ],
            }}
        return {"status": "ok", "retcode": 0, "data": {}}

    adapter._call_action = AsyncMock(side_effect=_getmsg)
    _run(adapter._handle_inbound_message(_quoted_payload("qr", "说了啥")))
    ctx = adapter.handle_message.call_args.args[0].channel_context or ""
    adapter._resolve_record.assert_awaited_once()
    assert "听[语音: <音频已缓存，可用 read_file 读取> /cache/audio/rec_abc.ogg]" in ctx
    # A quoted record is referenced by path, not attached as audio.
    assert adapter.handle_message.call_args.args[0].media_urls == []


def test_observe_file_is_name_only_no_download():
    # Background files are NOT downloaded (can be large) — name only, no path.
    adapter = _capture(_make_adapter(observe_unmentioned=True, observe_allowed_chats=["5"]))
    adapter._resolve_image = AsyncMock(return_value=None)
    payload = {
        "post_type": "message", "message_type": "group", "group_id": 5,
        "user_id": 222, "message_id": "ob1", "sender": {"nickname": "Alice"},
        "message": [
            {"type": "text", "data": {"text": "发个文件"}},
            {"type": "file", "data": {"file": "big.hash", "name": "大文件.zip", "url": "http://e/big"}},
        ],
    }
    _run(adapter._observe("group:5", "Alice", "222", payload["message"], 1234567890))
    line, imgs = adapter._observed["group:5"][0]
    # Name rendered, but the file was never resolved/downloaded.
    assert "[文件:大文件.zip]" in line
    assert "→" not in line
    adapter._resolve_file.assert_not_awaited()


def test_reply_quote_at_includes_qq():
    adapter = _capture(_make_adapter())

    def _getmsg(action, params, **kw):
        if action == "get_msg":
            return {"status": "ok", "retcode": 0, "data": {
                "user_id": 333, "sender": {"nickname": "Bob"},
                "message": [
                    {"type": "text", "data": {"text": "回复"}},
                    {"type": "at", "data": {"qq": "88888888", "name": "张三"}},
                    {"type": "text", "data": {"text": "一下"}},
                ],
            }}
        return {"status": "ok", "retcode": 0, "data": {}}

    adapter._call_action = AsyncMock(side_effect=_getmsg)
    _run(adapter._handle_inbound_message(_quoted_payload("q5", "嗯")))
    event = adapter.handle_message.call_args.args[0]
    # @-ed person carries their qq so the agent can @ them back. The quote is
    # fenced in channel_context now.
    ctx = event.channel_context or ""
    assert "Bob (QQ 333)" in ctx
    assert "@张三(QQ 88888888)" in ctx


def test_reply_quote_get_msg_failure_is_graceful():
    adapter = _capture(_make_adapter())
    adapter._call_action = AsyncMock(side_effect=RuntimeError("boom"))
    _run(adapter._handle_inbound_message(_quoted_payload("q3", "看看")))
    event = adapter.handle_message.call_args.args[0]
    assert event.reply_to_message_id == "999"   # id still recorded
    assert event.reply_to_text is None          # never set (quote lives in channel_context)
    # get_msg failed → no quote fence surfaced.
    assert "用户回复了这条消息" not in (event.channel_context or "")
    assert event.media_urls == []


def test_reply_quote_get_msg_nonok_is_graceful():
    adapter = _capture(_make_adapter())

    def _getmsg(action, params, **kw):
        if action == "get_msg":
            return {"status": "failed", "retcode": 1, "wording": "msg not found"}
        return {"status": "ok", "retcode": 0, "data": {}}

    adapter._call_action = AsyncMock(side_effect=_getmsg)
    _run(adapter._handle_inbound_message(_quoted_payload("q4", "看看")))
    event = adapter.handle_message.call_args.args[0]
    assert event.reply_to_text is None


def test_channel_prompt_injects_current_chat_id_for_targeting():
    # channel_prompt tells the agent its reply goes to THIS chat (chat_id) and
    # how to attach media (MEDIA:<path>) — send_message is NOT an agent tool.
    adapter = _capture(_make_adapter())
    _run(adapter._handle_inbound_message(_group_msg("cp1", "hi", at_self=True)))
    event = adapter.handle_message.call_args.args[0]
    assert event.channel_prompt is not None
    assert "group:5" in event.channel_prompt         # chat_id
    assert "MEDIA:" in event.channel_prompt           # media-attach pointer
    assert "send_message" not in event.channel_prompt  # not an agent tool here
    # No per-speaker data — channel_prompt is stable across turns/speakers.
    assert "Alice" not in event.channel_prompt
    assert "QQ 222" not in event.channel_prompt


def test_channel_prompt_for_dm_includes_private_chat_id():
    adapter = _capture(_make_adapter())
    payload = {
        "post_type": "message", "message_type": "private", "user_id": 7,
        "message_id": "cp2", "sender": {"nickname": "X"},
        "message": [{"type": "text", "data": {"text": "hi"}}],
    }
    _run(adapter._handle_inbound_message(payload))
    event = adapter.handle_message.call_args.args[0]
    assert "private:7" in event.channel_prompt
    assert "MEDIA:" in event.channel_prompt


def test_channel_prompt_differs_for_group_vs_dm():
    # The per-turn channel_prompt carries a group/DM delta so the agent gets
    # correct behavior for each (e.g. @mention gating + 合并转发 only in groups).
    adapter = _capture(_make_adapter())
    _run(adapter._handle_inbound_message(_group_msg("g1", "hi", at_self=True)))
    group_cp = adapter.handle_message.call_args.args[0].channel_prompt
    _run(adapter._handle_inbound_message({
        "post_type": "message", "message_type": "private", "user_id": 9,
        "message_id": "d1", "sender": {"nickname": "Y"},
        "message": [{"type": "text", "data": {"text": "hi"}}],
    }))
    dm_cp = adapter.handle_message.call_args.args[0].channel_prompt
    assert "[GROUP]" in group_cp and "[DM]" in dm_cp
    assert group_cp != dm_cp


def test_channel_prompt_stable_across_speakers():
    # channel_prompt must not depend on the speaker — it's stable per chat so it
    # doesn't churn every turn (and the speaker is already named in the message).
    adapter = _capture(_make_adapter())
    _run(adapter._handle_inbound_message(_group_msg("s1", "hi", at_self=True)))
    cp1 = adapter.handle_message.call_args.args[0].channel_prompt
    _run(adapter._handle_inbound_message({
        "post_type": "message", "message_type": "group", "group_id": 5,
        "user_id": 999, "message_id": "s2", "sender": {"nickname": "Other"},
        "message": [{"type": "at", "data": {"qq": "111"}},
                    {"type": "text", "data": {"text": "yo"}}],
    }))
    cp2 = adapter.handle_message.call_args.args[0].channel_prompt
    assert cp1 == cp2  # identical despite different speakers


# ── Wake-word trigger (regex, no @mention needed) ───────────────────────


def test_wake_word_default_triggers_without_mention():
    # Default wake_words = Arona,阿罗娜. Group msg (no @) with "Arona" triggers.
    adapter = _capture(_make_adapter())  # require_mention default True
    _run(adapter._handle_inbound_message(_group_msg("ww1", "Arona 帮我看看", at_self=False)))
    adapter.handle_message.assert_awaited_once()
    event = adapter.handle_message.call_args.args[0]
    assert "[Alice (QQ 222) 提到了你]" in event.text


def test_wake_word_chinese_default_triggers():
    adapter = _capture(_make_adapter())
    _run(adapter._handle_inbound_message(_group_msg("ww2", "阿罗娜 你在吗", at_self=False)))
    adapter.handle_message.assert_awaited_once()
    event = adapter.handle_message.call_args.args[0]
    assert "[Alice (QQ 222) 提到了你]" in event.text


def test_wake_word_case_insensitive():
    adapter = _capture(_make_adapter())
    _run(adapter._handle_inbound_message(_group_msg("ww3", "arona hi", at_self=False)))
    adapter.handle_message.assert_awaited_once()


def test_wake_word_no_match_drops_when_observe_off():
    # No wake-word, no @, observe off → dropped (not dispatched).
    adapter = _capture(_make_adapter())
    _run(adapter._handle_inbound_message(_group_msg("ww4", "今天天气不错", at_self=False)))
    adapter.handle_message.assert_not_called()


def test_wake_word_custom_regex():
    adapter = _capture(_make_adapter(wake_words="help,求助"))
    _run(adapter._handle_inbound_message(_group_msg("ww5", "求助啊", at_self=False)))
    adapter.handle_message.assert_awaited_once()
    event = adapter.handle_message.call_args.args[0]
    assert "[Alice (QQ 222) 提到了你]" in event.text
    # Non-matching message is dropped.
    _run(adapter._handle_inbound_message(_group_msg("ww6", "随便聊聊", at_self=False)))
    assert adapter.handle_message.await_count == 1


# ── outbound send ───────────────────────────────────────────────────────


def test_send_group_routes_send_group_msg():
    adapter = _connected(_make_adapter())
    result = _run(adapter.send("group:123", "hello"))
    assert result.success and result.message_id == "42"
    action, params = adapter._call_action.call_args.args
    assert action == "send_group_msg"
    assert params["group_id"] == 123
    assert params["message"] == [{"type": "text", "data": {"text": "hello"}}]


def test_send_private_routes_send_private_msg():
    adapter = _connected(_make_adapter())
    _run(adapter.send("private:9", "hi"))
    action, params = adapter._call_action.call_args.args
    assert action == "send_private_msg"
    assert params["user_id"] == 9


# ── outbound [CQ:at] → real at segments ──────────────────────────────────


def test_outbound_cq_at_becomes_at_segment():
    # [CQ:at,qq=N] in the outbound text must become a structured at segment
    # (a real QQ @), not a literal string in the text.
    adapter = _connected(_make_adapter())
    _run(adapter.send("group:123", "你好 [CQ:at,qq=3883393282] 在吗"))
    _, params = adapter._call_action.call_args.args
    segs = params["message"]
    assert {"type": "at", "data": {"qq": "3883393282"}} in segs
    texts = "".join(s["data"]["text"] for s in segs if s["type"] == "text")
    assert "[CQ:at" not in texts                     # marker consumed, not literal
    assert "你好" in texts and "在吗" in texts       # surrounding text preserved


def test_outbound_cq_at_multiple_and_at_all():
    # Several @s in one message each become their own at segment; @all works.
    segs = onebot.parse_cq_outbound("[CQ:at,qq=1] 和 [CQ:at,qq=2] 以及 [CQ:at,qq=all]")
    ats = [s["data"]["qq"] for s in segs if s["type"] == "at"]
    assert ats == ["1", "2", "all"]


def test_outbound_cq_at_tolerates_spacing_and_case():
    segs = onebot.parse_cq_outbound("hi[CQ:at, qq=42]x")
    assert {"type": "at", "data": {"qq": "42"}} in segs


def test_outbound_non_at_cq_codes_stay_literal():
    # Non-at [CQ:...] an agent emits is NOT parsed (it can't control media);
    # it stays as literal text rather than becoming a real segment.
    segs = onebot.parse_cq_outbound("看这 [CQ:image,file=x]")
    assert all(s["type"] == "text" for s in segs)
    assert "[CQ:image" in "".join(s["data"]["text"] for s in segs)


def test_outbound_cq_at_in_forward_node():
    # A long group reply (>forward_limit) goes through send_group_forward_msg;
    # the [CQ:at] must survive chunking and become an at segment in a node.
    adapter = _connected(_make_adapter(forward_limit=50))
    adapter._self_id = "111"  # forward branch requires a bot uin (_connected leaves it '')
    long_text = (
        "这段话非常非常非常非常的长，长到超过了五十个字的限制呢。"
        "[CQ:at,qq=7] 这一段也写得特别特别特别特别特别特别特别特别长。"
    )
    result = _run(adapter.send("group:123", long_text))
    assert result.success
    action, params = adapter._call_action.call_args.args
    assert action == "send_group_forward_msg"
    node_segs = [seg for node in params["messages"] for seg in node["data"]["content"]]
    assert any(s["type"] == "at" and s["data"]["qq"] == "7" for s in node_segs)


def test_status_routed_to_status_channel_when_set():
    # Operational status (warn/info/progress) is redirected to status_channel
    # (here a private DM) instead of the originating group, prefixed with the
    # source chat. Real replies are unaffected (they go through send()).
    adapter = _connected(_make_adapter(status_channel="private:3883393282"))
    res = _run(adapter.send_or_update_status(
        "group:227488202", "warn", "⚠ Compression summary failed: empty"
    ))
    assert res.success and res.message_id == ""  # no msg_id → not auto-cleaned
    action, params = adapter._call_action.call_args.args
    assert action == "send_private_msg"
    assert params["user_id"] == 3883393282
    text = params["message"][0]["data"]["text"]
    assert "[运维告警·group:227488202]" in text
    assert "⚠ Compression summary failed: empty" in text


def test_status_routed_to_group_channel_form():
    # status_channel accepts the group:<id> form too.
    adapter = _connected(_make_adapter(status_channel="group:999"))
    _run(adapter.send_or_update_status("private:5", "warn", "boom"))
    action, params = adapter._call_action.call_args.args
    assert action == "send_group_msg"
    assert params["group_id"] == 999


def test_status_suppressed_when_no_status_channel():
    # Unset status_channel → suppress (no send to the originating chat).
    adapter = _connected(_make_adapter())  # no status_channel
    res = _run(adapter.send_or_update_status("group:5", "warn", "oops"))
    assert res.success and res.message_id == ""
    adapter._call_action.assert_not_called()


def test_status_suppressed_when_status_channel_malformed():
    adapter = _connected(_make_adapter(status_channel="nonsense"))
    res = _run(adapter.send_or_update_status("group:5", "warn", "oops"))
    assert res.success and res.message_id == ""
    adapter._call_action.assert_not_called()


def test_send_reply_segment_is_first():
    adapter = _connected(_make_adapter())
    _run(adapter.send("group:1", "hi", reply_to="77"))
    _, params = adapter._call_action.call_args.args
    assert params["message"][0] == {"type": "reply", "data": {"id": "77"}}
    assert params["message"][1] == {"type": "text", "data": {"text": "hi"}}


def test_send_chunks_long_message():
    adapter = _connected(_make_adapter())
    _run(adapter.send("group:1", "a" * 5000))
    assert adapter._call_action.await_count == 2


# ── forward bundles (合并转发) ──────────────────────────────────────────


def test_split_sentences_chinese_periods():
    text = "一二三四五六七八九。" * 3            # 30 chars, 3 sentences
    chunks = onebot.split_text_by_sentences(text, limit=25)
    assert len(chunks) >= 2
    assert all(len(c) <= 25 for c in chunks)
    assert chunks[0].endswith("。")             # greedy cut lands on a period
    assert "".join(chunks) == text              # nothing dropped/mangled


def test_split_sentences_decimal_not_a_boundary():
    # The "." in "3.14" is followed by a digit → must NOT split there.
    text = "Value is 3.14 exactly. Then more text here. " * 10
    chunks = onebot.split_text_by_sentences(text, limit=45)
    assert all(len(c) <= 45 for c in chunks)
    assert not any(c.endswith("3.") for c in chunks)
    assert any("3.14" in c for c in chunks)     # decimal kept intact


def test_split_sentences_no_punctuation_hard_breaks():
    text = "啊" * 300                           # no period/newline/space
    chunks = onebot.split_text_by_sentences(text, limit=80)
    assert all(len(c) <= 80 for c in chunks)
    assert len(chunks) >= 3
    assert "".join(chunks) == text


def test_split_sentences_exact_fit_returns_single():
    assert onebot.split_text_by_sentences("short", limit=800) == ["short"]
    assert onebot.split_text_by_sentences("x" * 800, limit=800) == ["x" * 800]


def test_send_group_long_uses_forward():
    adapter = _connected(_make_adapter())
    adapter._self_id = "111"
    long_text = "这是一段话。 " * 250            # ~1250 chars, many sentences
    result = _run(adapter.send("group:123", long_text))
    assert result.success and result.message_id == "42"
    action, params = adapter._call_action.call_args.args
    assert action == "send_group_forward_msg"
    assert params["group_id"] == 123
    nodes = params["messages"]
    assert all(n["type"] == "node" for n in nodes)
    assert len(nodes) >= 2                       # split into multiple nodes
    assert all(len(n["data"]["content"][0]["data"]["text"]) <= 800 for n in nodes)
    assert nodes[0]["data"]["uin"] == "111"
    assert nodes[0]["data"]["name"] == "Hermes"


def test_send_group_short_stays_normal():
    adapter = _connected(_make_adapter())
    adapter._self_id = "111"
    _run(adapter.send("group:1", "short reply"))
    assert adapter._call_action.call_args.args[0] == "send_group_msg"


def test_send_private_long_never_forwards():
    adapter = _connected(_make_adapter())
    adapter._self_id = "111"
    _run(adapter.send("private:9", "x" * 2000))
    action, params = adapter._call_action.call_args.args
    assert action == "send_private_msg"          # DMs never use forward
    assert params["message"][-1]["type"] == "text"


def test_send_forward_falls_back_on_error():
    adapter = _connected(_make_adapter())
    adapter._self_id = "111"
    adapter._call_action = AsyncMock(side_effect=[
        {"status": "failed", "retcode": 100, "wording": "forward unsupported"},
        {"status": "ok", "retcode": 0, "data": {"message_id": 42}},
    ])
    result = _run(adapter.send("group:1", "x" * 2000))
    assert result.success                        # delivered via fallback
    actions = [c.args[0] for c in adapter._call_action.call_args_list]
    assert actions[0] == "send_group_forward_msg"
    assert "send_group_msg" in actions


def test_forward_disabled_uses_normal_send():
    adapter = _connected(_make_adapter(forward_enabled=False))
    adapter._self_id = "111"
    _run(adapter.send("group:1", "x" * 2000))
    assert adapter._call_action.call_args.args[0] == "send_group_msg"


def test_forward_skipped_without_self_id():
    adapter = _connected(_make_adapter())        # _self_id stays ""
    _run(adapter.send("group:1", "x" * 2000))
    assert adapter._call_action.call_args.args[0] == "send_group_msg"


def test_send_not_connected_is_retryable():
    adapter = _make_adapter()  # _running stays False
    result = _run(adapter.send("group:1", "hi"))
    assert not result.success
    assert result.retryable is True


def test_send_no_reply_is_silently_dropped():
    # Agent outputs NO_REPLY → adapter returns success but sends nothing.
    adapter = _connected(_make_adapter())
    result = _run(adapter.send("group:1", "NO_REPLY"))
    assert result.success               # turn treated as handled
    assert result.message_id is None    # but nothing was sent
    adapter._call_action.assert_not_called()
    # Whitespace around NO_REPLY is tolerated.
    result2 = _run(adapter.send("group:1", "  NO_REPLY\n"))
    assert result2.success and result2.message_id is None
    assert adapter._call_action.await_count == 0


def test_send_action_error_surfaces_wording():
    adapter = _connected(_make_adapter())
    adapter._call_action = AsyncMock(
        return_value={"status": "failed", "retcode": 100, "wording": "被禁言"}
    )
    result = _run(adapter.send("group:1", "hi"))
    assert not result.success
    assert "被禁言" in (result.error or "")


def test_send_malformed_chat_id_fails():
    adapter = _connected(_make_adapter())
    result = _run(adapter.send("nonsense", "hi"))
    assert not result.success


def test_send_image_builds_image_segment():
    adapter = _connected(_make_adapter())
    _run(adapter.send_image("group:1", "http://e/i.png", "cap"))
    _, params = adapter._call_action.call_args.args
    assert params["message"][0] == {"type": "image", "data": {"file": "http://e/i.png"}}
    assert params["message"][1] == {"type": "text", "data": {"text": "cap"}}


def test_send_voice_builds_record_segment():
    adapter = _connected(_make_adapter())
    _run(adapter.send_voice("group:1", "/tmp/a.ogg"))
    _, params = adapter._call_action.call_args.args
    assert params["message"][0]["type"] == "record"
    assert params["message"][0]["data"]["file"].startswith("file://")


def test_send_document_builds_file_segment():
    adapter = _connected(_make_adapter())
    _run(adapter.send_document("group:1", "/tmp/d.pdf", "cap", file_name="d.pdf"))
    _, params = adapter._call_action.call_args.args
    assert params["message"][0]["type"] == "file"
    assert params["message"][0]["data"]["file"].startswith("file://")
    assert params["message"][0]["data"]["name"] == "d.pdf"


def test_get_chat_info_group_resolves_name():
    adapter = _connected(_make_adapter())
    adapter._call_action = AsyncMock(
        return_value={"status": "ok", "retcode": 0, "data": {"group_name": "MyGroup"}}
    )
    info = _run(adapter.get_chat_info("group:7"))
    assert info == {"name": "MyGroup", "type": "group", "chat_id": "group:7"}


def test_get_chat_info_private():
    adapter = _connected(_make_adapter())
    info = _run(adapter.get_chat_info("private:7"))
    assert info["type"] == "dm"


# ── standalone sender (out-of-process cron delivery) ────────────────────


def test_standalone_send_missing_config_errors(monkeypatch):
    monkeypatch.delenv("LLBOT_WS_URL", raising=False)
    from gateway.config import PlatformConfig

    result = _run(_mod._standalone_send(PlatformConfig(enabled=True, extra={}), "group:1", "hi"))
    assert "error" in result


def test_standalone_send_malformed_chat_id_errors(monkeypatch):
    monkeypatch.setenv("LLBOT_WS_URL", "ws://x:1")
    from gateway.config import PlatformConfig

    result = _run(_mod._standalone_send(PlatformConfig(enabled=True, extra={}), "bad", "hi"))
    assert "error" in result


# ── register() ──────────────────────────────────────────────────────────


def test_register_creates_well_formed_entry():
    captured = {}

    class Ctx:
        def register_platform(self, **kwargs):
            captured.update(kwargs)

    register(Ctx())
    assert captured["name"] == "llbot"
    assert captured["label"] == "LLBot"
    assert callable(captured["adapter_factory"])
    assert callable(captured["check_fn"])
    assert captured["cron_deliver_env_var"] == "LLBOT_HOME_CHANNEL"
    assert captured["allowed_users_env"] == "LLBOT_ALLOWED_USERS"
    assert captured["allow_all_env"] == "LLBOT_ALLOW_ALL_USERS"
    assert captured["max_message_length"] == 4000
    assert callable(captured["standalone_sender_fn"])
    assert callable(captured["env_enablement_fn"])
    assert callable(captured.get("setup_fn"))
    assert "OneBot v11" in captured["platform_hint"]


# ── Mode B: observe unaddressed group chatter ───────────────────────────


def _observe_adapter(**over):
    extra = {
        "observe_unmentioned": True,
        "observe_allowed_chats": {"group:5"},
        "observe_max_messages": 50,
        # Default off in tests: the background describe is fire-and-forget
        # (asyncio.create_task), which doesn't survive asyncio.run's per-call
        # loop. Tests that exercise captioning enable it explicitly and gather
        # the tasks within one loop run (see test_observe_image_describes_*).
        "observe_describe_images": False,
    }
    extra.update(over)
    return _capture(_make_adapter(**extra))


def test_observe_disabled_drops_unaddressed():
    # Default (observe off): unaddressed group msg is dropped, nothing stored.
    adapter = _capture(_make_adapter())
    _run(adapter._handle_inbound_message(_group_msg("o1", "hi", at_self=False)))
    adapter.handle_message.assert_not_called()
    assert adapter._observed == {}


def test_observe_enabled_stores_unaddressed():
    adapter = _observe_adapter()
    _run(adapter._handle_inbound_message(_group_msg("o2", "闲聊", at_self=False)))
    adapter.handle_message.assert_not_called()  # stored, not dispatched
    assert list(adapter._observed["group:5"]) == [("[Alice (QQ 222)] 闲聊", [])]


def test_observe_skips_chats_not_in_allowlist():
    adapter = _observe_adapter(observe_allowed_chats={"group:999"})
    _run(adapter._handle_inbound_message(_group_msg("o3", "hi", at_self=False)))  # group:5
    adapter.handle_message.assert_not_called()
    assert adapter._observed == {}  # group:5 not allowlisted -> not stored


def test_observe_rolling_window_caps():
    adapter = _observe_adapter(observe_max_messages=3)
    for i, txt in enumerate(["one", "two", "three", "four", "five"]):
        _run(adapter._handle_inbound_message(_group_msg(f"o{i}", txt, at_self=False)))
    buf = list(adapter._observed["group:5"])
    assert len(buf) == 3  # capped
    texts = [line for line, _ in buf]
    assert "[Alice (QQ 222)] three" in texts and "[Alice (QQ 222)] five" in texts
    assert "[Alice (QQ 222)] one" not in texts  # oldest dropped


def test_observe_drained_into_channel_context_on_trigger():
    adapter = _observe_adapter()
    _run(adapter._handle_inbound_message(_group_msg("p1", "你好啊", at_self=False)))
    _run(adapter._handle_inbound_message(_group_msg("p2", "在吗", at_self=False)))
    # A @bot trigger in the same chat drains the buffer into channel_context.
    _run(adapter._handle_inbound_message(_group_msg("p3", "帮我看下", at_self=True)))
    event = adapter.handle_message.call_args.args[0]
    assert event.channel_context is not None
    assert "[Alice (QQ 222)] 你好啊" in event.channel_context
    assert "[Alice (QQ 222)] 在吗" in event.channel_context
    # Buffer cleared after drain.
    assert not adapter._observed.get("group:5")


def test_observe_allowed_chats_accepts_bare_group_id():
    # Users naturally write bare group numbers (as group_allow_from does); the
    # match must tolerate that, not only the full "group:<id>" chat_id form.
    adapter = _capture(_make_adapter(
        observe_unmentioned=True,
        observe_allowed_chats={"5"},
        observe_max_messages=50,
    ))
    _run(adapter._handle_inbound_message(_group_msg("b1", "今天天气真好", at_self=False)))
    # Unaddressed chatter was observed despite the bare-id allowlist entry.
    assert adapter._observed.get("group:5")
    # And it drains into channel_context on the next @-trigger.
    _run(adapter._handle_inbound_message(_group_msg("b2", "帮我看下", at_self=True)))
    event = adapter.handle_message.call_args.args[0]
    assert event.channel_context is not None
    assert "今天天气真好" in event.channel_context


def test_observe_media_snippet():
    adapter = _observe_adapter()
    payload = {
        "post_type": "message", "message_type": "group", "group_id": 5,
        "user_id": 222, "message_id": "om", "sender": {"nickname": "Alice"},
        "message": [{"type": "image", "data": {"file": "x.png", "url": "http://e/i.png"}}],
    }
    _run(adapter._handle_inbound_message(payload))
    line, imgs = adapter._observed["group:5"][0]
    assert "[Alice (QQ 222)]" in line and "[图" in line  # [图] = unresolved
    assert imgs == []  # _resolve_image mock returns None → not cached


def test_observe_image_lazy_ref_and_legend_on_drain():
    # Observed images are eagerly cached at receive time but NOT natively
    # attached. At drain they render as a text marker [背景图N] (no pixels) with
    # a path legend the agent can vision_analyze on demand for full pixels.
    adapter = _observe_adapter()  # describe_images=False by default
    adapter._resolve_image = AsyncMock(return_value="/cache/obs.jpg")
    payload = {
        "post_type": "message", "message_type": "group", "group_id": 5,
        "user_id": 222, "message_id": "ai", "sender": {"nickname": "Alice"},
        "message": [
            {"type": "text", "data": {"text": "看这个"}},
            {"type": "image", "data": {"file": "o.jpg", "url": "http://e/o.jpg"}},
        ],
    }
    _run(adapter._handle_inbound_message(payload))
    # Eager: resolved + cached at observe time. Buffered line carries the
    # placeholder; the _ObsImg holds the cached path (caption None — describe off).
    assert adapter._resolve_image.await_count == 1
    line, imgs = adapter._observed["group:5"][0]
    assert "[[IMG]]" in line
    assert [i.path for i in imgs] == ["/cache/obs.jpg"]
    assert all(i.caption is None for i in imgs)
    # @bot trigger drains the buffer: marker is text (NOT attached), path in legend.
    _run(adapter._handle_inbound_message(_group_msg("ai2", "嗯", at_self=True)))
    event = adapter.handle_message.call_args.args[0]
    assert adapter._resolve_image.await_count == 1  # still 1 — no re-resolve at drain
    assert event.media_urls == []                    # NOT natively attached
    assert "image/jpeg" not in event.media_types
    ctx = event.channel_context or ""
    assert "[背景图1]" in ctx                  # text marker, no caption
    assert "背景图1: /cache/obs.jpg" in ctx    # path legend
    assert "[[IMG]]" not in ctx                # placeholder fully rendered


def test_observe_image_renders_all_markers_no_cap():
    # No cap: every observed image gets a [背景图N] marker + legend entry,
    # none are natively attached, none are dropped as [图(未附)].
    adapter = _observe_adapter()
    adapter._resolve_image = AsyncMock(side_effect=lambda d: f"/cache/{d.get('file')}")
    for i in range(6):
        payload = {
            "post_type": "message", "message_type": "group", "group_id": 5,
            "user_id": 222, "message_id": f"c{i}", "sender": {"nickname": "Alice"},
            "message": [{"type": "image", "data": {"file": f"img{i}.jpg", "url": "http://e/i.jpg"}}],
        }
        _run(adapter._handle_inbound_message(payload))
    _run(adapter._handle_inbound_message(_group_msg("cT", "看", at_self=True)))
    event = adapter.handle_message.call_args.args[0]
    assert event.media_urls == []  # none attached
    ctx = event.channel_context or ""
    for i in range(6):
        assert f"[背景图{i + 1}]" in ctx
        assert f"背景图{i + 1}: /cache/img{i}.jpg" in ctx
    assert "[图(未附)]" not in ctx  # no cap → no dropped markers


def test_observe_image_describes_caption_on_drain():
    # With describe on, the background describe task fills caption; drain
    # renders [背景图N: <caption>] instead of the bare marker. The describe
    # task is fire-and-forget, so we gather it within the same loop run.
    adapter = _observe_adapter(observe_describe_images=True)
    adapter._resolve_image = AsyncMock(return_value="/cache/obs.jpg")
    adapter._describe_image_caption = AsyncMock(return_value="一只橘猫")
    payload = {
        "post_type": "message", "message_type": "group", "group_id": 5,
        "user_id": 222, "message_id": "dc", "sender": {"nickname": "Alice"},
        "message": [
            {"type": "text", "data": {"text": "看这个"}},
            {"type": "image", "data": {"file": "o.jpg", "url": "http://e/o.jpg"}},
        ],
    }

    async def _observe_and_describe():
        await adapter._handle_inbound_message(payload)
        if adapter._describe_tasks:
            await asyncio.gather(*adapter._describe_tasks, return_exceptions=True)

    _run(_observe_and_describe())
    assert adapter._describe_image_caption.await_count == 1
    _run(adapter._handle_inbound_message(_group_msg("dc2", "嗯", at_self=True)))
    event = adapter.handle_message.call_args.args[0]
    assert event.media_urls == []  # still not natively attached
    ctx = event.channel_context or ""
    assert "[背景图1: 一只橘猫]" in ctx
    assert "背景图1: /cache/obs.jpg" in ctx  # legend still present
    assert "[[IMG]]" not in ctx


def test_observe_describe_none_falls_back_to_marker():
    # If the describe completes but returns None (vision backend unavailable),
    # drain degrades to the bare [背景图N] marker — legend still carries the path.
    adapter = _observe_adapter(observe_describe_images=True)
    adapter._resolve_image = AsyncMock(return_value="/cache/obs.jpg")
    adapter._describe_image_caption = AsyncMock(return_value=None)
    payload = {
        "post_type": "message", "message_type": "group", "group_id": 5,
        "user_id": 222, "message_id": "dn", "sender": {"nickname": "Alice"},
        "message": [{"type": "image", "data": {"file": "o.jpg", "url": "http://e/o.jpg"}}],
    }

    async def _observe_and_describe():
        await adapter._handle_inbound_message(payload)
        if adapter._describe_tasks:
            await asyncio.gather(*adapter._describe_tasks, return_exceptions=True)

    _run(_observe_and_describe())
    _run(adapter._handle_inbound_message(_group_msg("dn2", "嗯", at_self=True)))
    event = adapter.handle_message.call_args.args[0]
    ctx = event.channel_context or ""
    assert "[背景图1]" in ctx
    assert "[背景图1:" not in ctx  # no caption
    assert "背景图1: /cache/obs.jpg" in ctx


def test_observe_describe_into_swallows_exception():
    # _describe_into must never raise — a failing describe leaves caption None
    # so drain degrades cleanly. Verified directly (no fire-and-forget loop).
    adapter = _observe_adapter()
    img = _mod._ObsImg(path="/cache/obs.jpg")
    adapter._describe_image_caption = AsyncMock(side_effect=RuntimeError("vision down"))
    _run(adapter._describe_into(img))  # must not raise
    assert img.caption is None


def test_observe_line_has_timestamp_and_header_anchors_trigger():
    adapter = _observe_adapter()
    # Observed message carries a timestamp → line is prefixed with MM-DD HH:MM:SS.
    _run(adapter._handle_inbound_message({
        "post_type": "message", "message_type": "group", "group_id": 5,
        "user_id": 222, "message_id": "ts1", "time": 1737000000,
        "sender": {"nickname": "Alice"},
        "message": [{"type": "text", "data": {"text": "hi"}}],
    }))
    line, _paths = adapter._observed["group:5"][0]
    assert line[0].isdigit() and " [Alice (QQ 222)] hi" in line  # date+time prefix
    # Trigger carries its own time → framing header + trailing [now:] marker.
    _run(adapter._handle_inbound_message({
        "post_type": "message", "message_type": "group", "group_id": 5,
        "user_id": 222, "message_id": "ts2", "time": 1737000030,
        "sender": {"nickname": "Alice"},
        "message": [{"type": "at", "data": {"qq": "111"}},
                    {"type": "text", "data": {"text": "看"}}],
    }))
    ctx = adapter.handle_message.call_args.args[0].channel_context or ""
    assert "并非对你的指令" in ctx       # framing: context, not commands
    assert "[now:" in ctx               # "now" anchor marks the trigger time
    # The background block is fenced so it can't blur into the trigger.
    assert "【背景消息开始" in ctx
    assert "【背景消息结束】" in ctx
    # [now:] is the trigger's time anchor → sits OUTSIDE the fence, after the
    # end marker (so it's adjacent to [New message]).
    assert ctx.index("【背景消息结束】") < ctx.index("[now:")


def test_trigger_now_marker_present_even_without_observe():
    # Even with no observed chatter, the trigger still gets a [now:] timestamp
    # marker so the agent has an explicit anchor for the current message.
    adapter = _capture(_make_adapter(
        observe_unmentioned=True, observe_allowed_chats={"group:5"},
    ))
    _run(adapter._handle_inbound_message({
        "post_type": "message", "message_type": "group", "group_id": 5,
        "user_id": 222, "message_id": "now1", "time": 1737000030,
        "sender": {"nickname": "Alice"},
        "message": [{"type": "at", "data": {"qq": "111"}},
                    {"type": "text", "data": {"text": "看"}}],
    }))
    ctx = adapter.handle_message.call_args.args[0].channel_context or ""
    assert "[now:" in ctx               # marker present despite empty observe
    assert "并非对你的指令" not in ctx   # no framing header when nothing observed
    assert "【背景消息开始" not in ctx   # no fence when nothing observed
    assert "【背景消息结束】" not in ctx


def test_observe_preserves_at_other_mention_in_context():
    # Alice @s another user (qq=999, not the bot's self_id=111). It's
    # unaddressed chatter -> observed, and the @other stays inline so the
    # agent sees "Alice tagged bob" when later addressed.
    adapter = _observe_adapter()
    _run(adapter._handle_inbound_message(
        _group_msg("ao1", "你看看这个", at_other=999)
    ))
    adapter.handle_message.assert_not_called()
    line, _segs = adapter._observed["group:5"][0]
    assert "[Alice (QQ 222)]" in line
    assert "@用户999" in line
    # Drained into channel_context on the next @bot trigger.
    _run(adapter._handle_inbound_message(_group_msg("ao2", "嗯", at_self=True)))
    event = adapter.handle_message.call_args.args[0]
    assert "@用户999" in (event.channel_context or "")


def test_observe_at_bot_is_dispatched_not_observed():
    # A message that @s the bot is dispatched, never buffered as observation.
    adapter = _observe_adapter()
    _run(adapter._handle_inbound_message(_group_msg("ab1", "hi", at_self=True)))
    adapter.handle_message.assert_awaited_once()
    assert adapter._observed == {}


def test_private_messages_are_never_observed():
    adapter = _observe_adapter(observe_allowed_chats={"private:1"})
    payload = {
        "post_type": "message", "message_type": "private", "user_id": 1,
        "message_id": "pm", "sender": {"nickname": "B"},
        "message": [{"type": "text", "data": {"text": "hi"}}],
    }
    _run(adapter._handle_inbound_message(payload))
    # Private has no require_mention gate -> always dispatched, never observed.
    adapter.handle_message.assert_awaited_once()
    assert adapter._observed == {}


def test_env_enablement_includes_observe(monkeypatch):
    monkeypatch.setenv("LLBOT_WS_URL", "ws://h:1")
    monkeypatch.setenv("LLBOT_OBSERVE_UNMENTIONED", "true")
    monkeypatch.setenv("LLBOT_OBSERVE_ALLOWED_CHATS", "group:1,group:2")
    monkeypatch.setenv("LLBOT_OBSERVE_MAX_MESSAGES", "30")
    seed = _mod._env_enablement()
    assert seed["observe_unmentioned"] is True
    assert seed["observe_allowed_chats"] == "group:1,group:2"
    assert seed["observe_max_messages"] == 30


# ── Docker / shared-volume media path translation ───────────────────────


def test_outbound_no_shared_media_uses_host_path():
    adapter = _make_adapter()  # no shared-media config -> same-host
    assert adapter._prepare_outbound_file("/tmp/x.png") == "file:///tmp/x.png"


def test_outbound_copies_file_into_shared_volume(tmp_path):
    host_dir = tmp_path / "shared"
    adapter = _make_adapter(
        shared_media_host_dir=str(host_dir), shared_media_container_dir="/openclaw_media"
    )
    src = tmp_path / "src.png"
    src.write_bytes(b"\x89PNG data")
    ref = adapter._prepare_outbound_file(str(src))
    assert ref.startswith("file:///openclaw_media/")  # container-side path
    staged = list(host_dir.iterdir())
    assert len(staged) == 1  # actually copied into the host shared dir
    assert staged[0].read_bytes() == b"\x89PNG data"


def test_outbound_file_already_in_volume_just_translates(tmp_path):
    host_dir = tmp_path / "shared"
    host_dir.mkdir()
    (host_dir / "existing.png").write_bytes(b"data")
    adapter = _make_adapter(
        shared_media_host_dir=str(host_dir), shared_media_container_dir="/openclaw_media"
    )
    ref = adapter._prepare_outbound_file(str(host_dir / "existing.png"))
    assert ref == "file:///openclaw_media/existing.png"
    assert len(list(host_dir.iterdir())) == 1  # no duplicate copy


def test_to_host_path_maps_container_to_host():
    adapter = _make_adapter(
        shared_media_host_dir="/home/bot/llbot/shared_media",
        shared_media_container_dir="/openclaw_media",
    )
    assert adapter._to_host_path("/openclaw_media/sub/x.png") == os.path.join(
        "/home/bot/llbot/shared_media", "sub/x.png"
    )
    assert adapter._to_host_path("/openclaw_media") == "/home/bot/llbot/shared_media"


def test_to_host_path_passthrough_without_config():
    adapter = _make_adapter()
    assert adapter._to_host_path("/openclaw_media/x.png") == "/openclaw_media/x.png"


def test_to_host_path_outside_mount_left_unchanged():
    adapter = _make_adapter(
        shared_media_host_dir="/host", shared_media_container_dir="/container"
    )
    assert adapter._to_host_path("/other/path.png") == "/other/path.png"


def test_send_document_outbound_uses_container_path(tmp_path):
    host_dir = tmp_path / "shared"
    adapter = _connected(_make_adapter(
        shared_media_host_dir=str(host_dir), shared_media_container_dir="/openclaw_media"
    ))
    src = tmp_path / "doc.pdf"
    src.write_bytes(b"%PDF-1.4 fake")
    _run(adapter.send_document("group:1", str(src), file_name="doc.pdf"))
    _, params = adapter._call_action.call_args.args
    seg = params["message"][0]
    assert seg["type"] == "file"
    assert seg["data"]["file"].startswith("file:///openclaw_media/")  # staged + translated
    assert seg["data"]["name"] == "doc.pdf"


def test_resolve_file_falls_back_to_mapped_host_path(tmp_path):
    # llbot returns a container-local path (no url/base64) via get_file.
    host_dir = tmp_path / "shared"
    host_dir.mkdir()
    (host_dir / "doc.pdf").write_bytes(b"%PDF-1.4 fake")
    adapter = _make_adapter(
        shared_media_host_dir=str(host_dir), shared_media_container_dir="/openclaw_media"
    )
    adapter._running = True
    adapter._call_action = AsyncMock(return_value={
        "status": "ok", "retcode": 0,
        "data": {"file": "/openclaw_media/doc.pdf", "file_name": "doc.pdf"},
    })
    path = _run(adapter._resolve_file({"file": "abc.hash", "name": "doc.pdf"}))
    assert path is not None
    assert os.path.isfile(path)  # cached from the host-mapped file


def test_env_enablement_includes_shared_media(monkeypatch):
    monkeypatch.setenv("LLBOT_WS_URL", "ws://h:1")
    monkeypatch.setenv("LLBOT_SHARED_MEDIA_HOST_DIR", "/home/bot/llbot/shared_media")
    monkeypatch.setenv("LLBOT_SHARED_MEDIA_CONTAINER_DIR", "/openclaw_media")
    seed = _mod._env_enablement()
    assert seed["shared_media_host_dir"] == "/home/bot/llbot/shared_media"
    assert seed["shared_media_container_dir"] == "/openclaw_media"


# ── Chat-level admission allowlists (group / DM) ─────────────────────────


def test_group_allowlist_admits_listed_group():
    adapter = _capture(_make_adapter(group_allow_from=["5", "9"]))
    _run(adapter._handle_inbound_message(_group_msg("ga1", "hi", at_self=True)))  # group:5
    adapter.handle_message.assert_awaited_once()


def test_group_allowlist_drops_unlisted_group():
    # group:5 is NOT in [9] -> dropped before the mention gate even runs.
    adapter = _capture(_make_adapter(group_allow_from=["9"]))
    _run(adapter._handle_inbound_message(_group_msg("ga2", "hi", at_self=True)))
    adapter.handle_message.assert_not_called()


def test_group_allowlist_empty_admits_all():
    adapter = _capture(_make_adapter())  # no group_allow_from -> unrestricted
    _run(adapter._handle_inbound_message(_group_msg("ga3", "hi", at_self=True)))
    adapter.handle_message.assert_awaited_once()


def test_dm_allowlist_drops_unlisted_user():
    adapter = _capture(_make_adapter(allow_from=["999"]))
    payload = {
        "post_type": "message", "message_type": "private", "user_id": 333,
        "message_id": "da1", "sender": {"nickname": "B"},
        "message": [{"type": "text", "data": {"text": "hi"}}],
    }
    _run(adapter._handle_inbound_message(payload))  # 333 not in [999]
    adapter.handle_message.assert_not_called()


def test_dm_allowlist_admits_listed_user():
    adapter = _capture(_make_adapter(allow_from=["333"]))
    payload = {
        "post_type": "message", "message_type": "private", "user_id": 333,
        "message_id": "da2", "sender": {"nickname": "B"},
        "message": [{"type": "text", "data": {"text": "hi"}}],
    }
    _run(adapter._handle_inbound_message(payload))
    adapter.handle_message.assert_awaited_once()


def test_group_allowlist_blocks_poke_too():
    adapter = _capture(_make_adapter(group_allow_from=["9"]))

    async def go():
        adapter._dispatch_event({
            "post_type": "notice", "notice_type": "notify", "sub_type": "poke",
            "self_id": 111, "user_id": 222, "group_id": 5,  # not allowlisted
            "sender": {"nickname": "Bob"},
        })
        await asyncio.sleep(0.05)

    _run(go())
    adapter.handle_message.assert_not_called()


def test_env_enablement_includes_chat_allowlists(monkeypatch):
    monkeypatch.setenv("LLBOT_WS_URL", "ws://h:1")
    monkeypatch.setenv("LLBOT_ALLOWED_GROUPS", "11,22")
    monkeypatch.setenv("LLBOT_ALLOWED_DMS", "333")
    seed = _mod._env_enablement()
    assert seed["group_allow_from"] == "11,22"
    assert seed["allow_from"] == "333"


# ── 合并转发 (forward) → JSON tree ───────────────────────────────────────
# get_forward_msg(id) → data.messages[] of {content:[segments], sender, time}.
# A node's content may contain a nested {"type":"forward","data":{"id":...}}.
# The adapter expands forward segments into a 【合并转发消息…】 fenced JSON tree.


def _forward_seg(fid):
    return {"type": "forward", "data": {"id": str(fid)}}


def _fwd_node(text_or_content, nick="Nick", uid=1001, ts=1785315460):
    content = (
        [{"type": "text", "data": {"text": text_or_content}}]
        if isinstance(text_or_content, str)
        else text_or_content
    )
    return {"content": content, "sender": {"nickname": nick, "user_id": uid}, "time": ts}


def _fwd_resp(nodes):
    return {"status": "ok", "retcode": 0, "data": {"messages": nodes}}


def _fwd_action(forward_map, **extra_actions):
    """_call_action side_effect: dispatch get_forward_msg by id (+ optional get_msg)."""
    def _action(action, params, **kw):
        if action == "get_forward_msg":
            fid = str((params or {}).get("id"))
            return forward_map.get(fid, {"status": "failed", "retcode": 1404})
        if action in extra_actions:
            return extra_actions[action]
        return {"status": "ok", "retcode": 0, "data": {}}
    return AsyncMock(side_effect=_action)


def test_forward_in_quote_renders_json_tree():
    adapter = _capture(_make_adapter())
    nodes = [
        _fwd_node("第一条消息", "Nick1", 1001, 1785315460),
        _fwd_node("第二条消息", "Nick2", 1002, 1785315520),
    ]
    adapter._call_action = _fwd_action(
        {"F1": _fwd_resp(nodes)},
        get_msg={"status": "ok", "retcode": 0, "data": {
            "user_id": 333, "sender": {"nickname": "Bob"},
            "message": [_forward_seg("F1")],
        }},
    )
    _run(adapter._handle_inbound_message(_quoted_payload("fw1", "看看这个")))
    event = adapter.handle_message.call_args.args[0]
    ctx = event.channel_context or ""
    assert "【合并转发消息 · 2条" in ctx
    assert "```json" in ctx
    assert "【合并转发结束】" in ctx
    assert '"sender": "Nick1 (QQ 1001)"' in ctx
    assert "第一条消息" in ctx and "第二条消息" in ctx
    assert event.reply_to_text is None


def test_forward_image_placeholder_renumbered_in_quote():
    adapter = _capture(_make_adapter())
    adapter._resolve_image = AsyncMock(return_value="/cache/f1.jpg")
    nodes = [_fwd_node([{"type": "text", "data": {"text": "看图 "}},
                        {"type": "image", "data": {"file": "x.jpg", "url": "http://e/x"}}])]
    adapter._call_action = _fwd_action(
        {"F1": _fwd_resp(nodes)},
        get_msg={"status": "ok", "retcode": 0, "data": {
            "user_id": 333, "sender": {"nickname": "Bob"}, "message": [_forward_seg("F1")]}},
    )
    _run(adapter._handle_inbound_message(_quoted_payload("fw2", "嗯")))
    event = adapter.handle_message.call_args.args[0]
    ctx = event.channel_context or ""
    # No own images → forward image is [输入图片1]; placeholder fully renumbered.
    assert "[输入图片1]" in ctx
    assert "[[IMG]]" not in ctx
    assert event.media_urls == ["/cache/f1.jpg"]


def test_forward_nested_two_levels():
    adapter = _capture(_make_adapter())
    inner = [_fwd_node("嵌套里的内容", "Inner", 2001)]
    outer = [
        _fwd_node("外层第一条", "Outer", 2002),
        _fwd_node([_forward_seg("F2")], "Outer", 2002),
    ]
    action = _fwd_action(
        {"F1": _fwd_resp(outer), "F2": _fwd_resp(inner)},
        get_msg={"status": "ok", "retcode": 0, "data": {
            "user_id": 333, "sender": {"nickname": "Bob"}, "message": [_forward_seg("F1")]}},
    )
    adapter._call_action = action
    _run(adapter._handle_inbound_message(_quoted_payload("fw3", "看")))
    ctx = adapter.handle_message.call_args.args[0].channel_context or ""
    assert '"forward"' in ctx
    assert "外层第一条" in ctx and "嵌套里的内容" in ctx
    # Both forwards fetched.
    fetched = {str(c.args[1].get("id")) for c in action.await_args_list
               if c.args[0] == "get_forward_msg"}
    assert {"F1", "F2"} <= fetched


def test_forward_fetch_failure_placeholder():
    adapter = _capture(_make_adapter())
    # get_forward_msg times out, but get_msg (the quote fetch) still succeeds so
    # the quote fence (and its forward placeholder) is actually rendered.
    def _action(action, params, **kw):
        if action == "get_forward_msg":
            raise asyncio.TimeoutError()
        if action == "get_msg":
            return {"status": "ok", "retcode": 0, "data": {
                "user_id": 333, "sender": {"nickname": "Bob"}, "message": [_forward_seg("F1")]}}
        return {"status": "ok", "retcode": 0, "data": {}}
    adapter._call_action = AsyncMock(side_effect=_action)
    adapter._forward_cache.clear()
    _run(adapter._handle_inbound_message(_quoted_payload("fw4", "看")))
    ctx = adapter.handle_message.call_args.args[0].channel_context or ""
    assert "【合并转发消息 · 无法加载" in ctx
    adapter.handle_message.assert_awaited_once()  # ingestion survived


def test_forward_node_budget_elision(monkeypatch):
    monkeypatch.setattr(_mod, "_FORWARD_MAX_NODES", 5)
    adapter = _capture(_make_adapter())
    nodes = [_fwd_node(f"消息{i}", "N", 1000 + i) for i in range(12)]
    adapter._call_action = _fwd_action(
        {"F1": _fwd_resp(nodes)},
        get_msg={"status": "ok", "retcode": 0, "data": {
            "user_id": 333, "sender": {"nickname": "Bob"}, "message": [_forward_seg("F1")]}},
    )
    _run(adapter._handle_inbound_message(_quoted_payload("fw5", "看")))
    ctx = adapter.handle_message.call_args.args[0].channel_context or ""
    assert "还有7条未显示" in ctx
    assert "消息4" in ctx and "消息11" not in ctx  # only first 5 real nodes


def test_forward_char_budget_truncates(monkeypatch):
    # Budget between one node's size and the total: node text truncates to
    # _FORWARD_MAX_NODE_CHARS first, then the global budget stops further nodes.
    monkeypatch.setattr(_mod, "_FORWARD_MAX_NODE_CHARS", 200)
    monkeypatch.setattr(_mod, "_FORWARD_MAX_TOTAL_CHARS", 450)
    adapter = _capture(_make_adapter())
    nodes = [_fwd_node("长" * 400, "N", 1001) for _ in range(6)]
    adapter._call_action = _fwd_action(
        {"F1": _fwd_resp(nodes)},
        get_msg={"status": "ok", "retcode": 0, "data": {
            "user_id": 333, "sender": {"nickname": "Bob"}, "message": [_forward_seg("F1")]}},
    )
    _run(adapter._handle_inbound_message(_quoted_payload("fw6", "看")))
    ctx = adapter.handle_message.call_args.args[0].channel_context or ""
    assert "转发内容过长，已截断" in ctx  # global budget kicked in
    # Fewer than all 6 nodes rendered despite 6 source nodes.
    assert ctx.count('"sender": "N (QQ 1001)"') < 6


def test_forward_cache_hit_avoids_refetch():
    adapter = _capture(_make_adapter())
    nodes = [_fwd_node("同一张转发", "N", 1001)]
    action = _fwd_action(
        {"F1": _fwd_resp(nodes)},
        get_msg={"status": "ok", "retcode": 0, "data": {
            "user_id": 333, "sender": {"nickname": "Bob"}, "message": [_forward_seg("F1")]}},
    )
    adapter._call_action = action
    # Two separate quoted triggers referencing the SAME forward id.
    _run(adapter._handle_inbound_message(_quoted_payload("fw7a", "看")))
    _run(adapter._handle_inbound_message(_quoted_payload("fw7b", "再看")))
    fetches = [c for c in action.await_args_list if c.args[0] == "get_forward_msg"]
    assert len(fetches) == 1  # cached


def test_forward_in_trigger_message():
    adapter = _capture(_make_adapter())
    adapter._resolve_image = AsyncMock(return_value="/cache/f.jpg")
    nodes = [_fwd_node([{"type": "text", "data": {"text": "转发文本 "}},
                        {"type": "image", "data": {"file": "y.jpg", "url": "http://e/y"}}])]
    adapter._call_action = _fwd_action({"F1": _fwd_resp(nodes)})
    payload = _group_msg("fw8", "", at_self=True)
    payload["message"] = [{"type": "at", "data": {"qq": "111"}}, _forward_seg("F1")]
    _run(adapter._handle_inbound_message(payload))
    event = adapter.handle_message.call_args.args[0]
    # Forward block lands in the trigger BODY; image attached + labeled.
    assert "【合并转发消息" in event.text
    assert "转发文本" in event.text
    assert "[输入图片1]" in event.text
    assert event.media_urls == ["/cache/f.jpg"]


def test_forward_in_observe_background():
    adapter = _observe_adapter()
    adapter._resolve_image = AsyncMock(return_value="/cache/ob.jpg")
    nodes = [_fwd_node([{"type": "text", "data": {"text": "背景转发 "}},
                        {"type": "image", "data": {"file": "z.jpg", "url": "http://e/z"}}])]
    adapter._call_action = _fwd_action({"F1": _fwd_resp(nodes)})
    payload = _group_msg("fw9", "", at_self=False)
    payload["message"] = [_forward_seg("F1")]
    _run(adapter._handle_inbound_message(payload))  # no @ → observed
    line, imgs = adapter._observed["group:5"][0]
    assert "【合并转发消息" in line and "背景转发" in line
    assert len(imgs) == 1 and imgs[0].path == "/cache/ob.jpg"  # captured, NOT attached


def test_forward_files_voice_name_only_in_background():
    adapter = _observe_adapter()
    adapter._resolve_file = AsyncMock(return_value="/should/not/be/called")
    adapter._resolve_record = AsyncMock(return_value="/should/not/be/called")
    nodes = [_fwd_node([
        {"type": "text", "data": {"text": "看附件 "}},
        {"type": "file", "data": {"file": "x.pdf", "name": "资料.pdf"}},
        {"type": "record", "data": {"file": "v.amr"}},
    ])]
    adapter._call_action = _fwd_action({"F1": _fwd_resp(nodes)})
    payload = _group_msg("fw10", "", at_self=False)
    payload["message"] = [_forward_seg("F1")]
    _run(adapter._handle_inbound_message(payload))
    line, _ = adapter._observed["group:5"][0]
    assert "[文件:资料.pdf]" in line and "[语音]" in line
    adapter._resolve_file.assert_not_awaited()
    adapter._resolve_record.assert_not_awaited()


def test_forward_files_downloaded_in_quote():
    adapter = _capture(_make_adapter())
    adapter._resolve_file = AsyncMock(return_value="/cache/documents/doc_q_题.pdf")
    nodes = [_fwd_node([{"type": "text", "data": {"text": "附件 "}},
                        {"type": "file", "data": {"file": "x.pdf", "name": "题.pdf"}}])]
    adapter._call_action = _fwd_action(
        {"F1": _fwd_resp(nodes)},
        get_msg={"status": "ok", "retcode": 0, "data": {
            "user_id": 333, "sender": {"nickname": "Bob"}, "message": [_forward_seg("F1")]}},
    )
    _run(adapter._handle_inbound_message(_quoted_payload("fw11", "读下")))
    ctx = adapter.handle_message.call_args.args[0].channel_context or ""
    adapter._resolve_file.assert_awaited_once()
    assert "[文件:题.pdf → /cache/documents/doc_q_题.pdf]" in ctx


def test_forward_max_depth_stub(monkeypatch):
    adapter = _capture(_make_adapter())
    # Chain F1→F2→F3→F4; depth cap 3 means F4 is never fetched.
    def nest(fid):
        return _fwd_resp([_fwd_node([_forward_seg(fid)], "N", 1001)])
    action = _fwd_action(
        {"F1": nest("F2"), "F2": nest("F3"), "F3": nest("F4"), "F4": _fwd_resp([_fwd_node("x")])},
        get_msg={"status": "ok", "retcode": 0, "data": {
            "user_id": 333, "sender": {"nickname": "Bob"}, "message": [_forward_seg("F1")]}},
    )
    adapter._call_action = action
    _run(adapter._handle_inbound_message(_quoted_payload("fw12", "看")))
    ctx = adapter.handle_message.call_args.args[0].channel_context or ""
    assert "max_depth" in ctx
    fetched = {str(c.args[1].get("id")) for c in action.await_args_list
               if c.args[0] == "get_forward_msg"}
    assert "F4" not in fetched
    assert len(fetched) == 3


def test_forward_cache_ttl_expires(monkeypatch):
    adapter = _capture(_make_adapter())
    nodes = [_fwd_node("x", "N", 1001)]
    action = _fwd_action({"F1": _fwd_resp(nodes)})
    adapter._call_action = action
    # First fetch populates the cache, then force the entry to look expired.
    _run(adapter._fetch_forward_messages("F1"))
    for ent in adapter._forward_cache.values():
        ent.fetched_at -= (_mod._FORWARD_CACHE_TTL + 10)
    _run(adapter._fetch_forward_messages("F1"))
    fetches = [c for c in action.await_args_list if c.args[0] == "get_forward_msg"]
    assert len(fetches) == 2  # refetched after TTL


def test_forward_malformed_nodes_skipped():
    adapter = _capture(_make_adapter())
    nodes = [
        {"content": "not-a-list", "time": 1785315460},   # no sender, str content
        {"sender": {}, "content": [{"type": "text", "data": {"text": "ok"}}]},  # empty sender
        "garbage-node",                                    # not a dict
    ]
    adapter._call_action = _fwd_action(
        {"F1": _fwd_resp(nodes)},
        get_msg={"status": "ok", "retcode": 0, "data": {
            "user_id": 333, "sender": {"nickname": "Bob"}, "message": [_forward_seg("F1")]}},
    )
    _run(adapter._handle_inbound_message(_quoted_payload("fw13", "看")))
    ctx = adapter.handle_message.call_args.args[0].channel_context or ""
    assert "未知" in ctx  # fallback sender
    assert "ok" in ctx
    adapter.handle_message.assert_awaited_once()  # no crash


def test_forward_mixed_text_and_nested_is_list():
    adapter = _capture(_make_adapter())
    nodes = [_fwd_node([
        {"type": "text", "data": {"text": "附带的话 "}},
        _forward_seg("F2"),
    ])]
    adapter._call_action = _fwd_action(
        {"F1": _fwd_resp(nodes), "F2": _fwd_resp([_fwd_node("内层", "In", 2001)])},
        get_msg={"status": "ok", "retcode": 0, "data": {
            "user_id": 333, "sender": {"nickname": "Bob"}, "message": [_forward_seg("F1")]}},
    )
    _run(adapter._handle_inbound_message(_quoted_payload("fw14", "看")))
    ctx = adapter.handle_message.call_args.args[0].channel_context or ""
    # Parse the JSON from the fence and assert content is a mixed list.
    import json as _json, re as _re
    m = _re.search(r"```json\n(\[.*?\])\n```", ctx, _re.DOTALL)
    assert m, ctx
    tree = _json.loads(m.group(1))
    content = tree[0]["content"]
    assert isinstance(content, list)
    assert any(isinstance(p, str) and "附带的话" in p for p in content)
    assert any(isinstance(p, dict) and "forward" in p for p in content)
