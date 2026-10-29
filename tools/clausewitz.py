"""Strict structural parser for the Clausewitz subset used by this mod.

Preserves repeated keys and bare settings. This is not the Vic3 script validator:
engine effects, scoping contracts and UI integration still need the game.
"""
from dataclasses import dataclass
import re
@dataclass(frozen=True)
class Entry:
    key: str
    op: str | None
    value: object
TOKEN = re.compile(r'\s+|#[^\n]*|"(?:\\.|[^"\\])*"|[{}]|>=|<=|!=|\?=|[=<>]|[^\s{}=<>!?#"]+')
def parse(text):
    text = text.lstrip('\ufeff')
    tokens = []
    pos = 0
    while pos < len(text):
        match = TOKEN.match(text, pos)
        if not match:
            raise ValueError(f'Invalid token at offset {pos}: {text[pos:pos+40]!r}')
        token = match.group()
        if not token.isspace() and not token.startswith('#'):
            tokens.append(token)
        pos = match.end()
    i = 0
    def block(nested=False):
        nonlocal i
        result = []
        while i < len(tokens):
            key = tokens[i]; i += 1
            if key == '}':
                if not nested: raise ValueError('Unexpected closing brace')
                return result
            if key in ('{', '=', '>=', '<=', '>', '<', '!=', '?='):
                raise ValueError(f'Expected key, got {key}')
            if i < len(tokens) and tokens[i] in ('=', '>=', '<=', '>', '<', '!=', '?='):
                op = tokens[i]; i += 1
                if i >= len(tokens): raise ValueError(f'Missing value for {key}')
                value = tokens[i]; i += 1
                if value == '{': value = block(True)
                elif value == '}': raise ValueError(f'Missing value for {key}')
                result.append(Entry(key, op, value))
            else:
                result.append(Entry(key, None, None))
        if nested: raise ValueError('Unclosed brace')
        return result
    return block()
def get(entries, key, default=None):
    matches = [e.value for e in entries if e.key == key]
    if len(matches) > 1: raise ValueError(f'Duplicate singleton key: {key}')
    return matches[0] if matches else default
def walk(entries):
    for e in entries:
        yield e
        if isinstance(e.value, list): yield from walk(e.value)
