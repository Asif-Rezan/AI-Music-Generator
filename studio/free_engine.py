"""Optional free public ACE-Step Space. Subject to Hugging Face ZeroGPU limits."""
from pathlib import Path
import tempfile
from django.conf import settings
from django.core.files import File
from .lyrics import prepare_lyrics, vocal_language

SPACE = 'ACE-Step/Ace-Step-v1.5'

def generate(track):
    from gradio_client import Client
    from .engine import EngineError
    try:
        # Isolate downloads and clean them after Django saves the selected audio.
        with tempfile.TemporaryDirectory(prefix='sonora-hf-') as download_dir:
            client = Client(SPACE, token=settings.HF_TOKEN or None, verbose=False,
                            download_files=download_dir, max_workers=1, analytics_enabled=False)
            info = client.view_api(return_format='dict', print_info=False)
            parameters = info['named_endpoints']['/generation_wrapper']['parameters']
            values = {p['parameter_name']: p.get('parameter_default') for p in parameters}
            required = {'param_4','param_5','param_6','param_9','param_15','param_16'}
            if not required.issubset(values):
                raise EngineError('The free provider changed its API. Please retry later or connect a dedicated ACE-Step server.')
            values.update(selected_model='acestep-v15-xl-turbo', generation_mode='custom',
                param_4=track.prompt, param_5='[Instrumental]' if track.instrumental else prepare_lyrics(track.lyrics),
                param_6=track.bpm, param_7='C Major', param_8='4',
                param_9='unknown' if track.instrumental else vocal_language(track.lyrics),
                param_10=8, param_12=track.seed == -1, param_13=str(track.seed),
                param_15=track.duration, param_16=1, param_30='mp3',
                param_32=False, param_37=False, param_38=False, param_39=False,
                param_43=False, param_44=False)
            job = client.submit(**values, api_name='/generation_wrapper')
            result = job.result(timeout=240)
            first = result[0] if result else None
            if isinstance(first, dict):
                first = first.get('path')
            if not first or not isinstance(first, str):
                status = result[10] if result and len(result) > 10 else 'No audio returned.'
                raise EngineError('Free provider did not produce audio: ' + str(status)[:500])
            file = Path(first).resolve()
            if not file.is_relative_to(Path(download_dir).resolve()) or not file.is_file():
                raise EngineError('Free provider returned an invalid audio file.')
            if not 0 < file.stat().st_size <= 100 * 1024 * 1024:
                raise EngineError('Free provider returned an invalid audio size.')
            with file.open('rb') as audio:
                track.audio.save(str(track.id) + '.mp3', File(audio), save=False)
            track.status = 'completed'
            track.error = ''
            track.save()
    except EngineError:
        raise
    except TimeoutError as exc:
        raise EngineError('The free GPU queue took too long. Please retry later; no audio was saved.') from exc
    except Exception as exc:
        message = str(exc)
        if 'quota' in message.lower():
            raise EngineError('Free GPU quota reached. ' + message[:600] + ' Add your own HF_TOKEN in Vercel for authenticated quota, or try again when it resets.') from exc
        raise EngineError('The free ACE-Step service is unavailable: ' + message[:500]) from exc
