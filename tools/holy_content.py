"""Generate bounded, religion-filtered holy-site crises. No instant conversions."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
def generate(write=True):
    config=json.loads((ROOT/'holy_sites.json').read_text())
    assert config['site']=='jerusalem', 'One-site pilot; add an explicit multi-site state model before extending.'
    effects=[];triggers=[];decisions=[];events=['namespace = fia'];loc={}
    def s(k,zh,en):loc[k]={'simp_chinese':zh,'english':en}
    def out(path,text):
        if write:(ROOT/'mod'/path).write_text('\n'.join(line.rstrip() for line in text.splitlines())+'\n',encoding='utf-8-sig')
    s('je_fia_holy','圣地与宗教影响力','Holy Sites and Religious Influence')
    s('je_fia_holy_reason','耶路撒冷的控制变化与礼拜限制引发跨国宗教诉求。承诺并不等于成果；只有实际恢复通行才结算忠诚收益。','Changes in Jerusalem’s control and worship restrictions generate international religious petitions. Promises are not results: loyalty requires restored access.')
    s('je_fia_holy_status',"圣地严重程度：[GetGlobalVariable('fia_holy_severity').GetValue|0]/3。0正常、1控制变化、2礼拜受限或战争破坏、3严重破坏。通过决议查看并回应各宗教诉求。", "Site severity: [GetGlobalVariable('fia_holy_severity').GetValue|0]/3. 0 normal, 1 control change, 2 worship restrictions or wartime damage, 3 severe damage. Use Decisions to review religious petitions.")
    # Avoid relying on a global-localization function: cache severity on each country.
    for lang in loc['je_fia_holy_status']:
        loc['je_fia_holy_status'][lang]=loc['je_fia_holy_status'][lang].replace("GetGlobalVariable('fia_holy_severity').GetValue", "JournalEntry.GetCountry.MakeScope.Var('fia_holy_severity_display').GetValue")
    s('fia_holy_relief_cost','圣地救济与外交协调','Holy-Site Relief and Diplomacy')
    s('fia_holy_credibility','护教成果信誉','Credibility from Religious Protection')
    s('fia_holy_open','保障耶路撒冷礼拜与朝圣','Guarantee Worship and Pilgrimage in Jerusalem')
    s('fia_holy_open_desc','为所有关联宗教恢复通行；移除本Mod的宗教活动限制。不能瞬间修复战争破坏。','Restore access for every associated faith and remove this mod’s worship restrictions. This does not instantly repair war damage.')
    s('fia_holy_restrict','限制耶路撒冷宗教活动','Restrict Religious Activity in Jerusalem')
    s('fia_holy_restrict_desc','对圣地实施宗教活动限制，可能引发多个宗教社群的不满。此决议代表明确的限制行为，不从统治者宗教自动推断迫害。','Impose worship restrictions, potentially mobilizing several religious communities. This is an explicit policy, not an inference from the ruler’s faith.')
    for key in ('fia_holy_open','fia_holy_restrict'):
        s(key+'_tooltip',loc[key+'_desc']['simp_chinese'],loc[key+'_desc']['english'])
    decisions.append('''fia_holy_open = {
    is_shown = { fia_holy_is_custodian = yes }
    possible = { global_var:fia_holy_state = { has_variable = fia_holy_restricted } }
    when_taken = { global_var:fia_holy_state = { remove_variable = fia_holy_restricted } }
    ai_chance = { value = 10 }
}
fia_holy_restrict = {
    is_shown = { fia_holy_is_custodian = yes }
    possible = {
        fia_restrictive_policy = yes
        global_var:fia_holy_state = { NOT = { has_variable = fia_holy_restricted } }
        NOT = { has_variable = fia_holy_policy_cooldown }
    }
    when_taken = {
        global_var:fia_holy_state = { set_variable = { name = fia_holy_restricted value = 1 } }
        set_variable = { name = fia_holy_policy_cooldown value = 1 days = fia_holy_reward_cap_days }
    }
    ai_chance = { value = 0 }
}''')
    triggers.append('''fia_holy_is_custodian = {
    exists = global_var:fia_holy_state
    global_var:fia_holy_state = { owner = prev }
}
fia_holy_is_resolved = {
    exists = global_var:fia_holy_state
    global_var:fia_holy_severity <= 1
    global_var:fia_holy_state = { NOT = { has_variable = fia_holy_restricted } }
}''')
    for i,f in enumerate(config['faiths']):
        k=f['key'];r='rel:'+k;p='fia_holy_'+k;event=f'fia.{100+i}'
        # Every faith is evaluated independently; minority populations are included.
        triggers.append(f'''{p}_affected = {{
    religion_percent_country = {{ target = {r} value >= fia_holy_minimum_share }}
    any_scope_pop = {{ has_pop_religion = {r} total_size >= fia_minimum_population }}
}}
{p}_voice = {{
    religion = {r}
    is_subject = no
    OR = {{ has_law = law_type:law_theocracy fia_restrictive_policy = yes }}
    prestige >= 50
    any_interest_group = {{ is_interest_group_type = ig_devout ig_clout >= fia_holy_devout_clout }}
}}
{p}_pending = {{
    has_variable = {p}_age
    has_variable = {p}_epoch
    var:{p}_epoch = global_var:fia_holy_epoch
}}''')
        effects.append(f'''{p}_clear = {{
    remove_variable = {p}_age
    remove_variable = {p}_response
    remove_variable = {p}_severity
    remove_variable = {p}_importance
}}
{p}_success = {{
    if = {{
        limit = {{ NOT = {{ has_variable = {p}_reward_cap }} }}
        add_loyalists = {{ religion = {r} value = fia_holy_reward }}
        set_variable = {{ name = {p}_reward_cap value = 1 days = fia_holy_reward_cap_days }}
        change_variable = {{ name = {p}_influence add = 5 }}
        change_variable = {{ name = {p}_authority add = 5 }}
        add_modifier = {{ name = fia_holy_credibility months = 24 }}
        if = {{ limit = {{ religion = {r} }} add_modifier = {{ name = fia_holy_domestic_trust months = 24 }} }}
    }}
}}
{p}_failure = {{
    if = {{
        limit = {{ NOT = {{ has_variable = {p}_penalty_cap }} }}
        if = {{
            limit = {{ var:{p}_response = 3 }}
            add_radicals = {{ religion = {r} value = fia_holy_broken_promise_rate }}
            change_variable = {{ name = {p}_influence subtract = 10 }}
            change_variable = {{ name = {p}_authority subtract = 10 }}
            if = {{ limit = {{ religion = {r} }} add_modifier = {{ name = fia_holy_broken_promise months = 12 }} }}
        }}
        else_if = {{
            limit = {{ has_global_variable = {p}_restraint }}
            add_radicals = {{ religion = {r} value = fia_holy_neglect_low }}
        }}
        else_if = {{
            limit = {{ OR = {{ var:{p}_severity >= 2 has_global_variable = {p}_call }} }}
            if = {{
                limit = {{ religion = {r} fia_restrictive_policy = yes }}
                add_radicals = {{ religion = {r} value = fia_holy_national_mobilization }}
            }}
            else_if = {{
                limit = {{ var:{p}_importance >= 85 }}
                add_radicals = {{ religion = {r} value = fia_holy_neglect_major }}
            }}
            else = {{ add_radicals = {{ religion = {r} value = fia_holy_neglect_minor }} }}
            change_variable = {{ name = {p}_influence subtract = 5 }}
        }}
        else = {{ add_radicals = {{ religion = {r} value = fia_holy_neglect_low }} }}
        set_variable = {{ name = {p}_penalty_cap value = 1 days = fia_holy_reward_cap_days }}
    }}
}}
{p}_tick = {{
    if = {{
        limit = {{ NOT = {{ has_variable = {p}_influence }} }}
        set_variable = {{ name = {p}_influence value = 10 }}
        set_variable = {{ name = {p}_authority value = 30 }}
        set_variable = {{ name = {p}_seen value = 0 }}
        {('if = { limit = { this = c:PAP religion = rel:catholic } set_variable = { name = '+p+'_authority value = 60 } }') if k=='catholic' else ''}
    }}
    if = {{ limit = {{ is_subject = yes }} change_variable = {{ name = {p}_authority subtract = 1 }} }}
    if = {{
        limit = {{ {p}_affected = yes global_var:fia_holy_epoch > var:{p}_seen }}
        # New epochs supersede stale petitions, never score the old one as failure.
        {p}_clear = yes
        set_variable = {{ name = {p}_seen value = global_var:fia_holy_epoch }}
        if = {{
            limit = {{ global_var:fia_holy_severity >= 1 }}
            set_variable = {{ name = {p}_epoch value = global_var:fia_holy_epoch }}
            set_variable = {{ name = {p}_age value = 0 }}
            set_variable = {{ name = {p}_response value = 0 }}
            set_variable = {{ name = {p}_severity value = global_var:fia_holy_severity }}
            set_variable = {{ name = {p}_importance value = {f['importance']} }}
            trigger_event = {{ id = {event} popup = yes }}
        }}
    }}
    if = {{
        limit = {{ has_variable = {p}_age }}
        if = {{
            limit = {{ {p}_pending = no }}
            {p}_clear = yes
        }}
        else = {{
            change_variable = {{ name = {p}_age add = 1 }}
            if = {{
                limit = {{ {p}_affected = no }}
                {p}_clear = yes
            }}
            else_if = {{
                limit = {{ fia_holy_is_resolved = yes var:{p}_age >= fia_holy_settlement_delay }}
                if = {{ limit = {{ var:{p}_response >= 1 }} {p}_success = yes }}
                {p}_clear = yes
            }}
            else_if = {{
                limit = {{
                    var:{p}_age >= fia_holy_response_months
                    OR = {{
                        var:{p}_age >= fia_holy_war_deadline
                        NOT = {{ has_war_with = global_var:fia_holy_owner }}
                    }}
                }}
                if = {{
                    limit = {{ OR = {{ var:{p}_response = 0 var:{p}_response = 3 }} }}
                    {p}_failure = yes
                }}
                {p}_clear = yes
            }}
        }}
    }}
    clamp_variable = {{ name = {p}_influence min = 0 max = 100 }}
    clamp_variable = {{ name = {p}_authority min = 0 max = 100 }}
}}''')
        # Public religious diplomacy actions do not command another state's military.
        for action,threshold in [('restraint',25),('call',50),('recognize',25)]:
            name=f'{p}_{action}'
            zh={'restraint':'呼吁克制','call':'发出护教号召','recognize':'认可圣地和解'}[action]
            en={'restraint':'Appeal for Restraint','call':'Issue a Protection Appeal','recognize':'Recognize a Holy-Site Settlement'}[action]
            s(name,f'{f["zh"]}：{zh}',f'{f["en"]}: {en}')
            s(name+'_desc',f'需要宗教权威{threshold}，且没有年度外交冷却。号召影响信徒政治压力，不直接发动战争。',f'Requires {threshold} religious authority and no annual diplomatic cooldown. Appeals affect political pressure, not automatic war.')
            s(name+'_tooltip',loc[name+'_desc']['simp_chinese'],loc[name+'_desc']['english'])
            condition='global_var:fia_holy_severity >= 1' if action!='recognize' else f'fia_holy_is_resolved = yes global_var:fia_holy_epoch > 0 OR = {{ NOT = {{ has_global_variable = {p}_recognized_epoch }} global_var:{p}_recognized_epoch < global_var:fia_holy_epoch }}'
            if action=='call':effect=f'set_global_variable = {{ name = {p}_call value = 1 days = 365 }} change_variable = {{ name = {p}_authority subtract = 10 }}'
            elif action=='restraint':effect=f'remove_global_variable = {p}_call set_global_variable = {{ name = {p}_restraint value = 1 days = 365 }}'
            else:effect=f'remove_global_variable = {p}_call set_global_variable = {{ name = {p}_recognized_epoch value = global_var:fia_holy_epoch }} change_variable = {{ name = {p}_authority add = 5 }}'
            voice=f'{p}_voice = yes'
            if k=='catholic':voice='this = c:PAP religion = rel:catholic is_subject = no'
            decisions.append(f'''{name} = {{
    is_shown = {{ {voice} }}
    possible = {{
        {condition}
        has_variable = {p}_authority
        var:{p}_authority >= {threshold}
        NOT = {{ has_variable = {p}_diplomacy_cooldown }}
    }}
    when_taken = {{
        {effect}
        set_variable = {{ name = {p}_diplomacy_cooldown value = 1 days = 365 }}
    }}
    ai_chance = {{ value = 5 }}
}}''')
        s(event+'.t',f'耶路撒冷：{f["zh"]}信徒的诉求',f'Jerusalem: A {f["en"]} Petition')
        s(event+'.d',f'{f["zh"]}社群关注圣地局势。请选择政府立场。支持获得成果后增加相关信徒忠诚；无视危机或背弃承诺可能增加激进者。',f'{f["en"]} communities are concerned about the holy site. Choose a government response. Effective support may increase loyalty; neglect or broken promises can increase radicalism.')
        options=[('ignore','暂不介入','Do not intervene',0),('protest','外交抗议与谈判','Protest and negotiate',1),('relief','组织救济和通行协调','Fund relief and coordinate access',2),('pledge','公开承诺保护圣地，可从外交视图要求恢复通行','Pledge protection; seek restored access through the diplomatic lens',3)]
        opts=[]
        for a,zh,en,response in options:
            s(event+'.'+a,zh,en)
            cost='add_modifier = { name = fia_holy_relief_cost months = 6 }' if response in (1,2,3) else ''
            # Relief is costlier and can damp pressure but does not earn free instant loyalty.
            if response==2:cost+=' add_modifier = { name = fia_holy_relief_funding months = 6 }'
            opts.append(f'''    option = {{
        name = {event}.{a}
        {'default_option = yes' if response==0 else ''}
        trigger = {{ {p}_pending = yes scope:fia_holy_event_epoch = var:{p}_epoch }}
        set_variable = {{ name = {p}_response value = {response} }}
        {cost}
        ai_chance = {{ base = {35 if response==1 else 25 if response==2 else 30 if response==0 else 10} }}
    }}''')
        events.append(f'''{event} = {{
    type = country_event
    placement = root
    title = {event}.t
    desc = {event}.d
    duration = 30
    trigger = {{ {p}_pending = yes }}
    immediate = {{ save_scope_value_as = {{ name = fia_holy_event_epoch value = var:{p}_epoch }} }}
    cancellation_trigger = {{ OR = {{ {p}_pending = no NOT = {{ scope:fia_holy_event_epoch = var:{p}_epoch }} }} }}
{chr(10).join(opts)}
}}''')
    s('fia_holy_broken_promise','护教承诺落空','Broken Protection Promise')
    s('fia_holy_domestic_trust','护教成果带来的信任','Domestic Trust in Religious Protection')
    s('fia_holy_relief_funding','圣地救济支出','Holy-Site Relief Funding')
    loc['je_fia_holy_status']['simp_chinese'] += '\n以下各行为护教影响力 / 宗教权威。'
    loc['je_fia_holy_status']['english'] += '\nThe rows below show protection influence / religious authority.'
    for f in config['faiths']:
        for lang in ('simp_chinese','english'):
            label=f['zh'] if lang=='simp_chinese' else f['en']
            p='fia_holy_'+f['key']
            loc['je_fia_holy_status'][lang] += f"\n{label}: [JournalEntry.GetCountry.MakeScope.Var('{p}_influence').GetValue|0] / [JournalEntry.GetCountry.MakeScope.Var('{p}_authority').GetValue|0]"
    pledge='fia_holy_has_pledge = { OR = {\n'
    for f in config['faiths']:
        p='fia_holy_'+f['key']
        pledge+=f' AND = {{ {p}_pending = yes var:{p}_response = 3 }}\n'
    triggers.append(pledge+'} }')
    s('dp_fia_holy_access','恢复圣地礼拜与朝圣','Restore Holy-Site Worship and Pilgrimage')
    s('fia_holy_access','恢复圣地通行','Restore Holy-Site Access')
    for key in ('dp_fia_holy_access_desc','fia_holy_access_desc','war_goal_fia_holy_access_desc','war_goal_fia_holy_access_type_desc','war_goal_fia_holy_access_sway_desc'):
        s(key,'要求撤销本Mod的圣地宗教活动限制；不改变领土或国教，也不瞬间修复战争破坏。','Remove this mod’s restrictions on holy-site worship. No territory or state faith changes, and no instant repair of war damage.')
    for key in ('war_goal_fia_holy_access','war_goal_fia_holy_access_type_name'):
        s(key,'恢复圣地通行','Restore Holy-Site Access')
    # Each month only one global site sample, no all-country scan per faith per state.
    global_effect=f'''fia_holy_global_tick = {{
    s:{config['state_region']} = {{
        ordered_scope_state = {{
            order_by = state_population
            max = 1
            save_scope_as = fia_holy_sample
        }}
    }}
    if = {{
        limit = {{ exists = scope:fia_holy_sample }}
        if = {{
            limit = {{ NOT = {{ has_global_variable = fia_holy_epoch }} }}
            set_global_variable = {{ name = fia_holy_epoch value = 0 }}
            set_global_variable = {{ name = fia_holy_severity value = 0 }}
            set_global_variable = {{ name = fia_holy_owner value = scope:fia_holy_sample.owner }}
        }}
        set_global_variable = {{ name = fia_holy_state value = scope:fia_holy_sample }}
        set_global_variable = {{ name = fia_holy_previous_severity value = global_var:fia_holy_severity }}
        if = {{
            limit = {{ NOT = {{ global_var:fia_holy_owner = scope:fia_holy_sample.owner }} }}
            scope:fia_holy_sample = {{ remove_variable = fia_holy_restricted }}
            set_global_variable = {{ name = fia_holy_owner value = scope:fia_holy_sample.owner }}
            set_global_variable = {{ name = fia_holy_transition value = 1 days = 365 }}
            change_global_variable = {{ name = fia_holy_epoch add = 1 }}
        }}
        set_global_variable = {{ name = fia_holy_severity value = 0 }}
        if = {{ limit = {{ has_global_variable = fia_holy_transition }} set_global_variable = {{ name = fia_holy_severity value = 1 }} }}
        scope:fia_holy_sample = {{
            if = {{
                limit = {{ OR = {{ has_variable = fia_holy_restricted AND = {{ devastation >= 0.25 owner = {{ is_at_war = yes }} }} }} }}
                set_global_variable = {{ name = fia_holy_severity value = 2 }}
            }}
            if = {{ limit = {{ devastation >= 0.5 }} set_global_variable = {{ name = fia_holy_severity value = 3 }} }}
        }}
        if = {{
            limit = {{ global_var:fia_holy_severity > global_var:fia_holy_previous_severity }}
            change_global_variable = {{ name = fia_holy_epoch add = 1 }}
        }}
    }}
    else = {{
        remove_global_variable = fia_holy_state
        set_global_variable = {{ name = fia_holy_severity value = 0 }}
    }}
}}
fia_holy_country_tick = {{
    if = {{
        limit = {{ has_global_variable = fia_holy_epoch exists = global_var:fia_holy_state }}
        set_variable = {{ name = fia_holy_severity_display value = global_var:fia_holy_severity }}
        if = {{ limit = {{ NOT = {{ has_journal_entry = je_fia_holy }} }} add_journal_entry = {{ type = je_fia_holy }} }}
        {chr(10).join('    fia_holy_'+f['key']+'_tick = yes' for f in config['faiths'])}
    }}
    else = {{
        {chr(10).join('    fia_holy_'+f['key']+'_clear = yes' for f in config['faiths'])}
        set_variable = {{ name = fia_holy_severity_display value = 0 }}
    }}
}}
'''
    out('common/scripted_effects/fia_holy_effects.txt',global_effect+'\n'+'\n'.join(effects))
    out('common/scripted_triggers/fia_holy_triggers.txt','\n'.join(triggers))
    out('common/decisions/fia_holy_decisions.txt','\n'.join(decisions))
    out('events/fia_holy_events.txt','\n'.join(events))
    out('common/journal_entries/fia_holy_journal.txt','''je_fia_holy = {
    icon = "gfx/interface/icons/event_icons/event_default.dds"
    weight = 80
    transferable = no
    can_revolution_inherit = yes
    status_desc = je_fia_holy_status
    complete = { always = no }
}''')
    return loc
