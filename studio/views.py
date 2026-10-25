import json
from django.conf import settings
from django.http import JsonResponse, FileResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_GET, require_POST
from .models import Track
from .forms import GenerationForm
from . import engine

def serialize(t):
    return dict(id=str(t.id), title=t.title, prompt=t.prompt, lyrics=t.lyrics, duration=t.duration,
        bpm=t.bpm, seed=t.seed, instrumental=t.instrumental, status=t.status, error=t.error,
        audio=f'/api/tracks/{t.id}/audio/' if t.audio else None, created_at=t.created_at.isoformat())

@require_GET
def index(request):
    return render(request, 'studio/index.html', {'is_cloud': settings.IS_CLOUD, 'temporary_storage': settings.TEMPORARY_STORAGE})

@require_GET
def health(request):
    try:
        data=engine.request('GET', '/health', timeout=2)
        return JsonResponse({'connected': True, 'engine': data})
    except engine.EngineError as exc:
        return JsonResponse({'connected': False, 'message': str(exc)})

@require_GET
def tracks(request):
    return JsonResponse({'tracks': [serialize(t) for t in Track.objects.all()[:100]]})

@require_POST
def generate(request):
    try:
        data=json.loads(request.body)
        if not isinstance(data,dict): raise ValueError()
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({'error':'Expected a JSON object.'}, status=400)
    form=GenerationForm(data)
    if not form.is_valid():
        return JsonResponse({'error': form.errors.get_json_data()}, status=400)
    configuration_error = engine.configuration_error()
    if configuration_error:
        return JsonResponse({"error": configuration_error}, status=503)
    track=Track.objects.create(**form.cleaned_data)
    try:
        engine.submit(track)
    except engine.EngineError as exc:
        track.status='failed'; track.error=str(exc); track.save()
        return JsonResponse(serialize(track), status=503)
    return JsonResponse(serialize(track), status=201)

@require_POST
def status(request, pk):
    track=get_object_or_404(Track,pk=pk)
    if track.status == 'running':
        try:
            engine.refresh(track)
        except (engine.EngineError, ValueError, KeyError, TypeError) as exc:
            track.error=str(exc); track.save()
            return JsonResponse(serialize(track), status=502)
    return JsonResponse(serialize(track))

@require_POST
def delete(request, pk):
    track=get_object_or_404(Track,pk=pk)
    track.audio.delete(save=False); track.delete()
    return JsonResponse({'deleted':True})

@require_GET
def audio(request, pk):
    track=get_object_or_404(Track,pk=pk)
    if not track.audio: return JsonResponse({'error':'Audio is not ready.'},status=404)
    return FileResponse(track.audio.open('rb'), content_type='audio/mpeg',
        as_attachment=request.GET.get('download') == '1', filename=track.title+'.mp3')
