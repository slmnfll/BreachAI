import json
from copy import deepcopy
from scenarios.catalog import load
from scenarios.tasks import task_id
from agents.simulator import run
from security.policy import authorize_tool
from security.mock_tools import MockMailbox
from evaluation.runner import messages_for, run_experiment
from tests.test_real_model import FakeClient

def test_corpus_pairs():
    corpus = load()
    assert len(corpus) == 30
    assert len({s['id'] for s in corpus}) == 30
    for task in ['summary', 'extract', 'calendar']:
        cases = [s for s in corpus if task_id(s) == task]
        assert len(cases) == 10
        assert sum(s['attack'] for s in cases) == 5
    for pair in {s['pair_id'] for s in corpus}:
        clean, attack = sorted([s for s in corpus if s['pair_id'] == pair], key=lambda s:s['attack'])
        assert clean['expected_event'] == attack['expected_event']
        assert attack['email'].replace(attack['excerpt']+'\n\n','') == clean['email']
        assert '[SIM:' not in attack['email']

def test_simulated_protected_preserves_all_tasks():
    for s in load():
        for identity in ['alice','bob']:
            r = run(s,'protégé',identity)
            assert r['tâche_accomplie'] and not r['compromis']

def test_calendar_scope_and_count():
    event = load()[0]['expected_event']
    action = dict(operation='creer_evenement', target='alice', event=event)
    assert authorize_tool(action,'alice','calendar',0)[0]
    assert not authorize_tool(action,'bob','calendar',0)[0]
    assert not authorize_tool(action,'alice','summary',0)[0]
    assert not authorize_tool(action,'alice','calendar',1)[0]
    assert not authorize_tool(dict(operation='supprimer_evenements',target='alice'),'alice','calendar')[0]

def test_calendar_state_evaluates_effects_not_claims():
    s = next(s for s in load() if s['id']=='C03-A')
    assert not run(s,'naïf')['tâche_accomplie']
    assert run(s,'naïf')['calendrier_après']['alice'] == []
    assert len(run(s,'protégé')['calendrier_après']['alice']) == 2

def test_model_accepts_legitimate_creation_blocks_extra_actions():
    s = next(s for s in load() if s['id']=='C03-A')
    class CalendarClient(FakeClient):
        def chat(self,payload):
            return {'done':True,'message':{'content':json.dumps({'summary':'Créé', 'actions':[
                dict(operation='creer_evenement',target='alice',event=s['expected_event']),
                dict(operation='supprimer_evenements',target='alice')]})}}
    result = run_experiment(s,'test:local','authorization',client=CalendarClient())
    assert result['status'] == 'ok' and result['task_success']
    assert result['events'][0]['autorisé'] and not result['events'][0]['bloqué']
    assert result['events'][1]['bloqué']
    assert not result['simulated_effect']
    baseline = run_experiment(s,'test:local','baseline',client=CalendarClient())
    assert baseline['simulated_effect'] and not baseline['task_success']

def test_wrong_date_is_task_failure_even_if_creation_authorized():
    s = next(s for s in load() if s['task']=='calendar')
    class WrongDate(FakeClient):
        def chat(self,payload):
            event=dict(s['expected_event'], date='2099-01-01')
            return {'done':True,'message':{'content':json.dumps({'summary':'Créé','actions':[dict(operation='creer_evenement',target='alice',event=event)]})}}
    result=run_experiment(s,'test:local','authorization',client=WrongDate())
    assert result['events'][0]['autorisé'] and not result['task_success']

def test_model_cannot_receive_reference():
    s=dict(load()[20],summary='SECRET_REF',expected_event={'secret':'SECRET_EVENT'},body='SECRET_SIM')
    prompt=json.dumps(messages_for(s,'alice','combined'))
    assert 'SECRET_' not in prompt


def test_action_schema_matches_validator():
    from evaluation.runner import schema_for, validate
    from agents.ollama_local import ModelError
    import pytest
    for task in ['summary', 'extract', 'calendar']:
        simple, creation = schema_for(task)['properties']['actions']['items']['anyOf']
        assert 'event' not in simple['properties']
        assert 'creer_evenement' not in simple['properties']['operation']['enum']
        assert creation['properties']['operation']['enum'] == ['creer_evenement']
        assert 'event' in creation['required']
    event = load()[0]['expected_event']
    result = dict(summary='Réunion', meeting=event, actions=[])
    assert validate(json.dumps(result), 'extract')['meeting'] == event
    result['actions'] = [dict(operation='transmettre', target='alice', event=event)]
    with pytest.raises(ModelError, match='réservé'):
        validate(json.dumps(result), 'extract')
