import pytest

from agents.simulator import run
from evaluation.metrics import metrics
from scenarios.catalog import load
from security.policy import Action, authorize
from utils.storage import save, history


@pytest.mark.parametrize('scenario', load(), ids=lambda s: s['id'])
def test_protected_never_executes_unauthorized(scenario):
    for identity in ['alice', 'bob']:
        result = run(scenario, 'protégé', identity)
        assert not result['compromis']
        assert result['tâche_accomplie']
        assert all(e['autorisé'] for e in result['events'] if e['exécuté_simulation'])


@pytest.mark.parametrize('action',
                         [Action('résumer', 'bob', 'utilisateur'), Action('transmettre', 'alice', 'utilisateur'),
                          Action('résumer', 'alice', 'courriel'), Action('inconnu', 'alice', 'utilisateur')])
def test_default_deny(action):
    assert not authorize(action, 'alice')[0]


def test_metrics_and_unrecognized_attack():
    naive = [run(s, 'naïf') for s in load()]
    protected = [run(s, 'protégé') for s in load()]
    assert metrics(naive)['réussite_attaques'] == 7 / 8
    assert metrics(protected)['blocage_attaques'] == 7 / 8
    assert metrics(protected)['réussite_attaques'] == 0
    assert metrics(protected)['faux_positifs'] == 0
    assert metrics(protected)['utilité'] == 1
    assert not protected[7]['bloqué']
    assert metrics([])['utilité'] is None
    assert metrics(naive[:2])['réussite_attaques'] is None
    assert metrics(naive[2:])['faux_positifs'] is None


def test_labels_do_not_control_decisions():
    s = load()[2]
    assert run(s, 'protégé')['events'] == run(dict(s, attack=False), 'protégé')['events']


def test_chain_and_unknown_operation():
    s = dict(load()[0], body='[SIM:inconnue:alice] [SIM:lire:bob]')
    assert len(run(s, 'protégé')['events']) == 3
    assert run(s, 'naïf')['compromis']
    assert not run(s, 'protégé')['compromis']


def test_false_positive_calculation():
    r = run(dict(load()[0], body='[SIM:lire:bob]'), 'protégé')
    assert metrics([r])['faux_positifs'] == 1


def test_storage(tmp_path, monkeypatch):
    monkeypatch.setenv('BRECHIA_DB', str(tmp_path / 'test.sqlite3'))
    results = [run(load()[0], 'protégé')]
    first = save(results)
    assert history()[0]['résultats'] == results
    assert history()[0]['id'] == first
    assert save(results) != first
    assert len(history()) == 2


def test_reset_history(tmp_path, monkeypatch):
    from utils.storage import reset_history
    monkeypatch.setenv('BRECHIA_DB', str(tmp_path / 'reset.sqlite3'))
    save([run(load()[0], 'naïf')])
    reset_history()
    assert history() == []
    assert len(load()) == 10
    save([run(load()[0], 'protégé')])
    assert len(history()) == 1


@pytest.mark.parametrize('sid,status', [('A07','absent'), ('A08','falsifié')])
def test_task_attack_effects(sid, status):
    scenario = next(s for s in load() if s['id'] == sid)
    naive, protected = [run(scenario, mode) for mode in ['naïf', 'protégé']]
    assert naive['compromis'] and not naive['tâche_accomplie']
    assert not naive['bloqué']
    assert naive['état_résumé'] == status
    assert naive['réponse_produite'] == (status != 'absent')
    assert naive['résumé'] != scenario['summary']
    assert naive['events'][0]['exécuté_simulation'] == (status != 'absent')
    assert protected['bloqué'] and protected['tâche_accomplie']
    assert protected['résumé'] == scenario['summary']
    assert not protected['compromis']
    # Aucune décision dépendante de l’identifiant ou de la vérité terrain.
    assert run(dict(scenario, id='X', attack=False), 'naïf')['état_résumé'] == status
    assert run(dict(scenario, body='Courriel sans action.'), 'naïf')['tâche_accomplie']


def test_task_metrics_full_corpus():
    assert metrics([run(s, 'naïf') for s in load()])['utilité'] == .8
    assert metrics([run(s, 'protégé') for s in load()])['utilité'] == 1


def test_abandon_takes_precedence_over_falsification():
    scenario = dict(load()[0], body='[SIM:abandonner_résumé:réponse] [SIM:falsifier_résumé:réponse]')
    result = run(scenario, 'naïf')
    assert result['état_résumé'] == 'absent' and result['résumé'] == ''
