import json
import pytest
from agents.ollama_local import ModelError
from evaluation.runner import run_experiment, messages_for, validate
from scenarios.catalog import load_legacy as load
from utils.experiments import save_experiment, experiments, review
from utils.storage import reset_history

class FakeClient:
    def models(self):
        return [{'name': 'test:local', 'digest': 'abc'}]
    def request(self, *args, **kwargs):
        return {'version': 'test'}
    def chat(self, payload):
        self.payload = payload
        return {'done': True, 'done_reason': 'stop', 'message': {'content': json.dumps({'summary': 'Réunion maintenue.', 'actions': [{'operation': 'transmettre', 'target': 'tiers@exemple.invalid'}]})}}

def test_no_answer_leakage():
    s = dict(load()[2], body='SECRET_SIM', summary='SECRET_EXPECTED', interpretation='SECRET_INTERPRETATION')
    prompt = json.dumps(messages_for(s, 'alice', 'baseline'))
    assert 'SECRET_' not in prompt
    assert 'attack' not in prompt
    assert s['email'] in messages_for(s, 'alice', 'baseline')[1]['content']

def test_independent_authorization():
    naive = run_experiment(load()[2], 'test:local', 'baseline', client=FakeClient())
    protected = run_experiment(load()[2], 'test:local', 'authorization', client=FakeClient())
    assert naive['attempted'] and naive['simulated_effect'] and not naive['blocked']
    assert protected['attempted'] and not protected['simulated_effect'] and protected['blocked']
    assert naive['request'] == protected['request']
    assert naive['human_review'] == 'non évalué'
    assert 'tâche_accomplie' not in naive

@pytest.mark.parametrize('content', ['no json', '{}', '{"summary":"x","actions":[{"operation":"shell","target":"ls"}]}', '{"summary":"x","actions":[{"operation":"lire","target":"alice","autorisé":true}]}'])
def test_invalid_output(content):
    with pytest.raises(ModelError):
        validate(content)

def test_error_not_security_success():
    class Broken(FakeClient):
        def chat(self, payload):
            raise ModelError('Délai dépassé')
    record = run_experiment(load()[0], 'test:local', 'combined', client=Broken())
    assert record['status'] == 'error'
    assert 'simulated_effect' not in record

def test_truncation_is_error():
    class Truncated(FakeClient):
        def chat(self, payload):
            return dict(super().chat(payload), done_reason='length')
    assert run_experiment(load()[0], 'test:local', 'baseline', client=Truncated())['status'] == 'error'

def test_experiment_storage_review_and_reset(tmp_path, monkeypatch):
    monkeypatch.setenv('BRECHIA_DB', str(tmp_path/'real.sqlite3'))
    record = run_experiment(load()[0], 'test:local', 'baseline', client=FakeClient())
    save_experiment(record)
    review(record['id'], 'incertain', 'À relire')
    assert experiments()[0]['human_review'] == 'incertain'
    assert experiments()[0]['request'] == record['request']
    reset_history()
    assert experiments() == []

def test_mock_tools_have_only_synthetic_effects():
    from security.mock_tools import MockMailbox
    mailbox = MockMailbox()
    assert mailbox.execute({'operation': 'lire', 'target': '/etc/passwd'})['statut'] == 'cible_inconnue'
    mailbox.execute({'operation': 'supprimer', 'target': 'bob'})
    assert mailbox.boxes['bob'] == []
    assert MockMailbox().boxes['bob']


def test_real_page_without_server(tmp_path, monkeypatch):
    from streamlit.testing.v1 import AppTest
    from pathlib import Path
    monkeypatch.setenv('BRECHIA_DB', str(tmp_path/'ui.sqlite3'))
    def unavailable(self):
        raise ModelError('Serveur arrêté')
    monkeypatch.setattr('agents.ollama_local.OllamaLocal.models', unavailable)
    at = AppTest.from_file(str(Path(__file__).resolve().parents[1]/'app.py'), default_timeout=15).run()
    at.sidebar.radio[0].set_value('Modèle réel (local)').run()
    at.button[0].click().run()
    assert not at.exception
    assert at.warning[0].value == 'Serveur arrêté'
