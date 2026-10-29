import unittest
from script_vm import world, Obj, get

class GameplayTests(unittest.TestCase):
    def bind(self):
        vm,host,patron,state=world()
        vm.run('fia_offer_patronage',state)
        self.assertIs(patron.vars['fia_mission_state'],state)
        self.assertIs(state.vars['fia_patron'],patron)
        return vm,host,patron,state
    def test_petition_acceptance_and_sixty_months_of_compliance(self):
        vm,host,patron,state=self.bind()
        vm.run('fia_send_request')
        self.assertIs(host.vars['fia_request_from'],patron)
        vm.run('fia_accept_request',host)
        self.assertIn('fia_monitoring_cost',patron.modifiers)
        self.assertIn('fia_local_guarantees',state.modifiers)
        for _ in range(59):vm.run('fia_monthly_state',state)
        self.assertEqual(state.vars['fia_accord_months'],59)
        self.assertNotIn('fia_diplomatic_credit',patron.modifiers)
        vm.run('fia_monthly_state',state)
        self.assertNotIn('fia_accord_months',state.vars)
        self.assertNotIn('fia_monitoring_cost',patron.modifiers)
        self.assertIn('fia_diplomatic_credit',patron.modifiers)
        self.assertNotIn('fia_mission_state',patron.vars)
        self.assertEqual(state.vars['fia_tension'],0)
        self.assertEqual(vm.radicals,[(state,'orthodox',-0.01)]*5)
    def test_rejection_then_wargoal_enforcement(self):
        vm,host,patron,state=self.bind();vm.run('fia_send_request');vm.run('fia_reject_request',host)
        self.assertTrue(vm.condition(vm.defs['fia_can_escalate']))
        vm.scopes.update(target_state=state,target_country=host)
        vm.effect(get(vm.defs['fia_religious_guarantees'],'on_enforced'))
        self.assertEqual(state.vars['fia_accord_months'],0)
        self.assertIn('fia_on_accord',patron.vars)
        self.assertFalse(vm.condition(vm.defs['fia_can_escalate']))
        state.vars['fia_accord_months']=12
        vm.effect(get(vm.defs['fia_religious_guarantees'],'on_enforced'))
        self.assertEqual(state.vars['fia_accord_months'],12)
    def test_revocation_reopens_reason_without_awarding_credit(self):
        vm,host,patron,state=self.bind();vm.run('fia_begin_accord',state);vm.run('fia_breach_accord',state)
        self.assertEqual(state.vars['fia_tension'],80)
        self.assertNotIn('fia_accord_months',state.vars)
        self.assertIn('fia_authorized',patron.vars)
        self.assertNotIn('fia_monitoring_cost',patron.modifiers)
        self.assertNotIn('fia_diplomatic_credit',patron.modifiers)
    def test_withdrawal_preserves_guarantees_but_not_patron_reward(self):
        vm,host,patron,state=self.bind();vm.run('fia_begin_accord',state);vm.run('fia_clear_mission')
        self.assertIn('fia_accord_months',state.vars)
        self.assertNotIn('fia_patron',state.vars)
        for _ in range(60):vm.run('fia_monthly_state',state)
        self.assertNotIn('fia_diplomatic_credit',patron.modifiers)
    def test_ownership_transfer_invalidates_mission_and_removes_benefits(self):
        vm,host,patron,state=self.bind();vm.run('fia_begin_accord',state)
        state.attrs['owner']=Obj('country',{'country_type':'recognized','laws':set()})
        vm.run('fia_monthly_state',state)
        self.assertNotIn('fia_local_guarantees',state.modifiers)
        self.assertFalse(vm.condition(vm.defs['fia_mission_valid']))
        vm.run('fia_monthly_country')
        self.assertNotIn('fia_mission_state',patron.vars)
        self.assertNotIn('fia_monitoring_cost',patron.modifiers)
    def test_secular_policy_and_peaceful_localities_do_not_seed_cases(self):
        vm,host,patron,state=world();state.vars.clear()
        host.attrs['laws']=set();vm.run('fia_monthly_state',state)
        self.assertNotIn('fia_tension',state.vars)
        host.attrs['laws']={'law_type:law_state_religion'};state.attrs['turmoil']=0
        vm.run('fia_monthly_state',state);self.assertNotIn('fia_tension',state.vars)
    def test_small_minority_cannot_seed_case(self):
        vm,host,patron,state=world();state.vars.clear();state.attrs['shares']['orthodox']=0.09
        vm.run('fia_monthly_state',state);self.assertNotIn('fia_tension',state.vars)
    def test_no_state_faith_or_interest_means_no_patron(self):
        for attr,value in [('religion','catholic'),('interests',set()),('is_subject',True)]:
            with self.subTest(attr=attr):
                vm,host,patron,state=world();patron.attrs[attr]=value
                vm.run('fia_offer_patronage',state)
                self.assertNotIn('fia_patron',state.vars)
    def test_tension_bounds_and_reform(self):
        vm,host,patron,state=world(99);vm.run('fia_update_tension',state)
        self.assertEqual(state.vars['fia_tension'],100)
        host.attrs['laws']=set();state.vars['fia_tension']=1
        vm.run('fia_update_tension',state);self.assertEqual(state.vars['fia_tension'],0)
    def test_repression_targets_case_faith_and_marks_incident(self):
        vm,host,patron,state=world(95);vm.run('fia_repress',state)
        self.assertEqual(state.vars['fia_tension'],100)
        self.assertEqual(vm.radicals,[(state,'orthodox',0.02)])
        self.assertIn('fia_incident',state.vars)
    def test_native_goal_survives_expired_reason_fatigue_and_demographic_change(self):
        vm,host,patron,state=self.bind();vm.scopes.update(target_country=host,target_state=state)
        patron.vars.update(fia_fatigue=100,fia_play_started=1)
        patron.vars.pop('fia_authorized',None);state.attrs['shares']['orthodox']=0
        state.vars['fia_tension']=0
        self.assertTrue(vm.condition(get(vm.defs['fia_religious_guarantees'],'valid')))
        self.assertFalse(vm.condition(get(vm.defs['fia_religious_guarantees'],'possible')))
        vm.run('fia_monthly_state',state)
        self.assertIn('fia_case_owner',state.vars)
        self.assertTrue(vm.condition(vm.defs['fia_mission_valid']))
    def test_destroyed_patron_does_not_reserve_case_forever(self):
        vm,host,patron,state=self.bind();patron.attrs['is_country_alive']=False
        vm.run('fia_monthly_state',state)
        self.assertNotIn('fia_patron',state.vars)
    def test_request_timeout_rejects_and_cleans_inbox(self):
        vm,host,patron,state=self.bind();vm.run('fia_send_request')
        for _ in range(3):vm.run('fia_monthly_country',host)
        self.assertNotIn('fia_request_from',host.vars)
        self.assertIn('fia_authorized',patron.vars)
    def test_expired_mission_cannot_leave_pending_request(self):
        vm,host,patron,state=self.bind();vm.run('fia_send_request');patron.vars['fia_mission_age']=23
        vm.run('fia_monthly_country')
        self.assertNotIn('fia_request_from',host.vars)
        self.assertNotIn('fia_patron',state.vars)
    def test_native_play_gate_works_before_state_selection(self):
        vm,host,patron,state=self.bind();patron.vars['fia_authorized']=1
        vm.scopes['target_country']=host
        self.assertTrue(vm.condition(vm.defs['fia_authorizes_target']))
        self.assertFalse(vm.condition(vm.defs['fia_authorizes_goal']))
        vm.scopes['target_state']=state
        self.assertTrue(vm.condition(vm.defs['fia_authorizes_goal']))
    def test_truce_blocks_new_escalation(self):
        vm,host,patron,state=self.bind();patron.vars['fia_authorized']=1
        patron.attrs['has_truce_with']={host}
        self.assertFalse(vm.condition(vm.defs['fia_can_escalate']))
    def test_fatigue_only_grows_in_related_war(self):
        vm,host,patron,state=self.bind();patron.vars['fia_fatigue']=10
        patron.attrs.update(is_at_war=True,has_war_with={host})
        vm.run('fia_monthly_country');self.assertEqual(patron.vars['fia_fatigue'],12)
        patron.attrs['has_war_with']=set();vm.run('fia_monthly_country')
        self.assertEqual(patron.vars['fia_fatigue'],10)
    def test_stale_request_cannot_accept_new_owners_case(self):
        vm,host,patron,state=self.bind();vm.run('fia_send_request')
        state.attrs['owner']=patron
        vm.run('fia_accept_request',host)
        self.assertNotIn('fia_accord_months',state.vars)
        self.assertNotIn('fia_request_from',host.vars)
if __name__=='__main__':unittest.main()
