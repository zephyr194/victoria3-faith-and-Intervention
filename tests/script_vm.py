"""Fail-closed test interpreter for this mod's script subset, not a Vic3 emulator.

Executes the committed script AST to catch transition/scoping regressions. Engine
scheduling, UI, combat, AI and modifiers' game effects require an actual game.
"""
from dataclasses import dataclass, field
from pathlib import Path
import json
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from clausewitz import parse, get
ROOT=Path(__file__).resolve().parents[1]
@dataclass(eq=False)
class Obj:
    kind: str
    attrs: dict = field(default_factory=dict)
    vars: dict = field(default_factory=dict)
    modifiers: set = field(default_factory=set)
    states: list = field(default_factory=list)
    pops: list = field(default_factory=list)
    journals: set = field(default_factory=set)
    groups: list = field(default_factory=list)

class VM:
    def __init__(self, root, countries=()):
        self.root=root;self.stack=[root];self.scopes={};self.countries=list(countries)
        self.events=[];self.radicals=[];self.loyalists=[];self.globals={};self.objects={}
        self.defs={}
        for p in (ROOT/'mod').rglob('*.txt'):
            for e in parse(p.read_text(encoding='utf-8-sig')):
                self.defs[e.key]=e.value
        self.constants={'fia_'+k:v for k,v in json.loads((ROOT/'balance.json').read_text()).items()}
    @property
    def cur(self): return self.stack[-1]
    def resolve(self, value):
        if not isinstance(value,str): return value
        if value.startswith('"'): return json.loads(value)
        if value in self.constants: return self.constants[value]
        if value in ('yes','no'): return value=='yes'
        try: return float(value)
        except ValueError: pass
        parts=value.split('.')
        token=parts.pop(0)
        if token=='root': result=self.root
        elif token=='prev': result=self.stack[-2]
        elif token=='this': result=self.cur
        elif token.startswith('global_var:'): result=self.globals.get(token[11:])
        elif token.startswith(('s:','c:')): result=self.objects.get(token)
        elif token.startswith('scope:'): result=self.scopes.get(token[6:])
        elif token.startswith('var:'): result=self.cur.vars.get(token[4:])
        elif token in self.cur.attrs: result=self.cur.attrs[token]
        else: return value
        for part in parts:
            if not isinstance(result,Obj): return None
            result=result.vars.get(part[4:]) if part.startswith('var:') else result.attrs.get(part)
        return result
    def scoped(self,obj,fn,entries):
        if not isinstance(obj,Obj): return False
        self.stack.append(obj)
        try: return fn(entries)
        finally: self.stack.pop()
    @staticmethod
    def compare(a,op,b):
        if op in ('=','?='): return a==b
        if a is None or b is None: return False
        return {'>':lambda:a>b,'<':lambda:a<b,'>=':lambda:a>=b,'<=':lambda:a<=b,'!=':lambda:a!=b}[op]()
    def condition(self,entries): return all(self.term(e) for e in entries)
    def term(self,e):
        k,v=e.key,e.value
        if k=='OR': return any(self.term(x) for x in v)
        if k in ('AND','limit'): return self.condition(v)
        if k=='NOT': return not self.condition(v)
        if k=='NOR': return not any(self.term(x) for x in v)
        if k in self.defs and k.startswith('fia_'):
            return self.condition(self.defs[k]) == self.resolve(v)
        if k=='always': return self.resolve(v)
        if k=='exists':
            x=self.resolve(v);return isinstance(x,Obj) and x.attrs.get('is_country_alive',True)
        if k=='has_global_variable': return v in self.globals
        if k=='religion_percent_country':
            test=next(x for x in v if x.key=='value')
            return self.compare(self.cur.attrs.get('shares',{}).get(self.resolve(get(v,'target')),0),test.op,self.resolve(test.value))
        if k=='has_variable': return v in self.cur.vars
        if k=='has_journal_entry': return v in self.cur.journals
        if k=='has_pop_religion': return self.cur.attrs.get('religion')==self.resolve(v)
        if k=='has_law': return v in self.cur.attrs.get('laws',set())
        if k=='is_country_type': return self.cur.attrs.get('country_type')==v
        if k in ('has_war_with','has_truce_with','is_diplomatic_play_participant_with'):
            return self.resolve(v) in self.cur.attrs.get(k,set())
        if k=='has_interest_marker_in_region': return self.resolve(v) in self.cur.attrs.get('interests',set())
        if k=='religion_percent_state':
            share=self.cur.attrs.get('shares',{}).get(self.resolve(get(v,'target')),0)
            test=next(x for x in v if x.key=='value')
            return self.compare(share,test.op,self.resolve(test.value))
        if k=='any_interest_group':return any(self.scoped(x,self.condition,v) for x in self.cur.groups)
        if k=='is_interest_group_type':return self.cur.attrs.get('group_type')==v
        if k=='any_scope_pop': return any(self.scoped(x,self.condition,v) for x in self.cur.pops)
        if k=='any_scope_state': return any(self.scoped(x,self.condition,v) for x in self.cur.states)
        if k=='any_diplomatic_play': return False  # integration-tested in game, never fabricated
        if isinstance(v,list): return self.scoped(self.resolve(k),self.condition,v)
        known={'religion','owner','this','root','prev','prestige','is_country_alive','is_subject','is_at_war','has_state_religion','pop_acceptance','total_size','turmoil','standard_of_living','state_population','devastation','ig_clout'}
        if k not in known and not k.startswith(('var:','global_var:','scope:')): raise AssertionError(f'Unsupported test trigger: {k}')
        return self.compare(self.resolve(k),e.op,self.resolve(v))
    def effect(self,entries):
        branch=False
        for e in entries:
            k,v=e.key,e.value
            if k in ('if','else_if','else'):
                if k=='if': branch=False
                if not branch and (k=='else' or self.condition(get(v,'limit',[]))):
                    self.effect([x for x in v if x.key!='limit']);branch=True
                continue
            branch=False
            if k in self.defs and k.startswith('fia_'):
                self.effect(self.defs[k]);continue
            if k=='set_global_variable':self.globals[get(v,'name')]=self.resolve(get(v,'value',1));continue
            if k=='remove_global_variable':self.globals.pop(v,None);continue
            if k=='change_global_variable':
                key=get(v,'name');self.globals[key]+=self.resolve(get(v,'add'));continue
            if k=='set_variable': self.cur.vars[get(v,'name')]=self.resolve(get(v,'value',1));continue
            if k=='remove_variable': self.cur.vars.pop(v,None);continue
            if k=='change_variable':
                key=get(v,'name');a=self.cur.vars[key]
                for op in v:
                    if op.key=='name':continue
                    b=self.resolve(op.value)
                    if op.key=='add':a+=b
                    elif op.key=='subtract':a-=b
                    else:raise AssertionError(op.key)
                self.cur.vars[key]=a;continue
            if k=='clamp_variable':
                key=get(v,'name');self.cur.vars[key]=max(self.resolve(get(v,'min')),min(self.resolve(get(v,'max')),self.cur.vars[key]));continue
            if k=='save_scope_value_as':self.scopes[get(v,'name')]=self.resolve(get(v,'value'));continue
            if k=='save_scope_as':self.scopes[v]=self.cur;continue
            if k=='add_modifier':self.cur.modifiers.add(get(v,'name'));continue
            if k=='remove_modifier':self.cur.modifiers.discard(v);continue
            if k=='add_journal_entry':self.cur.journals.add(get(v,'type'));continue
            if k=='trigger_event':self.events.append((self.cur,get(v,'id')));continue
            if k=='add_radicals':self.radicals.append((self.cur,self.resolve(get(v,'religion')),float(self.resolve(get(v,'value')))));continue
            if k=='add_loyalists':self.loyalists.append((self.cur,self.resolve(get(v,'religion')),float(self.resolve(get(v,'value')))));continue
            if k=='add_radicals_in_state':self.radicals.append((self.cur,self.resolve(get(v,'religion')),float(self.resolve(get(v,'value')))));continue
            if k=='every_scope_state':
                for state in self.cur.states:
                    if self.scoped(state,self.condition,get(v,'limit',[])):
                        self.scoped(state,self.effect,[x for x in v if x.key!='limit'])
                continue
            if k in ('ordered_scope_pop','ordered_country','ordered_scope_state'):
                objects=self.cur.pops if k=='ordered_scope_pop' else self.cur.states if k=='ordered_scope_state' else self.countries
                candidates=[x for x in objects if self.scoped(x,self.condition,get(v,'limit',[]))]
                order=get(v,'order_by')
                candidates.sort(key=lambda obj:self.scoped(obj,lambda _:self.resolve(order),[]),reverse=True)
                for obj in candidates[:int(get(v,'max','1'))]:
                    self.scoped(obj,self.effect,[x for x in v if x.key not in ('limit','order_by','max')])
                continue
            if isinstance(v,list):
                target=self.resolve(k)
                if not isinstance(target,Obj):raise AssertionError(f'Missing effect scope: {k}')
                self.scoped(target,self.effect,v);continue
            raise AssertionError(f'Unsupported test effect: {k}')
    def run(self,name,obj=None):
        if obj is None:self.effect(self.defs[name])
        else:self.scoped(obj,self.effect,self.defs[name])

def world(tension=70):
    host=Obj('country',{'is_country_alive':True,'is_subject':False,'is_at_war':False,'country_type':'recognized','religion':'sunni','laws':{'law_type:law_state_religion'},'prestige':80})
    patron=Obj('country',{'is_country_alive':True,'is_subject':False,'is_at_war':False,'country_type':'recognized','religion':'orthodox','prestige':100,'interests':{'balkans'}})
    state=Obj('state',{'owner':host,'state_population':100000,'turmoil':0.2,'region':'balkans','shares':{'orthodox':0.4}}, {'fia_tension':tension,'fia_faith':'orthodox','fia_case_owner':host,'fia_incident':1})
    host.states=[state];host.vars['fia_fatigue']=0;patron.vars['fia_fatigue']=0
    state.pops=[Obj('pop',{'religion':'orthodox','has_state_religion':False,'pop_acceptance':30,'standard_of_living':9,'total_size':40000})]
    vm=VM(patron,[host,patron]);return vm,host,patron,state
