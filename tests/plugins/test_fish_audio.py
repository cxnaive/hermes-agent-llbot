"""Exercise real plugin discovery, profile routing, HTTP and Hermes audio delivery."""
import io
import json
from pathlib import Path
import shutil
import threading
import wave
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest
import yaml


@pytest.fixture
def fish_server():
    audio = io.BytesIO()
    with wave.open(audio, 'wb') as stream:
        stream.setnchannels(1)
        stream.setsampwidth(2)
        stream.setframerate(24000)
        stream.writeframes(b'\0\0' * 4800)
    seen = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            data = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            seen.append((self.path, self.headers['Authorization'], self.headers['model'], data))
            if data['text'] == 'fail':
                self.send_response(401)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': self.headers['Authorization']}).encode())
                return
            self.send_response(200)
            self.send_header('Content-Type', 'audio/wav')
            self.end_headers()
            self.wfile.write(audio.getvalue())

        def log_message(self, *args):
            pass

    server = HTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f'http://127.0.0.1:{server.server_port}', seen
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()


def make_home(home, api_url, voice, model):
    source = Path(__file__).resolve().parents[2] / 'plugins' / 'fish-audio'
    shutil.copytree(source, home / 'plugins/fish-audio',
                    ignore=shutil.ignore_patterns('tests', '.git', '.pytest_cache', '__pycache__', '*.pyc'))
    config = {'plugins': {'enabled': ['fish-audio'], 'entries': {
        'fish-audio': {'settings': {'api_url': api_url, 'reference_id': voice,
                                   'speech_model': model, 'speed': 1.0, 'timeout': 5}}}},
        'tts': {'provider': 'fish-audio', 'output_format': 'wav'}}
    (home / 'config.yaml').write_text(yaml.safe_dump(config))
    return home


def invoke(home, key, text, output):
    from hermes_constants import set_hermes_home_override, reset_hermes_home_override
    from agent.secret_scope import (set_secret_scope, reset_secret_scope,
                                    set_multiplex_context, reset_multiplex_context)
    from hermes_cli.plugins import discover_plugins
    from tools.tts_tool import text_to_speech_tool, check_tts_requirements
    home_token = set_hermes_home_override(home)
    secret_token = set_secret_scope({'FISH_AUDIO_API_KEY': key}, profile_home=str(home))
    multiplex_token = set_multiplex_context(True)
    try:
        discover_plugins()
        assert check_tts_requirements()
        return json.loads(text_to_speech_tool(text, output_path=str(output)))
    finally:
        reset_multiplex_context(multiplex_token)
        reset_secret_scope(secret_token)
        reset_hermes_home_override(home_token)


def test_discovery_synthesis_and_a_b_a_profile_isolation(tmp_path, monkeypatch, fish_server):
    monkeypatch.setattr(Path, 'home', lambda: tmp_path)
    monkeypatch.setenv('HERMES_HOME', str(tmp_path / 'launch'))
    monkeypatch.setenv('FISH_AUDIO_API_KEY', 'wrong-launch-key')
    url, seen = fish_server
    a = make_home(tmp_path / 'a', url, 'voice-a', 'drama-3')
    b = make_home(tmp_path / 'b', url, 'voice-b', 's2.1-pro')
    for i, (home, key, voice, model) in enumerate([
        (a, 'key-a', 'voice-a', 'drama-3'),
        (b, 'key-b', 'voice-b', 's2.1-pro'),
        (a, 'key-a', 'voice-a', 'drama-3'),
    ]):
        result = invoke(home, key, '你好，这是语音测试。', home / f'audio-{i}.wav')
        assert result['success'] and result['provider'] == 'fish-audio'
        assert result['voice_compatible']
        assert Path(result['file_path']).read_bytes().startswith(b'OggS')
        path, auth, actual_model, body = seen[-1]
        assert (path, auth, actual_model) == ('/v1/tts', 'Bearer ' + key, model)
        assert body['reference_id'] == voice and '你好' in body['text']


def test_http_failure_redacts_key_and_publishes_no_audio(tmp_path, monkeypatch, fish_server):
    monkeypatch.setattr(Path, 'home', lambda: tmp_path)
    monkeypatch.setenv('HERMES_HOME', str(tmp_path / 'launch'))
    url, _ = fish_server
    home = make_home(tmp_path / 'a', url, 'voice-a', 'drama-3')
    out = home / 'failed.wav'
    result = invoke(home, 'never-echo-this-key', 'fail', out)
    assert result['success'] is False
    assert 'HTTP 401' in str(result) and '<redacted>' in str(result)
    assert 'never-echo-this-key' not in str(result)
    assert not out.exists() and not list(home.glob('*.part'))
