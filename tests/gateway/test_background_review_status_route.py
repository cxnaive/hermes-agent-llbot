"""Background reviews preserve the adapter's operational-status routing."""
import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

from gateway.config import Platform
from gateway.run_turn_runner import TurnRunner


def test_review_uses_the_adapters_status_route_after_final_delivery():
    turn = object.__new__(TurnRunner)
    adapter = SimpleNamespace(send=AsyncMock(), send_or_update_status=AsyncMock())
    turn._ctx = SimpleNamespace(
        source=SimpleNamespace(platform=Platform.TELEGRAM),
        _status_adapter=adapter,
        _status_chat_id='originating-chat',
        _status_thread_metadata=None,
        _run_still_current=lambda: True,
    )
    turn._approval_owner = None
    turn._schedule = lambda coro, _message: asyncio.run(coro)
    send, release = turn._make_bg_review_callbacks()

    send('Memory updated')
    adapter.send_or_update_status.assert_not_awaited()
    release()

    adapter.send_or_update_status.assert_awaited_once()
    assert adapter.send_or_update_status.await_args.args == (
        'originating-chat', 'background_review', 'Memory updated')
    adapter.send.assert_not_awaited()
