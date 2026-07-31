"""Regression tests: spaced paths, GIS extensions, cross-turn dedupe plumbing,
and code-block-safe streaming display strip.

Covers the follow-up wave after PR #72170:

* #24032 — GIS extensions (.kmz/.kml/.geojson/.gpx) are deliverable, and
  unknown-extension paths containing spaces extract via the
  validation-gated progressive right-trim (``_spaced_path_candidates``).
* #16434 half — ``strip_media_directives_for_display`` (streaming path) no
  longer strips MEDIA tags out of fenced code blocks / inline-code examples;
  protected spans are a mask-locator, matching ``extract_media``.
* #53586 — ``_collect_history_media_paths`` also collects tags from
  assistant messages, and the post-stream delivery path filters against it.
"""

import os

import pytest

from gateway.platforms.base import (
    BasePlatformAdapter,
    MEDIA_DELIVERY_EXTS,
)
from gateway.run import _collect_history_media_paths


class TestGisExtensions:
    def test_gis_extensions_in_delivery_set(self):
        for ext in (".kmz", ".kml", ".geojson", ".gpx"):
            assert ext in MEDIA_DELIVERY_EXTS

    def test_geojson_extracts(self, tmp_path):
        p = tmp_path / "route.geojson"
        p.write_text("{}")
        media, cleaned = BasePlatformAdapter.extract_media(f"MEDIA:{p}")
        assert [x for x, _ in media] == [str(p)]
        assert "MEDIA:" not in cleaned


class TestSpacedPaths:
    def test_spaced_known_ext_extracts(self, tmp_path):
        p = tmp_path / "map data.kmz"
        p.write_bytes(b"PK")
        media, _ = BasePlatformAdapter.extract_media(f"MEDIA:{p}")
        assert [x for x, _ in media] == [str(p)]

    def test_spaced_unknown_ext_extracts_when_file_exists(self, tmp_path):
        p = tmp_path / "my server.log"
        p.write_text("log line\n")
        media, cleaned = BasePlatformAdapter.extract_media(f"MEDIA:{p}")
        assert [os.path.realpath(x) for x, _ in media] == [os.path.realpath(str(p))]
        assert "MEDIA:" not in cleaned

    def test_spaced_path_followed_by_prose_keeps_prose(self, tmp_path):
        p = tmp_path / "my server.log"
        p.write_text("log line\n")
        media, cleaned = BasePlatformAdapter.extract_media(
            f"MEDIA:{p} is the log you asked for"
        )
        assert [os.path.realpath(x) for x, _ in media] == [os.path.realpath(str(p))]
        assert "is the log you asked for" in cleaned

    def test_spaced_nonexistent_stays_visible(self):
        text = "MEDIA:/data/not real file.xyz here"
        media, cleaned = BasePlatformAdapter.extract_media(text)
        assert media == []
        assert "MEDIA:/data/not real file.xyz" in cleaned

    def test_forward_extension_stops_at_next_media_tag(self, tmp_path):
        a = tmp_path / "Caddyfile"
        b = tmp_path / "Dockerfile"
        a.write_text("localhost\n")
        b.write_text("FROM alpine\n")
        media, cleaned = BasePlatformAdapter.extract_media(
            f"MEDIA:{a} MEDIA:{b}"
        )
        got = sorted(os.path.realpath(x) for x, _ in media)
        assert got == sorted(
            [os.path.realpath(str(a)), os.path.realpath(str(b))]
        )
        assert "MEDIA:" not in cleaned


class TestStreamingDisplayStripCodeBlocks:
    def test_fenced_code_example_preserved(self, tmp_path):
        p = tmp_path / "real.pdf"
        p.write_text("x")
        text = f"Example:\n```\nMEDIA:{p}\n```\ndone MEDIA:{p}"
        out = BasePlatformAdapter.strip_media_directives_for_display(text)
        # The example inside the fence survives verbatim; the real tag outside
        # is stripped.
        assert f"MEDIA:{p}" in out
        assert out.count(f"MEDIA:{p}") == 1
        assert "```" in out

    def test_inline_code_example_preserved(self):
        text = "Use `MEDIA:/nonexistent/example.csv` to attach files."
        out = BasePlatformAdapter.strip_media_directives_for_display(text)
        assert "`MEDIA:/nonexistent/example.csv`" in out

    def test_plain_tag_still_stripped(self, tmp_path):
        p = tmp_path / "real.csv"
        p.write_text("x")
        out = BasePlatformAdapter.strip_media_directives_for_display(
            f"Here you go MEDIA:{p}"
        )
        assert "MEDIA:" not in out


class TestHistoryMediaDedupe:
    def test_assistant_message_tags_collected(self):
        history = [
            {"role": "user", "content": "make a chart"},
            {"role": "assistant", "content": "Done! MEDIA:/tmp/chart.png"},
            {"role": "user", "content": "thanks"},
        ]
        paths = _collect_history_media_paths(history)
        assert "/tmp/chart.png" in paths

    def test_tool_message_tags_still_collected(self):
        history = [
            {"role": "tool", "content": "MEDIA:/tmp/out.pdf"},
        ]
        paths = _collect_history_media_paths(history)
        assert "/tmp/out.pdf" in paths

    def test_empty_history_empty_set(self):
        assert _collect_history_media_paths([]) == set()


class TestCurrentTurnOnlyDedupe:
    """`_history_media_paths_for_session(current_turn_only=True)` scopes dedup to
    the trailing assistant/tool run, so a cross-turn re-send is NOT swallowed."""

    class _FakeStore:
        def __init__(self, transcript):
            self._t = transcript

        def load_transcript(self, _sid):
            return self._t

    def _adapter(self, transcript):
        # Call the unbound method with a bare stand-in for `self` — the method
        # only reads `self._session_store`, so no real adapter is needed.
        fn = BasePlatformAdapter._history_media_paths_for_session
        stand_in = type("StandIn", (), {"_session_store": self._FakeStore(transcript)})()
        return lambda key, **kw: fn(stand_in, key, **kw)

    def test_current_turn_only_excludes_prior_turns(self):
        # The current response's OWN assistant entry is excluded (its MEDIA tags
        # are what we're about to send — they must NOT be deduped away). And a
        # path that appears ONLY in a prior turn is also excluded.
        transcript = [
            {"role": "user", "content": "draw"},
            {"role": "assistant", "content": "here MEDIA:/tmp/old.png"},
            {"role": "user", "content": "send it again"},
            {"role": "assistant", "content": "ok MEDIA:/tmp/old.png"},
        ]
        adapter = self._adapter(transcript)
        paths = adapter("k", current_turn_only=True)
        # old.png is ONLY in the current reply (excluded) → dedup set is empty.
        assert paths is None or "/tmp/old.png" not in (paths or set())
        # A path that appears ONLY in the prior turn is likewise excluded:
        transcript2 = [
            {"role": "user", "content": "draw"},
            {"role": "assistant", "content": "here MEDIA:/tmp/old.png"},
            {"role": "user", "content": "again"},
            {"role": "assistant", "content": "sure thing"},
        ]
        adapter2 = self._adapter(transcript2)
        paths2 = adapter2("k", current_turn_only=True)
        assert paths2 is None or "/tmp/old.png" not in (paths2 or set())

    def test_current_turn_collapses_repeat_within_one_reply(self):
        # A path tagged in an EARLIER assistant/tool row of the SAME turn (not
        # the final reply) IS deduped — so the delivery filter sends it once.
        transcript = [
            {"role": "user", "content": "draw"},
            {"role": "assistant", "content": "MEDIA:/tmp/x.png"},
            {"role": "tool", "content": "MEDIA:/tmp/x.png"},
            {"role": "assistant", "content": "done"},
        ]
        adapter = self._adapter(transcript)
        paths = adapter("k", current_turn_only=True)
        assert "/tmp/x.png" in paths

    def test_legacy_full_history_still_default(self):
        # current_turn_only=False keeps the old behavior: prior-turn tags are
        # collected (everything except the final assistant row).
        transcript = [
            {"role": "user", "content": "draw"},
            {"role": "assistant", "content": "here MEDIA:/tmp/old.png"},
            {"role": "user", "content": "again"},
            {"role": "assistant", "content": "sure"},
        ]
        adapter = self._adapter(transcript)
        paths = adapter("k")
        assert "/tmp/old.png" in paths

    def test_trailing_run_stops_at_user_boundary(self):
        # A tool row from an EARLIER turn must not bleed into the current turn:
        # the trailing run starts after the most recent user message.
        transcript = [
            {"role": "assistant", "content": "MEDIA:/tmp/very_old.png"},
            {"role": "user", "content": "next"},
            {"role": "assistant", "content": "no media here"},
        ]
        adapter = self._adapter(transcript)
        paths = adapter("k", current_turn_only=True)
        assert paths is None or "/tmp/very_old.png" not in (paths or set())
