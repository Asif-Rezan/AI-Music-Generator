"""Prepare section annotations while preserving the user's original lyrics."""
import re
import unicodedata

BENGALI = re.compile(r'[\u0980-\u09ff]')

def prepare_lyrics(text):
    lines = unicodedata.normalize('NFC', text).splitlines()
    sections = []
    current = []
    repeat = 1
    def flush():
        if current:
            sections.extend(['\n'.join(current)] * repeat)
    for line in lines:
        clean = line.strip().strip('🎵🎶🎼🌙 ').strip()
        heading = re.fullmatch(r'[\(\[]([^\)\]]+)[\)\]]', clean)
        if heading:
            name = heading.group(1)
            kind = None
            if 'কোরাস' in name or 'chorus' in name.lower():
                kind = 'Chorus'
            elif 'অন্তরা' in name or 'verse' in name.lower():
                kind = 'Verse'
            elif 'সেতু' in name or 'bridge' in name.lower():
                kind = 'Bridge'
            elif 'intro' in name.lower():
                kind = 'Intro'
            elif 'outro' in name.lower():
                kind = 'Outro'
            if kind:
                flush()
                current = ['[' + kind + ']']
                repeat = 2 if 'দুইবার' in name or re.search(r'\b(?:x2|2x|twice)\b', name, re.I) else 1
                continue
        current.append(clean)
    flush()
    return '\n\n'.join(sections).strip()

def vocal_language(text):
    return 'bn' if BENGALI.search(text) else 'en'
