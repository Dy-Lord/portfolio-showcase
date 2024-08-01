from datetime import datetime
from enum import Enum

import uuid6
from pydantic import BaseModel, Field


class Keys(Enum):
    mv_box_playlists_db = 'mv_box_playlists'

    playlists = 'playlists'
    top_playlists_snapshots = 'top_playlists_snapshots'
    tracks = 'tracks'
    artists = 'artists'
    info = 'info'
    join_members = 'join_members'
    configs = 'configs'
    spotify_users = 'spotify_users'
    email_users = 'email_users'
    test = 'test'

    @classmethod
    def alter_keys(cls, prefix: str):
        for el in cls:
            if prefix not in el.value:
                el._value_ = f'{prefix}_{el.value}'


class Platforms(Enum):
    spotify = 'spotify'


class Playlist(BaseModel):
    token: str = Field(default_factory=lambda: uuid6.uuid7().hex, alias='_id')
    owner_token: str | None = None

    platform: Platforms
    platform_id: str

    name: str
    description: str | None = None
    image_path: str | None = None

    follower_count: int
    track_count: int
    mv_track_count: int = 0
    sponsored: bool = False

    competing: bool = True


class TopPlaylistsSnapshot(BaseModel):
    token: str = Field(default_factory=lambda: uuid6.uuid7().hex, alias='_id')
    top_playlists: list[Playlist]
    timestamp: datetime


class TrackSource(BaseModel):
    platform: Platforms
    platform_id: str


class Track(BaseModel):
    token: str = Field(default_factory=lambda: uuid6.uuid7().hex, alias='_id')
    artist_token: str | None = None
    sources: list[TrackSource]

    name: str
    image_path: str

    mv_pass: bool


class ArtistSource(BaseModel):
    platform: Platforms
    platform_id: str
    follower_count: int


class Artist(BaseModel):
    token: str = Field(default_factory=lambda: uuid6.uuid7().hex, alias='_id')

    name: str
    image_path: str

    sources: list[ArtistSource]


class InfoTypes(Enum):
    general = 'general'


class GeneralInfo(BaseModel):
    info_type: str = Field(default=InfoTypes.general.value, alias='_id')
    last_snapshot_timestamp: datetime
    snapshot_cycle: int

    network_coverage: int
    landing_page_view_count: int


class MemberTypes(Enum):
    fan = 'fan'
    artist = 'artist'
    curator = 'curator'


class JoinMember(BaseModel):
    token: str = Field(default_factory=lambda: uuid6.uuid7().hex, alias='_id')
    name: str
    email: str
    member_type: MemberTypes
    signed_up: bool = True
    news_subscription: bool = True
    last_sent_news_date: datetime | None = None


class ConfigTypes(Enum):
    spotify = 'spotify'


class SpotifyConfig(BaseModel):
    config_type: str = Field(default=ConfigTypes.spotify.value, alias='_id')
    client_id: str
    client_secret: str


class SpotifyUser(BaseModel):
    token: str = Field(default_factory=lambda: uuid6.uuid7().hex, alias='_id')
    name: str
    follower_count: int
    spotify_id: str


class EmailTags(Enum):
    info = 'info'
    action = 'action'

    tech = 'tech'
    support = 'support'
    finance = 'finance'
    community = 'community'


class SenderSlugs(Enum):
    community_team = 'us-community-team'


class EmailUser(BaseModel):
    token: str = Field(default_factory=lambda: uuid6.uuid7().hex, alias='_id')
    slug: SenderSlugs
    name: str
    username: str
    domain: str
    region: str

