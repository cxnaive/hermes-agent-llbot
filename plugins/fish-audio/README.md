# Fish Audio for Hermes

Native plugin registered through `ctx.register_tts_provider()`, maintained in this Hermes fork
under `plugins/fish-audio`. Enable `fish-audio` in `plugins.enabled` and choose
`tts.provider: fish-audio`. The directory can also be installed as
`<HERMES_HOME>/plugins/fish-audio` on another Hermes installation. Requires only Python's standard
library and Hermes' public plugin APIs.

Settings follow the standard plugin layout:

```yaml
plugins:
  enabled: [fish-audio]
  entries:
    fish-audio:
      settings:
        api_url: https://api.fish.audio
        speech_model: drama-3
        reference_id: YOUR_VOICE_ID
        speed: 1.0
        timeout: 120
tts:
  provider: fish-audio
```

Add `FISH_AUDIO_API_KEY` to the active profile's `.env`, or use the plugin's masked API Key
field in the Desktop settings form. Settings use `ctx.get_config()` and credentials use
`agent.secret_scope.get_secret_str()` on every synthesis. The manifest's `config_schema`
provides the standard settings form; the key is never included in source or command arguments.

Audio uses Fish's `POST /v1/tts` and the exact configured `model` header. The standard Hermes
TTS tool cleans speech text, generates audio, converts voice-compatible output to Ogg/Opus,
and returns a media path. The plugin itself never sends chat messages. Automatic replies remain
controlled by Hermes' voice settings. A synthesized file is published only after a complete,
nonempty audio response, and API errors redact the credential.

Docs: https://docs.fish.audio/features/text-to-speech/drama-3

This version supports complete-file synthesis; Hermes handles delivery and optional chunking.
It does not implement Fish's bidirectional WebSocket API.

## Validation

Requires a Hermes checkout with the native TTS provider plugin API and its test environment.
From that checkout, run the plugin's integration tests through the Hermes test runner:

```bash
scripts/run_tests.sh tests/plugins/test_fish_audio.py -q
```

The tests use a local HTTP server and temporary profiles, exercise real plugin discovery and
audio conversion, and verify A → B → A profile isolation and credential redaction on API errors.
They do not call the Fish Audio service or send chat messages. Hermes' audio conversion requires
FFmpeg to be available.
