import unittest
from script_vm import VM, Obj, world, get

def holy():
    vm,host,patron,state=world()
    region=Obj('state_region',states=[state]);vm.objects['s:STATE_PALESTINE']=region
    pope=Obj('country',{'religion':'rel:catholic','is_subject':False,'is_country_alive':True})
    vm.objects['c:PAP']=pope
    host.attrs.update(religion='rel:sunni',shares={'rel:sunni':0.8,'rel:catholic':0.1})
    host.pops=[Obj('pop',{'religion':'rel:sunni','total_size':80000}),Obj('pop',{'religion':'rel:catholic','total_size':10000})]
    state.attrs['devastation']=0
    vm.run('fia_holy_global_tick')
    return vm,host,patron,state

def petition(vm,host,severity=2):
    vm.globals['fia_holy_severity']=severity
    vm.globals['fia_holy_epoch']+=1
    vm.run('fia_holy_country_tick',host)

class HolySiteTests(unittest.TestCase):
    def test_baseline_is_not_a_global_uprising(self):
        vm,host,patron,state=holy();vm.run('fia_holy_country_tick',host)
        self.assertEqual(vm.globals['fia_holy_epoch'],0)
        self.assertNotIn('fia_holy_sunni_age',host.vars)
        self.assertFalse(vm.radicals)
    def test_owner_change_raises_attention_without_assuming_persecution(self):
        vm,host,patron,state=holy();state.attrs['owner']=patron
        vm.run('fia_holy_global_tick')
        self.assertEqual(vm.globals['fia_holy_severity'],1)
        self.assertGreater(vm.globals['fia_holy_epoch'],0)
        self.assertFalse(vm.radicals)
    def test_restrictions_and_severe_damage_raise_different_severities(self):
        vm,host,patron,state=holy();state.vars['fia_holy_restricted']=1
        vm.run('fia_holy_global_tick');self.assertEqual(vm.globals['fia_holy_severity'],2)
        state.attrs['devastation']=0.6
        vm.run('fia_holy_global_tick');self.assertEqual(vm.globals['fia_holy_severity'],3)
    def test_all_related_faiths_include_minority_groups(self):
        vm,host,patron,state=holy();petition(vm,host)
        self.assertIn('fia_holy_sunni_age',host.vars)
        self.assertIn('fia_holy_catholic_age',host.vars)
        self.assertNotIn('fia_holy_jewish_age',host.vars)
    def test_no_immediate_population_reward_for_promise(self):
        vm,host,patron,state=holy();petition(vm,host)
        host.vars['fia_holy_sunni_response']=3
        vm.run('fia_holy_sunni_tick',host)
        self.assertFalse(vm.loyalists);self.assertFalse(vm.radicals)
    def test_broken_promise_is_filtered_and_capped(self):
        vm,host,patron,state=holy();petition(vm,host)
        host.vars['fia_holy_sunni_response']=3
        for _ in range(6):vm.run('fia_holy_sunni_tick',host)
        self.assertEqual(vm.radicals,[(host,'rel:sunni',0.02)])
        self.assertNotIn('fia_holy_sunni_age',host.vars)
        petition(vm,host);host.vars['fia_holy_sunni_response']=3
        for _ in range(6):vm.run('fia_holy_sunni_tick',host)
        self.assertEqual(len(vm.radicals),1)
    def test_restore_rights_then_reward_participants_once(self):
        vm,host,patron,state=holy();petition(vm,host)
        host.vars['fia_holy_sunni_response']=2
        vm.globals['fia_holy_severity']=0
        for _ in range(3):vm.run('fia_holy_sunni_tick',host)
        self.assertEqual(vm.loyalists,[(host,'rel:sunni',0.005)])
        self.assertIn('fia_holy_credibility',host.modifiers)
        for _ in range(6):vm.run('fia_holy_sunni_tick',host)
        self.assertEqual(len(vm.loyalists),1)
    def test_relief_without_resolution_does_not_create_free_loyalty(self):
        vm,host,patron,state=holy();petition(vm,host)
        host.vars['fia_holy_sunni_response']=2
        for _ in range(6):vm.run('fia_holy_sunni_tick',host)
        self.assertFalse(vm.loyalists);self.assertFalse(vm.radicals)
    def test_restrictions_cannot_be_laundered_by_a_lower_cached_severity(self):
        vm,host,patron,state=holy();state.vars['fia_holy_restricted']=1
        petition(vm,host);host.vars['fia_holy_sunni_response']=3
        vm.globals['fia_holy_severity']=1
        for _ in range(6):vm.run('fia_holy_sunni_tick',host)
        self.assertFalse(vm.loyalists)
    def test_restraint_reduces_neglect_but_not_broken_promises(self):
        vm,host,patron,state=holy();petition(vm,host)
        vm.globals['fia_holy_sunni_restraint']=1
        for _ in range(6):vm.run('fia_holy_sunni_tick',host)
        self.assertEqual(vm.radicals,[(host,'rel:sunni',0.0025)])
    def test_later_epoch_invalidates_old_petition_without_penalty(self):
        vm,host,patron,state=holy();petition(vm,host)
        host.vars['fia_holy_sunni_response']=3;host.vars['fia_holy_sunni_age']=5
        vm.globals['fia_holy_epoch']+=1
        vm.run('fia_holy_sunni_tick',host)
        self.assertFalse(vm.radicals);self.assertEqual(host.vars['fia_holy_sunni_response'],0)
    def test_actual_war_delays_promise_deadline_but_not_forever(self):
        vm,host,patron,state=holy();petition(vm,host)
        host.vars['fia_holy_sunni_response']=3;host.attrs['has_war_with']={host}
        for _ in range(7):vm.run('fia_holy_sunni_tick',host)
        self.assertFalse(vm.radicals)
        for _ in range(24):vm.run('fia_holy_sunni_tick',host)
        self.assertEqual(len(vm.radicals),1)
    def test_papal_authority_is_distinct_from_national_influence(self):
        vm,host,patron,state=holy();pope=vm.objects['c:PAP']
        vm.run('fia_holy_catholic_tick',pope)
        self.assertEqual(pope.vars['fia_holy_catholic_authority'],60)
        self.assertEqual(pope.vars['fia_holy_catholic_influence'],10)
        pope.attrs['is_subject']=True
        vm.run('fia_holy_catholic_tick',pope)
        self.assertEqual(pope.vars['fia_holy_catholic_authority'],59)
    def test_war_enforcement_restores_access_without_repair_or_annexation(self):
        vm,host,patron,state=holy();state.vars['fia_holy_restricted']=1;state.attrs['devastation']=0.6
        vm.scopes['target_state']=state
        vm.effect(get(vm.defs['fia_holy_access'],'on_enforced'))
        self.assertNotIn('fia_holy_restricted',state.vars)
        self.assertEqual(state.attrs['devastation'],0.6)
        self.assertIs(state.attrs['owner'],host)
    def test_event_epoch_is_captured_per_event_not_in_mutable_country_storage(self):
        vm,host,patron,state=holy();petition(vm,host)
        event=vm.defs['fia.103']
        vm.scoped(host,vm.effect,get(event,'immediate'))
        old=vm.scopes['fia_holy_event_epoch']
        vm.globals['fia_holy_epoch']+=1
        vm.run('fia_holy_sunni_tick',host)
        self.assertEqual(vm.scopes['fia_holy_event_epoch'],old)
        self.assertTrue(vm.scoped(host,vm.condition,get(event,'cancellation_trigger')))
    def test_missing_site_registry_cancels_without_penalizing(self):
        vm,host,patron,state=holy();petition(vm,host)
        host.vars['fia_holy_sunni_response']=3
        vm.globals.pop('fia_holy_state')
        vm.run('fia_holy_country_tick',host)
        self.assertNotIn('fia_holy_sunni_age',host.vars)
        self.assertFalse(vm.radicals)
    def test_islamic_authority_is_national_not_a_single_pope(self):
        vm,host,patron,state=holy()
        host.groups=[Obj('interest_group',{'group_type':'ig_devout','ig_clout':0.25})]
        self.assertTrue(vm.scoped(host,vm.condition,vm.defs['fia_holy_sunni_voice']))
        self.assertFalse(vm.scoped(host,vm.condition,vm.defs['fia_holy_shiite_voice']))
        host.groups[0].attrs['ig_clout']=0.1
        self.assertFalse(vm.scoped(host,vm.condition,vm.defs['fia_holy_sunni_voice']))
if __name__=='__main__':unittest.main()
