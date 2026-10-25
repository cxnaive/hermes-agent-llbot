"""Fish Audio provider using Hermes' public plugin configuration and TTS APIs."""
from agent.secret_scope import get_secret_str
from agent.tts_provider import TTSProvider

from .client import write_speech


class FishAudioProvider(TTSProvider):
    def __init__(self, ctx):
        self.ctx = ctx

    @property
    def name(self):
        return 'fish-audio'

    @property
    def display_name(self):
        return 'Fish Audio'

    @property
    def voice_compatible(self):
        return True

    def is_available(self):
        return bool(get_secret_str('FISH_AUDIO_API_KEY').strip()
                    and self.ctx.get_config('reference_id', '').strip())

    def default_model(self):
        return self.ctx.get_config('speech_model', 'drama-3')

    def default_voice(self):
        return self.ctx.get_config('reference_id', '') or None

    def list_models(self):
        return [{'id': model, 'display': model} for model in
                ('drama-3', 's2.1-pro', 's2.1-pro-free', 's2-pro', 's1')]

    def list_voices(self):
        voice = self.default_voice()
        return [{'id': voice, 'display': 'Configured Fish Audio voice'}] if voice else []

    def get_setup_schema(self):
        return {'name': self.display_name, 'badge': 'API', 'tag': 'Fish Audio',
                'env_vars': [{'key': 'FISH_AUDIO_API_KEY', 'prompt': 'Fish Audio API Key',
                              'url': 'https://fish.audio/app/api-keys/'}]}

    def synthesize(self, text, output_path, *, voice=None, model=None, speed=None,
                   format='mp3', **extra):
        # Resolve settings and secrets per call so one loaded provider cannot pin another profile.
        return write_speech(
            text, output_path,
            api_key=get_secret_str('FISH_AUDIO_API_KEY').strip(),
            api_url=self.ctx.get_config('api_url', 'https://api.fish.audio'),
            voice=voice or self.default_voice(), model=model or self.default_model(),
            speed=speed if speed is not None else self.ctx.get_config('speed', 1.0),
            timeout=self.ctx.get_config('timeout', 120), output_format=format,
        )


def register(ctx):
    ctx.register_tts_provider(FishAudioProvider(ctx))
