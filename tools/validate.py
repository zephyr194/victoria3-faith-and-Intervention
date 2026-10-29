"""Repository checks; deliberately makes no claim of game-engine validation."""
from pathlib import Path
import json
import re
import sys
from clausewitz import parse, walk, get
ROOT = Path(__file__).resolve().parents[1]
def validate():
    errors = []
    files = {}
    definitions = {}
    for p in sorted((ROOT/'mod').rglob('*.txt')):
        try:
            entries = parse(p.read_text(encoding='utf-8-sig'))
            files[p] = entries
            for entry in entries:
                if entry.key == 'namespace': continue
                if entry.key in definitions: errors.append(f'duplicate definition: {entry.key}')
                definitions[entry.key] = entry
        except ValueError as exc: errors.append(f'{p.relative_to(ROOT)}: {exc}')
    loc = json.loads((ROOT/'localization.json').read_text())
    from holy_content import generate as generate_holy
    # Read expected strings without writing runtime during validation.
    loc.update(generate_holy(write=False))
    for key, translations in loc.items():
        if set(translations) != {'english','simp_chinese'} or not all(translations.values()):
            errors.append(f'incomplete translation: {key}')
    references = {'fia_monthly_pulse', 'je_fia_overview'}
    loc_fields = {'title','desc','flavor','name','status_desc'}
    def require_loc(key):
        key = key.strip('"')
        if key not in loc: errors.append(f'missing localization: {key}')
    for p, entries in files.items():
        for e in walk(entries):
            if e.key.startswith('fia_') and e.value in ('yes','no'):
                references.add(e.key)
            if e.key in ('id','type','war_goal') and isinstance(e.value,str) and e.value.startswith(('fia.','fia_','je_fia_','dp_fia_')):
                references.add(e.value)
            if e.key in loc_fields and isinstance(e.value,str) and e.value.startswith(('fia.','fia_','je_fia_')):
                if e.key != 'name' or e.value.startswith('fia.'): require_loc(e.value)
        if p.parent.name in ('decisions','journal_entries','static_modifiers','diplomatic_plays','war_goal_types'):
            for entry in entries:
                require_loc(entry.key)
        if p.parent.name == 'events':
            if not p.read_bytes().startswith(b'\xef\xbb\xbf'): errors.append(f'missing event BOM: {p.name}')
            namespaces = {e.value for e in entries if e.key == 'namespace'}
            for entry in entries:
                if entry.key == 'namespace': continue
                if entry.key.split('.')[0] not in namespaces: errors.append(f'undeclared namespace: {entry.key}')
                if not any(x.key == 'option' for x in entry.value): errors.append(f'no options: {entry.key}')
    for ref in references:
        if ref not in definitions: errors.append(f'undefined reference: {ref}')
    balance = json.loads((ROOT/'balance.json').read_text())
    if not 0 < balance['incident_threshold'] < balance['crisis_threshold'] < balance['intervention_threshold'] < balance['maximum_tension']:
        errors.append('invalid threshold ordering')
    expected = {f'fia_{k}':str(v) for k,v in balance.items()}
    actual = {e.key:e.value for e in files[ROOT/'mod/common/script_values/fia_parameters.txt']}
    if expected != actual: errors.append('parameters out of date: run tools/build_content.py')
    for lang in ('english','simp_chinese'):
        p = ROOT/f'mod/localization/{lang}/fia_l_{lang}.yml'
        if not p.read_bytes().startswith(b'\xef\xbb\xbf'): errors.append(f'missing localization BOM: {lang}')
        lines = p.read_text(encoding='utf-8-sig').splitlines()
        if lines[0] != f'l_{lang}:': errors.append(f'bad localization header: {lang}')
        keys = []
        for line in lines[1:]:
            match = re.fullmatch(r' ([\w.]+):0 (".*")',line)
            if not match: errors.append(f'invalid localization line: {line[:60]}'); continue
            key,value = match.groups(); keys.append(key)
            try:
                if json.loads(value) != loc[key][lang]: errors.append(f'stale translation: {key}/{lang}')
            except (ValueError, KeyError) as exc: errors.append(str(exc))
        if len(set(keys)) != len(keys) or set(keys) != set(loc): errors.append(f'localization key mismatch: {lang}')
    # Primary interface definitions remain additive, with one namespaced child pulse.
    pulse = definitions['on_monthly_pulse_country'].value
    if [e.key for e in pulse] != ['on_actions']: errors.append('vanilla monthly pulse overwritten')
    for path, entries in files.items():
        if path.parent.name == 'war_goal_types':
            for e in walk(entries):
                if e.key in ('annex','set_state_owner','change_pop_religion','activate_law'): errors.append(f'unexpected coercive effect in {path.name}')
    global_pulse = definitions['on_monthly_pulse'].value
    if [e.key for e in global_pulse] != ['on_actions']: errors.append('vanilla global monthly pulse overwritten')
    if errors: raise ValueError('\n'.join(errors))
    return f'PASS: {len(files)} script files, {len(definitions)} definitions, {len(loc)} bilingual strings; structural checks only.'
if __name__ == '__main__':
    try: print(validate())
    except ValueError as exc: print(exc, file=sys.stderr); sys.exit(1)
