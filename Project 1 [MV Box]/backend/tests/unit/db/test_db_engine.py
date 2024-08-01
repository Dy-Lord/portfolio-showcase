from datetime import datetime, timedelta, timezone

import pytest

from backend.modules.db.db_engine import DBEngine
from backend.modules.db.models import InfoTypes, ConfigTypes, JoinMember, MemberTypes
from backend.modules.tools import hour_rounder
from backend.tests.sample_data import playlist_samples, track_samples, artist_samples, general_info_sample, \
    spotify_config_sample, spotify_users_samples, join_members_samples, email_user_sample, top_playlists_snapshot_sample
from backend.tests.unit.db.test_mongo_engine import mongo_engine_rollback, mongo_engine


@pytest.fixture()
def db_engine(mongo_engine_rollback):
    engine = DBEngine(db_engine=mongo_engine_rollback)
    return engine


def test_add_playlist(db_engine):
    playlist = playlist_samples[0]
    db_engine.add_playlist(playlist=playlist)
    assert db_engine.check_playlist_existence(platform_id=playlist.platform_id, platform=playlist.platform)


def test_check_playlist_existence(db_engine):
    playlist = playlist_samples[0]
    db_engine.add_playlist(playlist=playlist)
    assert db_engine.check_playlist_existence(platform_id=playlist.platform_id, platform=playlist.platform)


def test_get_top_playlist(db_engine):
    for playlist in playlist_samples:
        db_engine.add_playlist(playlist=playlist)

    top_playlists = db_engine.get_top_playlists()
    assert top_playlists == sorted(playlist_samples, key=lambda x: (x.mv_track_count, x.follower_count), reverse=True)


def test_get_sponsored_playlists(db_engine):
    for playlist in playlist_samples:
        playlist.sponsored = True
        db_engine.add_playlist(playlist=playlist)

    top_playlists = db_engine.get_sponsored_playlists()
    assert top_playlists == sorted(playlist_samples, key=lambda x: (x.mv_track_count, x.follower_count), reverse=True)


def test_get_playlist_rank(db_engine):
    for playlist in playlist_samples:
        db_engine.add_playlist(playlist=playlist)

    sorted_playlists = sorted(playlist_samples, key=lambda x: (x.mv_track_count, x.follower_count), reverse=True)
    for idx, pl in enumerate(sorted_playlists, start=1):
        rank = db_engine.get_playlist_rank(playlist_token=pl.token)
        assert rank == idx


def test_update_playlist(db_engine):
    playlist = playlist_samples[0]
    db_engine.add_playlist(playlist=playlist)
    db_engine.update_playlist(playlist_token=playlist.token, mv_track_count=144, follower_count=5050)
    updated_playlist = db_engine.get_top_playlists(limit=1)[0]
    assert updated_playlist.mv_track_count == 144
    assert updated_playlist.follower_count == 5050


def test_add_track(db_engine):
    track = track_samples[0]
    db_engine.add_track(track=track)
    assert db_engine.check_track_existence(platform_id=track.sources[0].platform_id,
                                           platform=track.sources[0].platform)


def test_check_track_existence(db_engine):
    track = track_samples[0]
    db_engine.add_track(track=track)
    assert db_engine.check_track_existence(platform_id=track.sources[0].platform_id,
                                           platform=track.sources[0].platform)


def test_get_mv_tracks(db_engine):
    for track in track_samples:
        db_engine.add_track(track=track)

    mv_tracks = db_engine.get_mv_tracks()
    assert mv_tracks == list(filter(lambda x: x.mv_pass, track_samples))


def test_add_artist(db_engine):
    artist = artist_samples[0]
    db_engine.add_artist(artist=artist)
    assert db_engine.check_artist_existence(platform_id=artist.sources[0].platform_id,
                                            platform=artist.sources[0].platform)


def test_check_artist_existence(db_engine):
    artist = artist_samples[0]
    db_engine.add_artist(artist=artist)
    assert db_engine.check_artist_existence(platform_id=artist.sources[0].platform_id,
                                            platform=artist.sources[0].platform)


def test_get_artists(db_engine):
    for artist in artist_samples:
        db_engine.add_artist(artist=artist)

    artists = db_engine.get_artists(artist_tokens=[artist.token for artist in artist_samples])
    assert artists == artist_samples


def test_get_artist_by_platform(db_engine):
    for artist in artist_samples:
        db_engine.add_artist(artist=artist)

    artist = db_engine.get_artist_by_platform(platform_id=artist_samples[0].sources[0].platform_id,
                                              platform=artist_samples[0].sources[0].platform)
    assert artist == artist_samples[0]


def test_add_general_info(db_engine):
    db_engine.add_general_info(info=general_info_sample)
    assert general_info_sample == db_engine.get_info(info_type=InfoTypes.general)


def test_get_general_info(db_engine):
    db_engine.add_general_info(info=general_info_sample)
    assert general_info_sample == db_engine.get_info(info_type=InfoTypes.general)


def test_update_general_info(db_engine):
    db_engine.add_general_info(info=general_info_sample)
    db_engine.update_general_info(network_coverage=5555, landing_page_view_count=9999)
    info = db_engine.get_info(info_type=InfoTypes.general)
    assert info.network_coverage == 5555
    assert info.landing_page_view_count == 9999


def test_incr_landing_page_view_count(db_engine):
    db_engine.add_general_info(info=general_info_sample)
    db_engine.incr_landing_page_view_count(14)
    info = db_engine.get_info(info_type=InfoTypes.general)
    assert info.landing_page_view_count == general_info_sample.landing_page_view_count + 14


def test_set_last_snapshot_timestamp(db_engine):
    db_engine.add_general_info(info=general_info_sample)

    new_timestamp = hour_rounder(datetime.now() + timedelta(hours=1))
    db_engine.set_last_snapshot_timestamp(date=new_timestamp)
    assert new_timestamp == db_engine.get_info(info_type=InfoTypes.general).last_snapshot_timestamp


def test_add_config(db_engine):
    db_engine.add_config(config=spotify_config_sample)
    assert spotify_config_sample == db_engine.get_config(config_type=ConfigTypes.spotify)


def test_get_config(db_engine):
    db_engine.add_config(config=spotify_config_sample)
    assert spotify_config_sample == db_engine.get_config(config_type=ConfigTypes.spotify)


def test_add_spotify_user(db_engine):
    user = spotify_users_samples[0]
    db_engine.add_spotify_user(user=user)
    assert db_engine.get_spotify_user_by_spotify_id(spotify_id=user.spotify_id)


def test_get_spotify_user_by_spotify_id(db_engine):
    user = spotify_users_samples[1]
    db_engine.add_spotify_user(user=user)
    assert db_engine.get_spotify_user_by_spotify_id(spotify_id=user.spotify_id)


def test_get_spotify_user_by_token(db_engine):
    user = spotify_users_samples[1]
    db_engine.add_spotify_user(user=user)
    assert db_engine.get_spotify_user_by_token(token=user.token)


def test_add_join_member(db_engine):
    member = join_members_samples[0]
    db_engine.add_join_member(member=member)
    assert member == db_engine.get_join_members()[0]


def test_update_join_member(db_engine):
    member = join_members_samples[0]
    db_engine.add_join_member(member=member)
    last_date = hour_rounder(datetime.now())
    db_engine.update_join_member(token=member.token, last_sent_news_date=last_date)

    updated_member = db_engine.get_join_members(limit=1)[0]

    assert updated_member.last_sent_news_date == last_date


def test_get_join_members(db_engine):
    for member in join_members_samples:
        db_engine.add_join_member(member=member)
    members = db_engine.get_join_members()
    assert all([member in join_members_samples for member in members])


def test_get_join_members_count(db_engine):
    for member in join_members_samples:
        db_engine.add_join_member(member=member)
    member_count = db_engine.get_join_members_count()
    assert member_count == len(join_members_samples)


def test_sign_up_member(db_engine):
    member = join_members_samples[0]
    db_engine.add_join_member(member=member)
    db_engine.sign_up_member(token=member.token)
    assert db_engine.get_join_members(target={'_id': member.token})[0].signed_up


def test_add_email_user(db_engine):
    db_engine.add_email_user(email_user=email_user_sample)
    assert email_user_sample == db_engine.get_email_user(sender=email_user_sample.slug)


def test_get_email_user(db_engine):
    db_engine.add_email_user(email_user=email_user_sample)
    user = db_engine.get_email_user(sender=email_user_sample.slug)
    assert email_user_sample == user


def test_add_top_playlists_snapshot(db_engine):
    db_engine.add_top_playlists_snapshot(timestamp=top_playlists_snapshot_sample.timestamp,
                                         playlists=top_playlists_snapshot_sample.top_playlists)
    snapshot = db_engine.get_top_playlists_snapshots()[0]
    snapshot.token = top_playlists_snapshot_sample.token
    assert snapshot == top_playlists_snapshot_sample


def test_get_top_playlists_snapshots(db_engine):
    db_engine.add_top_playlists_snapshot(timestamp=top_playlists_snapshot_sample.timestamp,
                                         playlists=top_playlists_snapshot_sample.top_playlists)
    snapshot = db_engine.get_top_playlists_snapshots()[0]
    snapshot.token = top_playlists_snapshot_sample.token
    assert snapshot == top_playlists_snapshot_sample

