import uuid
from django.db import models
class Track(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=100)
    prompt = models.TextField()
    lyrics = models.TextField(blank=True)
    duration = models.PositiveIntegerField(default=30)
    bpm = models.PositiveIntegerField(default=120)
    seed = models.BigIntegerField(default=-1)
    instrumental = models.BooleanField(default=True)
    task_id = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=20, default='queued')
    error = models.TextField(blank=True)
    audio = models.FileField(upload_to='tracks/', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['-created_at']
