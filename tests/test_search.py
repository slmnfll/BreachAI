from agents.simulator import PATTERN
from scenarios.catalog import load
from utils.search import search_results

ROWS = [
    dict(scenario_id='A01', titre='Fausse assistance technique', identité='alice', date_utc='2026-11-19T19:00:00+00:00',
         mode='naïf'),
    dict(scenario_id='T02', titre='Discussion de sécurité', identité='bob', date_utc='2026-11-20T20:00:00+00:00',
         mode='protégé')]


def test_search_identity_date_id_and_accents():
    for term in ['A 01', 'ALICE', 'alice 2026-11-19', 'assistance']:
        assert search_results(ROWS, term)[0] == ROWS[:1]
    assert search_results(ROWS, 'T 02 securite')[0] == ROWS[1:]
    assert search_results(ROWS, '2026-11-21')[0] == []
    assert search_results(ROWS, '')[0] == ROWS


def test_approximate_search_is_labelled():
    found, near = search_results(ROWS, 'assistnce')
    assert found == ROWS[:1] and near
    assert search_results(ROWS, 'A99')[0] == []


def test_natural_messages_and_simulated_mapping():
    for scenario in load():
        assert len(scenario['email'].split('\n\n')) >= 4
        assert '[SIM:' not in scenario['email']
        assert scenario['excerpt'] in scenario['email']
        assert scenario['interpretation']
    assert len(PATTERN.findall(load()[6]['body'])) == 2
    assert PATTERN.findall(load()[7]['body']) == []
