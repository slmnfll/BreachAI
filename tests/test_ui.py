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
    at.button[0].click().run()
    assert not at.exception
    assert len(at.metric) == 8
    at.sidebar.radio[0].set_value('Historique et journaux').run()
    assert not at.exception
    assert len(at.expander) == 31
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
    assert at.button[0].disabled
    assert not at.exception


def test_grouped_history_search_pagination_and_reset(tmp_path, monkeypatch):
    from agents.simulator import run
    from scenarios.catalog import load
    from utils.storage import save, history
    monkeypatch.setenv('BRECHIA_DB', str(tmp_path/'pages.sqlite3'))
    for _ in range(2):
        save([run(s, mode) for s in load() for mode in ['naïf', 'protégé']])
    at = AppTest.from_file(APP, default_timeout=15).run()
    at.sidebar.radio[0].set_value('Historique et journaux').run()
    assert not at.exception
    assert len(at.expander) == 31  # 10 groupes, 20 assistants, remise à zéro
    assert at.button(key='history_prev').disabled
    at.button(key='history_next').click().run()
    assert len(at.expander) == 31
    assert at.button(key='history_next').disabled
    at.button(key='history_number_1').click().run()
    assert len(at.expander) == 31
    at.text_input(key='history_search').set_value('FAUSSE ASSISTANCE').run()
    assert len(at.expander) == 7  # deux campagnes distinctes, chacune avec deux assistants
    assert at.session_state['history_page'] == 1
    at.selectbox(key='history_mode').set_value('protégé').run()
    assert len(at.expander) == 5
    at.text_input(key='history_search').set_value('aucun resultat xyz').run()
    assert len(at.expander) == 1
    assert at.button(key='history_next').disabled
    at.checkbox(key='confirm_reset').check().run()
    at.button[0].click().run()
    assert not at.exception
    assert history() == []


def test_email_and_grouped_comparison(tmp_path, monkeypatch):
    monkeypatch.setenv('BRECHIA_DB', str(tmp_path/'mail.sqlite3'))
    at = AppTest.from_file(APP, default_timeout=15).run()
    at.sidebar.radio[0].set_value('Laboratoire').run()
    at.selectbox[0].set_value(2).run()
    assert any('Nous effectuons une vérification' in item.value for item in at.markdown)
    at.button[0].click().run()
    assert any('L’attaque a réussi' in item.value for item in at.error)
    at.sidebar.radio[0].set_value('Comparaison').run()
    at.button[0].click().run()
    assert len(at.expander) == 30
    assert len(at.metric) == 8
    at.text_input(key='comparison_search').set_value('reunion').run()
    assert len(at.expander) == 3
    assert len(at.metric) == 8
    at.text_input(key='comparison_search').set_value('A01').run()
    assert len(at.expander) == 3
    at.selectbox(key='comparison_size').set_value(25).run()
    assert at.session_state['comparison_page'] == 1
    assert not at.exception


def test_new_task_results_visible(tmp_path, monkeypatch):
    monkeypatch.setenv('BRECHIA_DB', str(tmp_path/'task.sqlite3'))
    at = AppTest.from_file(APP, default_timeout=15).run()
    at.sidebar.radio[0].set_value('Laboratoire').run()
    for index, expected in [(8, 'Aucun résumé produit'), (9, 'Résumé produit mais falsifié')]:
        at.selectbox[0].set_value(index).run()
        at.button[0].click().run()
        assert not at.exception
        assert any(expected in m.value for m in at.markdown)
        assert any('Résumé attendu' in m.value for m in at.markdown)
    at.sidebar.radio[0].set_value('Comparaison').run()
    at.button[0].click().run()
    assert at.metric[3].value == '80%'
    assert at.metric[7].value == '100%'
