import json
from urllib.parse import urlsplit
import requests
from django.conf import settings
from django.core.files.base import ContentFile
class EngineError(Exception):
    pass

def configuration_error():
    if settings.IS_CLOUD and urlsplit(settings.ACESTEP_URL).hostname in {'localhost', '127.0.0.1', '::1'}:
        return 'Music generation is not connected. Configure ACESTEP_URL in Vercel with the HTTPS address of a running ACE-Step server. The library works independently.'
    return None

def request(method, path, **kwargs):
    error = configuration_error()
    if error:
        raise EngineError(error)
    try:
        response = requests.request(method, settings.ACESTEP_URL + path,
            headers={'Authorization': 'Bearer ' + settings.ACESTEP_API_KEY} if settings.ACESTEP_API_KEY else {},
            timeout=kwargs.pop('timeout', 15), **kwargs)
        response.raise_for_status()
        body = response.json()
        if body.get('error') or body.get('code', 200) != 200:
            raise EngineError(str(body.get('error') or 'Engine rejected request'))
        return body.get('data', body)
    except (requests.RequestException, ValueError) as exc:
        raise EngineError('ACE-Step is unavailable. Start its API on ' + settings.ACESTEP_URL + ' and retry.') from exc

def submit(track):
    result = request('POST', '/release_task', json={
        'prompt': track.prompt, 'lyrics': '[Instrumental]' if track.instrumental else track.lyrics,
        'audio_duration': track.duration, 'bpm': track.bpm, 'seed': track.seed,
        'use_random_seed': track.seed == -1, 'batch_size': 1, 'audio_format': 'mp3',
        'inference_steps': 8, 'thinking': False, 'use_cot_caption': False,
        'use_cot_language': False, 'key_scale': 'C Major', 'time_signature': '4',
    })
    if not isinstance(result, dict) or not result.get('task_id'):
        raise EngineError('Engine returned no task ID.')
    track.task_id = result['task_id']
    track.status = 'running'
    track.error = ''
    track.save()

def refresh(track):
    result = request('POST', '/query_result', json={'task_id_list': [track.task_id]})
    if not isinstance(result, list) or not result:
        return
    item = result[0]
    if item.get('status') == 2:
        track.status = 'failed'
        track.error = str(item.get('error') or 'ACE-Step generation failed.')
        track.save()
        raise EngineError(track.error)
    if item.get('status') != 1:
        return
    outputs = item.get('result', [])
    if isinstance(outputs, str):
        outputs = json.loads(outputs)
    if not outputs or not outputs[0].get('file'):
        raise EngineError('Engine completed without an audio file.')
    url = urlsplit(outputs[0]['file'])
    base = urlsplit(settings.ACESTEP_URL)
    if (url.netloc and (url.netloc != base.netloc or url.scheme != base.scheme)) or url.path != '/v1/audio':
        raise EngineError('Engine returned an invalid audio URL.')
    try:
        response = requests.get(settings.ACESTEP_URL + url.path + '?' + url.query,
            headers={'Authorization': 'Bearer ' + settings.ACESTEP_API_KEY} if settings.ACESTEP_API_KEY else {}, timeout=120)
        response.raise_for_status()
        if not response.content or len(response.content) > 100 * 1024 * 1024:
            raise EngineError('Invalid audio file size.')
        track.audio.save(str(track.id) + '.mp3', ContentFile(response.content), save=False)
    except requests.RequestException as exc:
        raise EngineError('Could not download the generated audio. Retry status check.') from exc
    track.status = 'completed'
    track.error = ''
    track.save()
