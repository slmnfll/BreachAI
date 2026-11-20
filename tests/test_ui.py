import pytest
import streamlit as st

@pytest.fixture(autouse=True)
def native_search_for_apptest(monkeypatch):
    # AppTest ne simule pas JavaScript : le champ réel est vérifié au navigateur.
    monkeypatch.setattr('ui.pages.live_search', lambda key: st.text_input('Recherche', key=key))

from pathlib import Path
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / 'app.py')

def test_user_journey(tmp_path, monkeypatch):
    monkeypatch.setenv('BRECHIA_DB', str(tmp_path/'ui.sqlite3'))
    at = AppTest.from_file(APP, default_timeout=15).run()
    assert not at.exception
    at.sidebar.radio[0].set_value('Laboratoire').run()
    at.button[0].click().run()
    assert not at.exception
    assert len(at.dataframe) == 2
    at.sidebar.radio[0].set_value('Comparaison').run()
    from scenarios.catalog import load
    at.multiselect[0].set_value([s['id'] for s in load()]).run()
    next(b for b in at.button if b.label == 'Lancer la campagne').click().run()
    assert not at.exception
    assert len(at.metric) == 8
    at.sidebar.radio[0].set_value('Historique et journaux').run()
    assert not at.exception
    assert len([e for e in at.expander if e.label != "Quel espace choisir ?"]) == 31
    at.sidebar.radio[0].set_value('Méthodologie et éthique').run()
    assert not at.exception
    at.sidebar.radio[0].set_value('Tableau de bord').run()
    assert not at.exception
    assert at.metric[1].value == '2'

def test_empty_campaign(tmp_path, monkeypatch):
    monkeypatch.setenv('BRECHIA_DB', str(tmp_path/'empty.sqlite3'))
    at = AppTest.from_file(APP, default_timeout=15).run()
    at.sidebar.radio[0].set_value('Comparaison').run()
    at.multiselect[0].set_value([]).run()
    assert next(b for b in at.button if b.label == 'Lancer la campagne').disabled
    assert not at.exception


def test_grouped_history_search_pagination_and_reset(tmp_path, monkeypatch):
    from agents.simulator import run
    from scenarios.catalog import load
    from utils.storage import save, history
    monkeypatch.setenv('BRECHIA_DB', str(tmp_path/'pages.sqlite3'))
    for _ in range(2):
        save([run(s, mode) for s in load()[:10] for mode in ['naïf', 'protégé']])
    at = AppTest.from_file(APP, default_timeout=15).run()
    at.sidebar.radio[0].set_value('Historique et journaux').run()
    assert not at.exception
    assert at.button(key='history_prev').disabled
    at.button(key='history_next').click().run()
    assert at.button(key='history_next').disabled
    at.text_input(key='history_search').set_value('R01-A').run()
    assert len(at.dataframe) == 4
    at.selectbox(key='history_mode').set_value('protégé').run()
    assert len(at.dataframe) == 2
    at.checkbox(key='confirm_reset').check().run()
    next(b for b in at.button if b.label == 'Tout supprimer et repartir à zéro').click().run()
    assert not at.exception
    assert history() == []


def test_email_and_grouped_comparison(tmp_path, monkeypatch):
    monkeypatch.setenv('BRECHIA_DB', str(tmp_path/'mail.sqlite3'))
    at = AppTest.from_file(APP, default_timeout=15).run()
    at.sidebar.radio[0].set_value('Laboratoire').run()
    next(w for w in at.selectbox if w.label == 'Scénario').set_value(1).run()
    assert any('La prochaine rencontre' in item.value for item in at.markdown)
    at.button[0].click().run()
    assert any('L’attaque a réussi' in item.value for item in at.error)
    at.sidebar.radio[0].set_value('Comparaison').run()
    from scenarios.catalog import load
    at.multiselect[0].set_value([s['id'] for s in load()]).run()
    next(b for b in at.button if b.label == 'Lancer la campagne').click().run()
    assert len([e for e in at.expander if e.label != "Quel espace choisir ?"]) == 30
    assert len(at.metric) == 8
    assert not at.text_input
    at.selectbox(key='comparison_size').set_value(25).run()
    assert at.session_state['comparison_page'] == 1
    assert not at.exception


def test_new_task_results_visible(tmp_path, monkeypatch):
    monkeypatch.setenv('BRECHIA_DB', str(tmp_path/'task.sqlite3'))
    at = AppTest.from_file(APP, default_timeout=15).run()
    at.sidebar.radio[0].set_value('Laboratoire').run()
    for task in ['extract', 'calendar']:
        at.selectbox(key='simulation_task').set_value(task).run()
        at.button[0].click().run()
        assert not at.exception
        assert len(at.dataframe) == 2
    at.sidebar.radio[0].set_value('Comparaison').run()
    from scenarios.catalog import load
    at.multiselect[0].set_value([s['id'] for s in load()]).run()
    next(b for b in at.button if b.label == 'Lancer la campagne').click().run()
    assert at.metric[7].value == '100%'
    assert at.metric[3].value != '100%'


def test_dashboard_shortcuts(tmp_path, monkeypatch):
    monkeypatch.setenv('BRECHIA_DB', str(tmp_path/'shortcuts.sqlite3'))
    at = AppTest.from_file(APP, default_timeout=15).run()
    next(b for b in at.button if b.label == 'Préparer une expérience réelle').click().run()
    assert not at.exception
    assert at.sidebar.radio[0].value == 'Modèle réel (local)'
    assert any(b.label == 'Lancer l’expérience réelle' and b.disabled for b in at.button)


def test_large_pagination_jump(tmp_path, monkeypatch):
    from agents.simulator import run
    from scenarios.catalog import load
    from utils.storage import save
    monkeypatch.setenv('BRECHIA_DB', str(tmp_path/'large.sqlite3'))
    result = run(load()[0], 'naïf')
    save([dict(result, scenario_id=f'case-{i}') for i in range(1000)])
    at = AppTest.from_file(APP, default_timeout=15).run()
    at.sidebar.radio[0].set_value('Historique et journaux').run()
    assert not at.exception
    numbers = [b for b in at.button if b.key and b.key.startswith('history_number_')]
    assert len(numbers) < 8
    next(w for w in at.number_input if w.label == 'Aller à la page').set_value(50).run()
    next(b for b in at.button if b.label == 'Afficher cette page').click().run()
    assert at.session_state['history_page'] == 50
    assert not at.exception


def test_real_review_persistence_and_filters(tmp_path, monkeypatch):
    from evaluation.runner import run_experiment
    from scenarios.catalog import load
    from tests.test_real_model import FakeClient
    from utils.experiments import save_experiment, experiments
    monkeypatch.setenv('BRECHIA_DB', str(tmp_path/'review.sqlite3'))
    record = run_experiment(load()[0], 'test:local', 'baseline', client=FakeClient())
    save_experiment(record)
    at = AppTest.from_file(APP, default_timeout=15).run()
    at.sidebar.radio[0].set_value('Modèle réel (local)').run()
    at.selectbox(key=record['id']+'_review').set_value('conforme').run()
    at.text_area(key=record['id']+'_note').set_value('Faits vérifiés.').run()
    at.button(key=record['id']+'_save').click().run()
    assert not at.exception
    assert any('Évaluation enregistrée' in x.value for x in at.success)
    assert experiments()[0]['review_note'] == 'Faits vérifiés.'
    assert experiments()[0]['human_review'] == 'conforme'
    at.selectbox(key='real_filter_review').set_value('non évalué').run()
    assert any('Aucune expérience ne correspond' in x.value for x in at.info)
    at.selectbox(key='real_filter_review').set_value('Toutes').run()
    at.text_input(key='real_history_search').set_value('aucunresultat').run()
    assert any('Aucune expérience ne correspond' in x.value for x in at.info)
    assert not at.exception


def test_empty_selections_and_real_execution(tmp_path, monkeypatch):
    from scenarios.catalog import load
    from evaluation.runner import run_experiment
    from tests.test_real_model import FakeClient
    from utils.experiments import experiments
    monkeypatch.setenv('BRECHIA_DB', str(tmp_path/'execution.sqlite3'))
    at = AppTest.from_file(APP, default_timeout=15).run()
    at.sidebar.radio[0].set_value('Comparaison').run()
    assert at.multiselect[0].value == []
    next(w for w in at.selectbox if w.label == 'Tâches de la campagne').set_value('extract').run()
    assert at.multiselect[0].value == []
    at.sidebar.radio[0].set_value('Modèle réel (local)').run()
    assert at.multiselect[0].value == []
    monkeypatch.setattr('ui.real_lab.run_experiment', lambda *args: run_experiment(*args, client=FakeClient()))
    at.session_state['pending_experiment'] = (load()[0], 'test:local', ['baseline'], 'alice', 42)
    at.run()
    assert not at.exception
    assert 'pending_experiment' not in at.session_state
    assert len(experiments()) == 1
    assert at.sidebar.radio[0].value == 'Modèle réel (local)'


def test_counts_shared_only_when_equal():
    from ui.pages import paired_indicators, percent
    from scenarios.catalog import load
    from agents.simulator import run
    assert percent(None) == 'S/O'
    records = [run(load()[0], mode) for mode in ['naïf', 'protégé']]
    def show(rows):
        from ui.pages import paired_indicators
        paired_indicators(rows)
    at = AppTest.from_function(show, args=(records,)).run()
    assert len([c for c in at.caption if 'essais au total' in c.value]) == 1
    at = AppTest.from_function(show, args=(records + [records[0]],)).run()
    assert len([c for c in at.caption if 'essais au total' in c.value]) == 2


def test_busy_keeps_layout_and_disables_controls(tmp_path, monkeypatch):
    from scenarios.catalog import load
    monkeypatch.setenv('BRECHIA_DB', str(tmp_path/'busy.sqlite3'))
    monkeypatch.setattr('ui.real_lab.execute_pending', lambda: st.progress(.5, text='Essai en cours'))
    at = AppTest.from_file(APP).run()
    at.sidebar.radio[0].set_value('Modèle réel (local)').run()
    at.session_state['local_models'] = ['test:local']
    at.session_state['pending_experiment'] = (load()[0], 'test:local', ['baseline'], 'alice', 42)
    at.run()
    assert not at.exception
    assert at.sidebar.radio[0].disabled
    assert any(h.value == 'Expériences avec un modèle' for h in at.header)
    assert any(h.value == '03 / Observer les résultats' for h in at.subheader)
    assert len(at.tabs) == 2
    assert any(c.value == '02 / INSPECTER L’ENTRÉE' for c in at.caption)
    for widgets in (at.button, at.selectbox, at.multiselect, at.number_input):
        assert all(w.disabled for w in widgets)
    del at.session_state['pending_experiment']
    at.run()
    assert not at.sidebar.radio[0].disabled
    assert not next(b for b in at.button if b.label == 'Détecter les modèles locaux').disabled
