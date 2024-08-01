import os

import pytest
from dotenv import load_dotenv

from backend.modules.app.core import AppCore, PlaylistTrace
from backend.modules.db.db_engine import DBEngine
from backend.modules.db.models import Platforms, SpotifyConfig
from backend.tests.sample_data import track_samples, playlist_samples, spotify_track_sample
from backend.tests.unit.db.test_mongo_engine import mongo_engine_rollback, mongo_engine


load_dotenv()

TEST_SPOTIFY_CLIENT_ID = os.environ['TEST_SPOTIFY_CLIENT_ID']
TEST_SPOTIFY_CLIENT_SECRET = os.environ['TEST_SPOTIFY_CLIENT_SECRET']


@pytest.fixture()
def app_core(mongo_engine_rollback):
    db_engine = DBEngine(db_engine=mongo_engine_rollback)
    db_engine.add_config(SpotifyConfig(client_id=TEST_SPOTIFY_CLIENT_ID,
                                       client_secret=TEST_SPOTIFY_CLIENT_SECRET))
    app_core = AppCore(db_engine=db_engine, dev_mode=True, verbose=False)

    yield app_core

    app_core.__del__()


def test__init_playlist_tracking(app_core):
    for playlist in playlist_samples:
        app_core.db_engine.add_playlist(playlist)
    app_core._init_playlist_tracking()
    assert app_core.playlist_tracking.available_slot_idx == len(playlist_samples) % 24


def test__update_playlist_trace(app_core):
    for playlist in playlist_samples:
        app_core.db_engine.add_playlist(playlist)
    app_core._init_playlist_tracking()

    new_trace = app_core.playlist_tracking.slots[1][0]
    new_trace.mv_track_count = 32
    new_trace.follower_count = 23
    update_response = app_core._update_playlist_trace(new_trace)
    assert update_response

    current_trace = app_core.playlist_tracking.slots[1][0]
    assert current_trace.mv_track_count == new_trace.mv_track_count
    assert current_trace.follower_count == new_trace.follower_count


def test__track_playlist(app_core):
    playlist = playlist_samples[0]
    trace = PlaylistTrace(playlist_token=playlist.token,
                          platform=playlist.platform,
                          platform_id=playlist.platform_id,
                          mv_track_count=playlist.mv_track_count,
                          follower_count=playlist.follower_count)
    app_core._track_playlist(playlist=trace)
    assert app_core.playlist_tracking.available_slot_idx == 1
    assert app_core.playlist_tracking.slots[0][0] == trace


def test__playlist_tracking_job(app_core):
    for playlist in playlist_samples:
        app_core.db_engine.add_playlist(playlist)

    app_core._init_playlist_tracking()
    app_core._playlist_tracking_job()


def test_check_playlist(app_core):
    playlist = playlist_samples[0]
    app_core.track_new_playlist(platform_id=playlist.platform_id, platform=Platforms.spotify)
    app_core.add_track(platform_id='469WecMhHPGtp39QSUOdNw', platform=Platforms.spotify)
    trace = app_core.playlist_tracking.slots[0][0]
    app_core.check_playlist(trace)
    assert app_core.db_engine.get_top_playlists(limit=1)[0].mv_track_count == 1


def test_track_new_playlist(app_core):
    playlist = playlist_samples[0]
    app_core.track_new_playlist(platform_id=playlist.platform_id, platform=Platforms.spotify)

    new_playlist = app_core.db_engine.get_top_playlists()[0]
    spotify_user = app_core.db_engine.get_spotify_user_by_token(new_playlist.owner_token)

    assert new_playlist.platform_id == playlist.platform_id
    assert spotify_user


def test_add_track(app_core):
    track = spotify_track_sample
    app_core.add_track(platform_id=track.spotify_id, platform=Platforms.spotify)
    artist = app_core.db_engine.get_artist_by_platform(platform_id=track.artist.spotify_id, platform=Platforms.spotify)
    new_track = app_core.db_engine.get_mv_tracks()[0]

    assert artist.sources[0].platform_id == track.artist.spotify_id
    assert new_track.sources[0].platform_id == track.spotify_id
    assert new_track.artist_token == artist.token

