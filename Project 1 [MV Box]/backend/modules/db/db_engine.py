from datetime import datetime

from backend.modules.db.models import Playlist, Keys, Track, Artist, GeneralInfo, InfoTypes, JoinMember, Platforms, \
    ConfigTypes, SpotifyConfig, SpotifyUser, SenderSlugs, EmailUser, TopPlaylistsSnapshot
from backend.modules.db.mongo_engine import MongoEngine


class DBEngine:
    def __init__(self, db_engine: MongoEngine):
        self.db_engine = db_engine

    def check_playlist_existence(self, platform_id: str, platform: Platforms):
        return self.db_engine.exists(db=Keys.mv_box_playlists_db, key=Keys.playlists,
                                     target={'platform_id': platform_id,
                                             'platform': platform.value})

    def check_track_existence(self, platform_id: str, platform: Platforms):
        return self.db_engine.exists(db=Keys.mv_box_playlists_db, key=Keys.tracks,
                                     target={'sources': {'$elemMatch': {
                                         'platform': platform.value,
                                         'platform_id': platform_id}}})

    def check_artist_existence(self, platform_id: str, platform: Platforms):
        return self.db_engine.exists(db=Keys.mv_box_playlists_db, key=Keys.artists,
                                     target={'sources': {'$elemMatch': {
                                         'platform': platform.value,
                                         'platform_id': platform_id}}})

    def add_playlist(self, playlist: Playlist):
        if self.check_playlist_existence(platform_id=playlist.platform_id, platform=playlist.platform):
            return False

        data = playlist.model_dump(by_alias=True, mode='json')
        self.db_engine.insert(db=Keys.mv_box_playlists_db, key=Keys.playlists, data=data)
        return True

    def get_top_playlists(self, offset: int = 0, limit: int = 0):
        sort = [('mv_track_count', -1), ('follower_count', -1)]
        data = self.db_engine.find(db=Keys.mv_box_playlists_db, key=Keys.playlists,
                                   target={'competing': True, 'sponsored': False},
                                   sort=sort, skip=offset, limit=limit)
        return [Playlist.model_validate(el) for el in data]

    def get_sponsored_playlists(self, offset: int = 0, limit: int = 0):
        sort = [('mv_track_count', -1), ('follower_count', -1)]
        data = self.db_engine.find(db=Keys.mv_box_playlists_db, key=Keys.playlists,
                                   target={'competing': True, 'sponsored': True},
                                   sort=sort, skip=offset, limit=limit)
        return [Playlist.model_validate(el) for el in data]

    def get_playlist_rank(self, playlist_token: str):
        sort = [('mv_track_count', -1), ('follower_count', -1)]
        data = self.db_engine.find(db=Keys.mv_box_playlists_db, key=Keys.playlists,
                                   target={'competing': True}, sort=sort, project={'_id': 1})
        tokens = [el['_id'] for el in data]
        return tokens.index(playlist_token) + 1

    def update_playlist(self,
                        playlist_token: str,
                        mv_track_count: int = None,
                        follower_count: int = None):
        update_query = {}
        if mv_track_count is not None:
            update_query.update({'mv_track_count': mv_track_count})
        if follower_count is not None:
            update_query.update({'follower_count': follower_count})

        if update_query:
            self.db_engine.update_one(db=Keys.mv_box_playlists_db, key=Keys.playlists,
                                      target={'_id': playlist_token},
                                      update_query={'$set': update_query})

    def add_track(self, track: Track):
        data = track.model_dump(by_alias=True, mode='json')
        self.db_engine.insert(db=Keys.mv_box_playlists_db, key=Keys.tracks, data=data)

    def get_mv_tracks(self, offset: int = 0, limit: int = 0):
        data = self.db_engine.find(db=Keys.mv_box_playlists_db, key=Keys.tracks,
                                   target={'mv_pass': True}, skip=offset, limit=limit)
        return [Track.model_validate(el) for el in data]

    def get_artists(self, artist_tokens: list[str]):
        data = self.db_engine.find(db=Keys.mv_box_playlists_db, key=Keys.artists,
                                   target={'_id': {'$in': artist_tokens}})
        return [Artist.model_validate(el) for el in data]

    def get_artist_by_platform(self, platform_id: str, platform: Platforms):
        data = self.db_engine.find_one(db=Keys.mv_box_playlists_db, key=Keys.artists,
                                       target={'sources': {'$elemMatch': {
                                           'platform': platform.value,
                                           'platform_id': platform_id}}})
        return Artist.model_validate(data) if data else None

    def add_artist(self, artist: Artist):
        data = artist.model_dump(by_alias=True, mode='json')
        self.db_engine.insert(db=Keys.mv_box_playlists_db, key=Keys.artists, data=data)

    def add_general_info(self, info: GeneralInfo):
        data = info.model_dump(by_alias=True, mode='json')
        self.db_engine.insert(db=Keys.mv_box_playlists_db, key=Keys.info, data=data)

    def get_info(self, info_type: InfoTypes):
        data = self.db_engine.find_one(db=Keys.mv_box_playlists_db, key=Keys.info,
                                       target={'_id': info_type.value})
        if info_type is InfoTypes.general:
            return GeneralInfo.model_validate(data)
        return None

    def update_general_info(self,
                            network_coverage: int = None,
                            landing_page_view_count: int = None):
        update_query = {}
        if network_coverage is not None:
            update_query.update({'network_coverage': network_coverage})
        if landing_page_view_count is not None:
            update_query.update({'landing_page_view_count': landing_page_view_count})

        if update_query:
            self.db_engine.update_one(db=Keys.mv_box_playlists_db, key=Keys.info,
                                      target={'_id': InfoTypes.general.value},
                                      update_query={'$set': update_query})

    def incr_landing_page_view_count(self, amount: int = 1):
        self.db_engine.update_one(db=Keys.mv_box_playlists_db, key=Keys.info,
                                  target={'_id': InfoTypes.general.value},
                                  update_query={'$inc': {'landing_page_view_count': amount}})

    def set_last_snapshot_timestamp(self, date: datetime):
        self.db_engine.update_one(db=Keys.mv_box_playlists_db, key=Keys.info,
                                  target={'_id': InfoTypes.general.value},
                                  update_query={'$set': {'last_snapshot_timestamp': date}})

    def get_config(self, config_type: ConfigTypes):
        data = self.db_engine.find_one(db=Keys.mv_box_playlists_db, key=Keys.configs,
                                       target={'_id': config_type.value})
        if config_type is ConfigTypes.spotify:
            return SpotifyConfig.model_validate(data)
        return None

    def add_config(self, config: SpotifyConfig):
        data = config.model_dump(by_alias=True, mode='json')
        self.db_engine.insert(db=Keys.mv_box_playlists_db, key=Keys.configs, data=data)

    def add_join_member(self, member: JoinMember):
        if self.db_engine.exists(db=Keys.mv_box_playlists_db, key=Keys.join_members,
                                 target={'email': member.email}):
            return False

        data = member.model_dump(by_alias=True, mode='json')
        self.db_engine.insert(db=Keys.mv_box_playlists_db, key=Keys.join_members, data=data)
        return True

    def get_join_members(self, offset: int = 0, limit: int = 0, target: dict = None):
        sort = [('last_sent_news_date', 1), ('signed_up', -1)]
        data = self.db_engine.find(db=Keys.mv_box_playlists_db, key=Keys.join_members,
                                   target=target if target is not None else {},
                                   sort=sort, skip=offset, limit=limit)
        return [JoinMember.model_validate(el) for el in data]

    def update_join_member(self,
                           token: str,
                           last_sent_news_date: datetime = None):
        update_query = {}
        if last_sent_news_date is not None:
            update_query.update({'last_sent_news_date': last_sent_news_date})

        if update_query:
            self.db_engine.update_one(db=Keys.mv_box_playlists_db, key=Keys.join_members,
                                      target={'_id': token},
                                      update_query={'$set': update_query})

    def get_join_members_count(self):
        return self.db_engine.count(db=Keys.mv_box_playlists_db, key=Keys.join_members, target={})

    def sign_up_member(self, token: str):
        self.db_engine.update_one(db=Keys.mv_box_playlists_db, key=Keys.join_members,
                                  target={'_id': token}, update_query={'$set': {'signed_up': True}})

    def add_spotify_user(self, user: SpotifyUser):
        if self.db_engine.exists(db=Keys.mv_box_playlists_db, key=Keys.spotify_users,
                                 target={'spotify_id': user.spotify_id}):
            return False

        data = user.model_dump(by_alias=True, mode='json')
        self.db_engine.insert(db=Keys.mv_box_playlists_db, key=Keys.spotify_users, data=data)
        return True

    def get_spotify_user_by_spotify_id(self, spotify_id: str):
        data = self.db_engine.find_one(db=Keys.mv_box_playlists_db, key=Keys.spotify_users,
                                       target={'spotify_id': spotify_id})
        return SpotifyUser.model_validate(data) if data else None

    def get_spotify_user_by_token(self, token: str):
        data = self.db_engine.find_one(db=Keys.mv_box_playlists_db, key=Keys.spotify_users,
                                       target={'_id': token})
        return SpotifyUser.model_validate(data) if data else None

    def get_email_user(self, sender: SenderSlugs):
        data = self.db_engine.find_one(db=Keys.mv_box_playlists_db, key=Keys.email_users,
                                       target={'slug': sender.value})
        return EmailUser.model_validate(data) if data else None

    def add_email_user(self, email_user: EmailUser):
        data = email_user.model_dump(by_alias=True, mode='json')
        self.db_engine.insert(db=Keys.mv_box_playlists_db, key=Keys.email_users, data=data)

    def add_top_playlists_snapshot(self, timestamp: datetime, playlists: list[Playlist]):
        snapshot = TopPlaylistsSnapshot(top_playlists=playlists, timestamp=timestamp)
        data = snapshot.model_dump(by_alias=True, mode='json')
        self.db_engine.insert(db=Keys.mv_box_playlists_db, key=Keys.top_playlists_snapshots, data=data)

    def get_top_playlists_snapshots(self, offset: int = 0, limit: int = 0, target: dict = None):
        sort = [('timestamp', -1)]
        data = self.db_engine.find(db=Keys.mv_box_playlists_db, key=Keys.top_playlists_snapshots,
                                   target=target if target is not None else {},
                                   sort=sort, skip=offset, limit=limit)
        return [TopPlaylistsSnapshot.model_validate(el) for el in data]

