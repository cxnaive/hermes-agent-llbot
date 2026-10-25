"""Fish Audio REST request and atomic audio-file output; no additional SDK required."""
import json
import math
import os
from pathlib import Path
import tempfile
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # The configured endpoint receives the credential; redirects must not forward it elsewhere.
        return None


def write_speech(text, output_path, *, api_key, api_url, voice, model, speed, timeout,
                 output_format):
    if not api_key:
        raise ValueError('Fish Audio API Key is missing; configure the plugin secret.')
    if not voice or not str(voice).strip():
        raise ValueError('Fish Audio voice reference_id is missing.')
    if not text.strip():
        raise ValueError('Speech text is empty.')
    speed, timeout = float(speed), float(timeout)
    if not math.isfinite(speed) or not 0.5 <= speed <= 2.0:
        raise ValueError('Fish Audio speech speed must be between 0.5 and 2.0.')
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError('Fish Audio timeout must be positive.')
    fmt = {'mp3': 'mp3', 'wav': 'wav', 'opus': 'opus', 'ogg': 'opus'}.get(output_format)
    if fmt is None:
        raise ValueError(f'Unsupported Fish Audio format: {output_format}')
    output = Path(output_path).expanduser().with_suffix('.ogg' if fmt == 'opus' else '.' + fmt)
    payload = {'text': text, 'reference_id': str(voice).strip(), 'format': fmt,
               'latency': 'normal', 'normalize': True, 'prosody': {'speed': speed}}
    request = Request(str(api_url).rstrip('/') + '/v1/tts',
                      data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
                      headers={'Authorization': 'Bearer ' + api_key,
                               'Content-Type': 'application/json', 'model': model}, method='POST')
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with build_opener(_NoRedirect).open(request, timeout=timeout) as response:
            content_type = response.headers.get_content_type()
            if not (content_type.startswith('audio/') or content_type == 'application/octet-stream'):
                raise RuntimeError(f'Fish Audio returned an unexpected response type: {content_type}')
            with tempfile.NamedTemporaryFile(dir=output.parent, prefix='.' + output.name,
                                             suffix='.part', delete=False) as stream:
                temporary = Path(stream.name)
                size = 0
                while chunk := response.read(65536):
                    size += len(chunk)
                    if size > 64 * 1024 * 1024:
                        raise RuntimeError('Fish Audio response exceeded 64 MiB.')
                    stream.write(chunk)
            if not size:
                raise RuntimeError('Fish Audio returned empty audio.')
        os.replace(temporary, output)
        temporary = None
        return str(output)
    except HTTPError as exc:
        detail = exc.read(2048).decode('utf-8', errors='replace').replace(api_key, '<redacted>')
        raise RuntimeError(f'Fish Audio HTTP {exc.code}: {detail[:800]}') from None
    except URLError as exc:
        raise RuntimeError(f'Fish Audio connection failed: {exc.reason}') from None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
