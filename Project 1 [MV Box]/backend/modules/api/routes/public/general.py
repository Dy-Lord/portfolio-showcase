import random
from datetime import timedelta

from fastapi import APIRouter, HTTPException
from fastapi import status as http_status
from pydantic import BaseModel

from backend.modules.api.auxiliary.dependencies import DBEngineDep, AppCoreDep
from backend.modules.db.models import InfoTypes, JoinMember, Platforms
from backend.modules.tools import try_extract, validate_email_format, extract_spotify_id_from_urs, base62_validator, \
    get_spotify_playlist_url, get_spotify_track_url

general_api_router = APIRouter(prefix='/general', tags=['general'])


class TopPlaylist(BaseModel):
    token: str
    name: str
    platform: Platforms
    platform_url: str
    image_url: str | None
    follower_count: int
    mv_track_count: int
    sponsored: bool


class TopPlaylistsResponse(BaseModel):
    offset: int
    next_offset: int | None
    count: int
    playlists: list[TopPlaylist]


class MVTrackSource(BaseModel):
    platform: Platforms
    platform_url: str


class MVTrack(BaseModel):
    title: str
    artist_name: str | None
    image_url: str
    sources: list[MVTrackSource]


class MVTracksResponse(BaseModel):
    offset: int
    next_offset: int | None
    count: int
    tracks: list[MVTrack]


class LandingStatsResponse(BaseModel):
    next_snapshot_at: int
    network_coverage: int
    view_count: int


class TrackPlaylistResponse(BaseModel):
    playlist: TopPlaylist
    playlist_rank: int


@general_api_router.get('/info/landing_stats', response_model=LandingStatsResponse)
def general_info_get_landing_stats(db: DBEngineDep):
    data = db.get_info(InfoTypes.general)
    next_snapshot_at = data.last_snapshot_timestamp + timedelta(seconds=data.snapshot_cycle)
    db.incr_landing_page_view_count()
    return LandingStatsResponse(next_snapshot_at=int(next_snapshot_at.timestamp()),
                                network_coverage=data.network_coverage,
                                view_count=data.landing_page_view_count)


@general_api_router.get('/playlists/top_playlists', response_model=TopPlaylistsResponse)
def general_playlists_get_top_playlists(db: DBEngineDep, offset: int = 0):
    if offset < 0:
        raise HTTPException(http_status.HTTP_400_BAD_REQUEST, 'Invalid offset')

    limit = 11
    next_offset = None
    playlists = db.get_top_playlists(offset=offset, limit=limit)
    sponsored_playlists = db.get_sponsored_playlists(offset=offset, limit=limit - 1)
    if len(playlists) == limit:
        next_offset = offset + limit - 1
        playlists.pop()

    sponsor_idx = -2
    for spl in sponsored_playlists:
        sponsor_idx += 3
        playlists.insert(sponsor_idx, spl)

    wrapped_playlists = [TopPlaylist(token=playlist.token,
                                     name=playlist.name,
                                     platform=playlist.platform,
                                     platform_url=get_spotify_playlist_url(playlist_id=playlist.platform_id),
                                     image_url=playlist.image_path,
                                     follower_count=playlist.follower_count,
                                     mv_track_count=playlist.mv_track_count,
                                     sponsored=playlist.sponsored) for playlist in playlists]

    return TopPlaylistsResponse(offset=offset, next_offset=next_offset,
                                count=len(playlists), playlists=wrapped_playlists)


@general_api_router.post('/playlists/track_playlist', response_model=TrackPlaylistResponse)
def general_playlists_track_playlist(playlist_url: str, db: DBEngineDep, app_core: AppCoreDep):
    spotify_id = extract_spotify_id_from_urs(url=playlist_url)
    if not spotify_id or not base62_validator(data=spotify_id):
        raise HTTPException(http_status.HTTP_400_BAD_REQUEST, 'Invalid url')

    if db.check_playlist_existence(platform_id=spotify_id, platform=Platforms.spotify):
        raise HTTPException(http_status.HTTP_403_FORBIDDEN, 'Playlist already exists')

    try:
        new_playlist = app_core.track_new_playlist(platform_id=spotify_id, platform=Platforms.spotify)
    except:
        raise HTTPException(http_status.HTTP_400_BAD_REQUEST, 'Invalid url')

    playlist_rank = db.get_playlist_rank(playlist_token=new_playlist.token)
    return TrackPlaylistResponse(playlist=TopPlaylist(token=new_playlist.token,
                                                      name=new_playlist.name,
                                                      platform=new_playlist.platform,
                                                      platform_url=get_spotify_playlist_url(new_playlist.platform_id),
                                                      image_url=new_playlist.image_path,
                                                      follower_count=new_playlist.follower_count,
                                                      mv_track_count=new_playlist.mv_track_count,
                                                      sponsored=new_playlist.sponsored),
                                 playlist_rank=playlist_rank)


@general_api_router.get('/tracks/mv_tracks', response_model=MVTracksResponse)
def general_tracks_get_mv_tracks(db: DBEngineDep, offset: int = 0, shuffle: bool = True):
    if offset < 0:
        raise HTTPException(http_status.HTTP_400_BAD_REQUEST, 'Invalid offset')

    limit = 11
    next_offset = None
    tracks = db.get_mv_tracks(offset=offset, limit=limit)
    if len(tracks) == limit:
        next_offset = offset + limit - 1
        tracks.pop()

    artist_tokens = [track.artist_token for track in tracks]
    artists = db.get_artists(artist_tokens)
    artists = {artist.token: artist for artist in artists}

    mv_tracks = []
    for track in tracks:
        mv_tracks.append(MVTrack(title=track.name,
                                 artist_name=try_extract(lambda: artists[track.artist_token].name),
                                 image_url=track.image_path, sources=[MVTrackSource(platform=source.platform,
                                                                                    platform_url=get_spotify_track_url(source.platform_id))
                                                                      for source in track.sources]))
    if shuffle:
        random.shuffle(mv_tracks)
    return MVTracksResponse(offset=offset, next_offset=next_offset,
                            count=len(tracks), tracks=mv_tracks)


@general_api_router.post('/members/join')
def general_members_join(body: JoinMember, db: DBEngineDep):
    # TODO add request limit
    if not validate_email_format(email=body.email):
        raise HTTPException(http_status.HTTP_400_BAD_REQUEST, 'Invalid email')

    if not db.add_join_member(member=body):
        member = db.get_join_members(target={'email': body.email})[0]
        if member.signed_up:
            raise HTTPException(http_status.HTTP_403_FORBIDDEN, 'Member already exists')
        db.sign_up_member(token=member.token)
    return {'details': 'ok'}

