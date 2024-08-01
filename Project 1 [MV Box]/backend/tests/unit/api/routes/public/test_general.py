from datetime import timedelta

import pytest
from fastapi import HTTPException
from fastapi import status as http_status

from backend.modules.api.routes.public.general import general_info_get_landing_stats, LandingStatsResponse, \
    general_playlists_get_top_playlists, TopPlaylistsResponse, general_playlists_track_playlist, \
    general_tracks_get_mv_tracks, MVTracksResponse, MVTrack, general_members_join, TopPlaylist, MVTrackSource, \
    TrackPlaylistResponse
from backend.modules.db.models import Platforms, TrackSource, JoinMember, MemberTypes
from backend.modules.tools import get_spotify_playlist_url, get_spotify_track_url
from backend.tests.sample_data import general_info_sample, playlist_samples, spotify_playlist_sample, \
    spotify_track_sample, join_members_samples
from backend.tests.unit.app.test_core import app_core
from backend.tests.unit.db.test_db_engine import mongo_engine_rollback, mongo_engine


def test_general_info_get_landing_stats(app_core):
    app_core.db_engine.add_general_info(info=general_info_sample)
    info = general_info_get_landing_stats(db=app_core.db_engine)

    next_snapshot_at = general_info_sample.last_snapshot_timestamp + timedelta(
        seconds=general_info_sample.snapshot_cycle)
    expected_info = LandingStatsResponse(
        next_snapshot_at=int(next_snapshot_at.timestamp()),
        network_coverage=general_info_sample.network_coverage,
        view_count=general_info_sample.landing_page_view_count)
    assert info == expected_info


def test_general_playlists_get_top_playlists(app_core):
    for playlist in playlist_samples:
        app_core.db_engine.add_playlist(playlist=playlist)
    response = general_playlists_get_top_playlists(db=app_core.db_engine, offset=0)

    wrapped_playlists = [TopPlaylist(token=playlist.token,
                                     name=playlist.name,
                                     platform=playlist.platform,
                                     platform_url=get_spotify_playlist_url(playlist_id=playlist.platform_id),
                                     image_url=playlist.image_path,
                                     follower_count=playlist.follower_count,
                                     mv_track_count=playlist.mv_track_count,
                                     sponsored=playlist.sponsored) for playlist in playlist_samples]

    expected_response = TopPlaylistsResponse(offset=0,
                                             next_offset=None,
                                             count=len(wrapped_playlists),
                                             playlists=sorted(wrapped_playlists,
                                                              key=lambda x: (x.mv_track_count, x.follower_count),
                                                              reverse=True))
    assert response == expected_response

    with pytest.raises(HTTPException) as ex_info:
        general_playlists_get_top_playlists(db=app_core.db_engine, offset=-1)
    assert ex_info.value.status_code == http_status.HTTP_400_BAD_REQUEST
    assert ex_info.value.detail == 'Invalid offset'


def test_general_playlists_track_playlist(app_core):
    spotify_playlist_url = get_spotify_playlist_url(spotify_playlist_sample.spotify_id)

    response = general_playlists_track_playlist(playlist_url=spotify_playlist_url,
                                                app_core=app_core, db=app_core.db_engine)
    playlist = app_core.db_engine.get_top_playlists(limit=1)[0]
    playlist_rank = app_core.db_engine.get_playlist_rank(playlist_token=playlist.token)
    expected_response = TrackPlaylistResponse(playlist=TopPlaylist(token=playlist.token,
                                                                   name=playlist.name,
                                                                   platform=playlist.platform,
                                                                   platform_url=get_spotify_playlist_url(playlist.platform_id),
                                                                   image_url=playlist.image_path,
                                                                   follower_count=playlist.follower_count,
                                                                   mv_track_count=playlist.mv_track_count,
                                                                   sponsored=playlist.sponsored),
                                              playlist_rank=playlist_rank)

    assert response == expected_response

    with pytest.raises(HTTPException) as ex_1:
        general_playlists_track_playlist(playlist_url=spotify_playlist_url,
                                         app_core=app_core, db=app_core.db_engine)
    assert ex_1.value.status_code == http_status.HTTP_403_FORBIDDEN
    assert ex_1.value.detail == 'Playlist already exists'

    with pytest.raises(HTTPException) as ex_2:
        invalid_spotify_playlist_url = get_spotify_playlist_url('broken_id')
        general_playlists_track_playlist(playlist_url=invalid_spotify_playlist_url,
                                         app_core=app_core, db=app_core.db_engine)
    assert ex_2.value.status_code == http_status.HTTP_400_BAD_REQUEST
    assert ex_2.value.detail == 'Invalid url'


def test_general_tracks_get_mv_tracks(app_core):
    track = spotify_track_sample
    app_core.add_track(platform_id=track.spotify_id, platform=Platforms.spotify)
    response = general_tracks_get_mv_tracks(db=app_core.db_engine, offset=0, shuffle=False)

    expected_response = MVTracksResponse(offset=0,
                                         next_offset=None,
                                         count=1,
                                         tracks=[MVTrack(title=track.name,
                                                         artist_name=track.artist.name,
                                                         image_url=track.album.image_url,
                                                         sources=[MVTrackSource(platform=Platforms.spotify,
                                                                                platform_url=get_spotify_track_url(
                                                                                    track.spotify_id))])])
    assert response == expected_response

    with pytest.raises(HTTPException) as ex_info:
        general_tracks_get_mv_tracks(db=app_core.db_engine, offset=-1)
    assert ex_info.value.status_code == http_status.HTTP_400_BAD_REQUEST
    assert ex_info.value.detail == 'Invalid offset'


def test_general_members_join(app_core):
    member = join_members_samples[0]
    response = general_members_join(body=member, db=app_core.db_engine)
    new_member = app_core.db_engine.get_join_members(limit=1)[0]

    assert response == {'details': 'ok'}
    assert member == new_member

    response = general_members_join(body=member, db=app_core.db_engine)
    new_member = app_core.db_engine.get_join_members(limit=1)[0]

    assert response == {'details': 'ok'}
    assert new_member.signed_up

    with pytest.raises(HTTPException) as ex_1:
        general_members_join(body=member, db=app_core.db_engine)
    assert ex_1.value.status_code == http_status.HTTP_403_FORBIDDEN
    assert ex_1.value.detail == 'Member already exists'

    with pytest.raises(HTTPException) as ex_2:
        member.email = 'broken.email.com'
        general_members_join(body=member, db=app_core.db_engine)
    assert ex_2.value.status_code == http_status.HTTP_400_BAD_REQUEST
    assert ex_2.value.detail == 'Invalid email'
