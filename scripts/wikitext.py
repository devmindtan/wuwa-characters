"""Convert Fandom wiki infobox wikitext into the plain lines the archive stores."""

import html
import re

LINK = re.compile(r'\[\[([^\[\]|]+)(?:\|([^\[\]]*))?\]\]')
INNER = re.compile(r'\{\{([^{}]*)\}\}')


def _positional(parts):
    return [p.strip() for p in parts if '=' not in p.split('|')[0][:20] or p.strip().startswith('"')]


def _template(body):
    name, *args = body.split('|')
    name = name.strip().lower()
    pos = [a for a in args if not re.match(r'^\s*[A-Za-z_]+\s*=', a)]
    if name == 'color':
        # {{Color|<style>|<text>|...}} or {{Color|<text>|...}}
        if len(pos) >= 2:
            return pos[1]
        return pos[0] if pos else ''
    if name == 'extra effect':
        # {{Extra Effect|<display>|<link>|<tooltip>}}: keep only what is displayed.
        return pos[0] if pos else ''
    if name in ('sic',):
        return ''
    # Unknown template: keep its first positional argument if any.
    return pos[0] if pos else ''


def clean(src):
    """Wikitext -> list of plain text lines."""
    s = re.sub(r'<ref[^>]*/>|<ref[^>]*>.*?</ref>', '', src, flags=re.S)  # footnotes
    # In-game plural placeholder, e.g. {Cus:Sap,S=point P=points SapTag=A} -> points
    s = re.sub(r'\{Cus:Sap,S=([^ }]*) P=([^ }]*)[^}]*\}', r'\2', s)
    s = LINK.sub(lambda m: m.group(2) if m.group(2) is not None else m.group(1), s)
    prev = None
    while prev != s:  # resolve innermost templates first
        prev = s
        s = INNER.sub(lambda m: _template(m.group(1)), s)
    s = re.sub(r'\{(\d+(?:\.\d+)?%?)\}', r'\1', s)  # stray "{3}s" on the wiki -> "3s"
    s = re.sub(r'<br\s*/?>', '\n', s, flags=re.I)
    s = re.sub(r'<[^>]+>', '', s)
    s = s.replace("'''", '').replace("''", '')
    s = html.unescape(s)
    lines = []
    for line in s.split('\n'):
        line = re.sub(r'[ \t]+', ' ', line).strip()
        if line:
            lines.append(line)
    return lines
