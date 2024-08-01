import os

import pytest
from dotenv import load_dotenv

from backend.modules.db.models import Keys
from backend.modules.db.mongo_engine import MongoEngine
from backend.tests.sample_data import mongo_engine_samples

load_dotenv()

MONGO_HOST = os.environ['MONGO_HOST']
MONGO_PORT = int(os.environ['MONGO_PORT'])
MONGO_USER = os.environ['MONGO_USER']
MONGO_PASSWORD = os.environ['MONGO_PASSWORD']


@pytest.fixture(scope="session")
def mongo_engine():
    Keys.alter_keys(prefix='test')
    engine = MongoEngine(host=MONGO_HOST, username=MONGO_USER, password=MONGO_PASSWORD,
                         marker='unit_test', verbose=False)
    engine.start_session()

    yield engine

    engine.abort_session()
    engine.__del__()


@pytest.fixture()
def mongo_engine_rollback(mongo_engine):
    mongo_engine.start_session()

    yield mongo_engine

    mongo_engine.abort_session()


def test_insert(mongo_engine_rollback):
    mongo_engine_rollback.insert(db=Keys.mv_box_playlists_db, key=Keys.test, data=mongo_engine_samples[0])
    response = mongo_engine_rollback.find_one(db=Keys.mv_box_playlists_db, key=Keys.test, target={'_id': mongo_engine_samples[0]['_id']})
    assert mongo_engine_samples[0]['data'] == response['data']


def test_find_one(mongo_engine_rollback):
    mongo_engine_rollback.insert(db=Keys.mv_box_playlists_db, key=Keys.test, data=mongo_engine_samples[0])
    response = mongo_engine_rollback.find_one(db=Keys.mv_box_playlists_db, key=Keys.test, target={'_id': mongo_engine_samples[0]['_id']})
    assert mongo_engine_samples[0]['data'] == response['data']


def test_find(mongo_engine_rollback):
    mongo_engine_rollback.insert(db=Keys.mv_box_playlists_db, key=Keys.test, data=mongo_engine_samples[0])
    mongo_engine_rollback.insert(db=Keys.mv_box_playlists_db, key=Keys.test, data=mongo_engine_samples[1])
    response = mongo_engine_rollback.find(db=Keys.mv_box_playlists_db, key=Keys.test, target={'data': mongo_engine_samples[0]['data']})
    assert len(list(response)) == 2


def test_update_one(mongo_engine_rollback):
    mongo_engine_rollback.insert(db=Keys.mv_box_playlists_db, key=Keys.test, data=mongo_engine_samples[0])
    mongo_engine_rollback.update_one(db=Keys.mv_box_playlists_db, key=Keys.test, target={'_id': mongo_engine_samples[0]['_id']},
                                     update_query={'$set': {'data': 'new_data'}})
    response = mongo_engine_rollback.find_one(db=Keys.mv_box_playlists_db, key=Keys.test, target={'_id': mongo_engine_samples[0]['_id']})
    assert 'new_data' == response['data']


def test_update_many(mongo_engine_rollback):
    mongo_engine_rollback.insert(db=Keys.mv_box_playlists_db, key=Keys.test, data=mongo_engine_samples[0])
    mongo_engine_rollback.insert(db=Keys.mv_box_playlists_db, key=Keys.test, data=mongo_engine_samples[1])
    mongo_engine_rollback.update_many(db=Keys.mv_box_playlists_db, key=Keys.test, target={'data': mongo_engine_samples[0]['data']},
                                      update_query={'$set': {'data': 'new_data'}})
    response = mongo_engine_rollback.find(db=Keys.mv_box_playlists_db, key=Keys.test, target={'data': 'new_data'})
    assert len(list(response)) == 2


def test_delete_one(mongo_engine_rollback):
    mongo_engine_rollback.insert(db=Keys.mv_box_playlists_db, key=Keys.test, data=mongo_engine_samples[0])
    mongo_engine_rollback.delete_one(db=Keys.mv_box_playlists_db, key=Keys.test, target={'_id': mongo_engine_samples[0]['_id']})
    assert not mongo_engine_rollback.exists(db=Keys.mv_box_playlists_db, key=Keys.test, target={'_id': mongo_engine_samples[0]['_id']})


def test_exists(mongo_engine_rollback):
    mongo_engine_rollback.insert(db=Keys.mv_box_playlists_db, key=Keys.test, data=mongo_engine_samples[0])
    assert mongo_engine_rollback.exists(db=Keys.mv_box_playlists_db, key=Keys.test, target={'_id': mongo_engine_samples[0]['_id']})


def test_count(mongo_engine_rollback):
    mongo_engine_rollback.insert(db=Keys.mv_box_playlists_db, key=Keys.test, data=mongo_engine_samples[0])
    mongo_engine_rollback.insert(db=Keys.mv_box_playlists_db, key=Keys.test, data=mongo_engine_samples[1])
    document_count = mongo_engine_rollback.count(db=Keys.mv_box_playlists_db, key=Keys.test, target={})
    assert document_count == 2


def test_get_keys(mongo_engine_rollback):
    mongo_engine_rollback.insert(db=Keys.mv_box_playlists_db, key=Keys.test, data=mongo_engine_samples[0])
    keys = mongo_engine_rollback.get_keys(db=Keys.mv_box_playlists_db, key=Keys.test, target={'_id': mongo_engine_samples[0]['_id']})
    assert keys == list(mongo_engine_samples[0].keys())
