import json
import tempfile
from unittest.mock import patch, Mock
from django.test import TestCase, override_settings, Client
from .models import Track
from . import engine

class StudioTests(TestCase):
    def payload(self, **kw):
        return dict(title='Night drive',prompt='Warm analog synthwave',lyrics='',duration=30,bpm=120,seed=-1,instrumental=True,**kw)
    def test_home_and_empty_library(self):
        self.assertContains(self.client.get('/'), 'Turn an idea into')
        self.assertEqual(self.client.get('/api/tracks/').json(), {'tracks':[]})
    def test_validation_and_malformed_json(self):
        for data in ['[]','{',json.dumps({'duration':999})]:
            self.assertEqual(self.client.post('/api/generate/',data,content_type='application/json').status_code,400)
        self.assertFalse(Track.objects.exists())
    def test_csrf_protection(self):
        client=Client(enforce_csrf_checks=True)
        self.assertEqual(client.post('/api/generate/',self.payload(),content_type='application/json').status_code,403)
    @patch('studio.engine.requests.request')
    def test_submit_uses_official_api(self, req):
        req.return_value=Mock(json=lambda:{'code':200,'data':{'task_id':'abc'}})
        r=self.client.post('/api/generate/',self.payload(),content_type='application/json')
        self.assertEqual(r.status_code,201)
        self.assertEqual(r.json()['status'],'running')
        args=req.call_args
        self.assertTrue(args.args[1].endswith('/release_task'))
        self.assertEqual(args.kwargs['json']['lyrics'],'[Instrumental]')
        self.assertEqual(args.kwargs['json']['batch_size'],1)
    @patch('studio.engine.request',side_effect=engine.EngineError('Engine offline'))
    def test_offline_is_honest_and_saved(self, req):
        r=self.client.post('/api/generate/',self.payload(),content_type='application/json')
        self.assertEqual(r.status_code,503)
        self.assertEqual(Track.objects.get().status,'failed')
        self.assertFalse(r.json()['audio'])
    @patch('studio.engine.requests.get')
    @patch('studio.engine.request')
    def test_completion_download_playback_and_delete(self, req, download):
        with tempfile.TemporaryDirectory() as root, override_settings(MEDIA_ROOT=root):
            t=Track.objects.create(**self.payload(),task_id='abc',status='running')
            req.return_value=[{'task_id':'abc','status':1,'result':json.dumps([{'file':'/v1/audio?path=test.mp3'}])}]
            download.return_value=Mock(content=b'ID3testaudio')
            r=self.client.post(f'/api/tracks/{t.id}/status/',{},content_type='application/json')
            self.assertEqual(r.json()['status'],'completed')
            audio=self.client.get(r.json()['audio']+'?download=1')
            self.assertEqual(b''.join(audio.streaming_content),b'ID3testaudio')
            self.assertIn('attachment',audio['Content-Disposition'])
            self.assertEqual(self.client.post(f'/api/tracks/{t.id}/delete/').status_code,200)
            self.assertFalse(Track.objects.exists())
    @patch('studio.engine.request')
    def test_rejects_foreign_audio_url(self, req):
        t=Track.objects.create(**self.payload(),task_id='abc',status='running')
        req.return_value=[{'status':1,'result':[{'file':'http://example.com/v1/audio?path=x'}]}]
        with self.assertRaises(engine.EngineError):engine.refresh(t)
    @patch('studio.engine.request')
    def test_running_and_failed_engine_status(self, req):
        t=Track.objects.create(**self.payload(),task_id='abc',status='running')
        req.return_value=[{'status':0}]
        engine.refresh(t);self.assertEqual(t.status,'running')
        req.return_value=[{'status':2,'error':'Out of memory'}]
        with self.assertRaisesMessage(engine.EngineError,'Out of memory'):engine.refresh(t)
    def test_lyrics_visible_by_default(self):
        response=self.client.get('/')
        self.assertContains(response,'Write your lyrics')
        self.assertNotContains(response,'id="lyrics-area" hidden')

    @override_settings(TEMPORARY_STORAGE=True, IS_CLOUD=True)
    def test_temporary_library_notice(self):
        response = self.client.get('/')
        self.assertContains(response, 'Temporary library')
        self.assertNotContains(response, 'connect PostgreSQL')
