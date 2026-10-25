from django import forms
class GenerationForm(forms.Form):
    title = forms.CharField(max_length=100)
    prompt = forms.CharField(max_length=4000)
    lyrics = forms.CharField(max_length=12000, required=False)
    duration = forms.IntegerField(min_value=10, max_value=600)
    bpm = forms.IntegerField(min_value=30, max_value=300)
    seed = forms.IntegerField(min_value=-1, max_value=2147483647, initial=-1)
    instrumental = forms.BooleanField(required=False)
