import os
import random
from datetime import datetime, timezone, timedelta

from dotenv import load_dotenv
from pydantic import BaseModel

from backend.modules.db.db_engine import DBEngine
from backend.modules.db.models import ConfigTypes, Platforms, Playlist, SpotifyUser, Track, Artist, ArtistSource, \
    TrackSource, SenderSlugs, InfoTypes
from backend.modules.email_service.engine import MailGunEngine
from backend.modules.email_service.templates import EmailPlaylistModel, TopPlaylistsEmailModel, TemplateEngine
from backend.modules.platforms.spotify.controller import SpotifyController
from backend.modules.platforms.spotify.models import SpotifyTrack
from backend.modules.tools import sprint, Colors, hour_rounder, CronThread, try_extract, slice_format, \
    get_spotify_playlist_url, format_number, group_into_bunches

load_dotenv()

MAILGUN_API_KEY = os.environ['MAILGUN_API_KEY']
WEB_APP_HOST = os.environ['WEB_APP_HOST']


class PlaylistTrace(BaseModel):
    playlist_token: str
    platform: Platforms
    platform_id: str
    mv_track_count: int
    follower_count: int


class TrackWhitelist(BaseModel):
    spotify_id_list: list[str] = []


class PlaylistTracking(BaseModel):
    available_slot_idx: int = 0
    slots: tuple[list[PlaylistTrace]] = tuple([] for _ in range(24))


class AppCore:
    def __init__(self, db_engine: DBEngine, dev_mode: bool = False, verbose: bool = True):
        self.db_engine = db_engine
        self.verbose = verbose
        self.dev_mode = dev_mode
        self.spotify_config = self.db_engine.get_config(config_type=ConfigTypes.spotify)
        self.spotify_controller = SpotifyController(client_id=self.spotify_config.client_id,
                                                    client_secret=self.spotify_config.client_secret)
        self.playlist_tracking = PlaylistTracking()

        self._init_playlist_tracking()

        if not self.dev_mode:
            per_hour = hour_rounder(datetime.now(timezone.utc))
            per_hour += timedelta(hours=1) if per_hour < datetime.now(timezone.utc) else timedelta()
            self.playlist_tracking_thread = CronThread(start_time=per_hour, recall_time=timedelta(hours=1),
                                                       target=self._playlist_tracking_job,
                                                       marker='playlist_tracking_thread')

            self.update_stats_thread = CronThread(start_time=per_hour, recall_time=timedelta(hours=1),
                                                  target=self._update_stats_job,
                                                  marker='update_stats_thread')

            self.top_playlists_emailing_thread = CronThread(start_time=per_hour + timedelta(minutes=5),
                                                            recall_time=timedelta(hours=1),
                                                            target=self._top_playlists_emailing_job,
                                                            marker='top_playlists_emailing_job_thread')

            general_info = self.db_engine.get_info(info_type=InfoTypes.general)
            next_top_time = general_info.last_snapshot_timestamp.replace(tzinfo=timezone.utc) + timedelta(seconds=general_info.snapshot_cycle)
            self.top_playlists_snapshot_thread = CronThread(start_time=next_top_time,
                                                            recall_time=timedelta(seconds=general_info.snapshot_cycle),
                                                            target=self._top_playlists_snapshots_job,
                                                            marker='weekly_playlist_top_job')

    def __del__(self):
        self.spotify_controller.__del__()
        if not self.dev_mode:
            self.playlist_tracking_thread.__del__()
            self.top_playlists_emailing_thread.__del__()
            self.top_playlists_snapshot_thread.__del__()
            self.update_stats_thread.__del__()

    def _init_playlist_tracking(self):
        playlists = self.db_engine.get_top_playlists()
        playlists += self.db_engine.get_sponsored_playlists()
        for playlist in playlists:
            trace = PlaylistTrace(playlist_token=playlist.token,
                                  platform=playlist.platform,
                                  platform_id=playlist.platform_id,
                                  mv_track_count=playlist.mv_track_count,
                                  follower_count=playlist.follower_count)
            self._track_playlist(playlist=trace)
        if self.verbose:
            sprint(f'[PLAYLIST_TRACKING] [LOADED] [{len(playlists)}]', Colors.light_green)

    def _update_playlist_trace(self, trace: PlaylistTrace):
        for s_idx, slot in enumerate(self.playlist_tracking.slots):
            for p_idx, playlist in enumerate(slot):
                if playlist.playlist_token == trace.playlist_token:
                    self.playlist_tracking.slots[s_idx][p_idx] = trace
                    return True
        return False

    def _update_stats_job(self):
        member_count = self.db_engine.get_join_members_count()
        self.db_engine.update_general_info(network_coverage=member_count)

    def _track_playlist(self, playlist: PlaylistTrace):
        idx = self.playlist_tracking.available_slot_idx
        self.playlist_tracking.slots[idx].append(playlist)
        self.playlist_tracking.available_slot_idx = idx + 1 if idx < 23 else 0

    def _playlist_tracking_job(self):
        current_hour = datetime.now(timezone.utc).hour
        for playlist in self.playlist_tracking.slots[current_hour]:
            self.check_playlist(playlist=playlist)

    def _top_playlists_snapshots_job(self):
        top_playlists = self.db_engine.get_top_playlists(limit=10)
        sponsored_playlists = self.db_engine.get_sponsored_playlists(limit=10)

        sponsor_idx = -2
        for spl in sponsored_playlists:
            sponsor_idx += 3
            top_playlists.insert(sponsor_idx, spl)

        top_playlists = top_playlists[:10]
        self.db_engine.add_top_playlists_snapshot(timestamp=hour_rounder(datetime.now(timezone.utc)),
                                                  playlists=top_playlists)

        self.db_engine.set_last_snapshot_timestamp(date=hour_rounder(datetime.now(timezone.utc)))

    def _top_playlists_emailing_job(self):
        snapshot = self.db_engine.get_top_playlists_snapshots(limit=1)[0]
        top_playlists = snapshot.top_playlists

        formatted_top_playlists = [EmailPlaylistModel(name=slice_format(text=pl.name, max_length=20),
                                   playlist_url=get_spotify_playlist_url(pl.platform_id),
                                   image_url=pl.image_path,
                                   follower_count=format_number(pl.follower_count),
                                   mv_track_count=format_number(pl.mv_track_count),
                                   sponsored=pl.sponsored) for pl in top_playlists]
        wrapped_top_playlists = group_into_bunches(data=formatted_top_playlists, bunch_size=2)

        context = TopPlaylistsEmailModel(app_url=WEB_APP_HOST,
                                         facebook_url='https://facebook.com/mvboxrecords',
                                         x_url='https://x.com/mvboxrecords',
                                         instagram_url='https://instagram.com/mvboxofficial',
                                         manage_notifications_url=WEB_APP_HOST,
                                         playlists=wrapped_top_playlists)

        mailgun = MailGunEngine(api_key=MAILGUN_API_KEY)
        email_user = self.db_engine.get_email_user(sender=SenderSlugs.community_team)

        active_members = self.db_engine.get_join_members(target={'news_subscription': True}, limit=5)

        members_batches = group_into_bunches(data=active_members, bunch_size=5)

        for batch in members_batches:
            template = TemplateEngine.top_playlists(recipient_email=[member.email for member in batch], data=context,
                                                    email_user=email_user)
            mailgun.send_email(template=template)
            if self.verbose:
                sprint(f'[EMAILING] [WEEKLY TOP] [SENT] [{len(batch)}]', Colors.light_cyan)
            for member in batch:
                self.db_engine.update_join_member(token=member.token, last_sent_news_date=datetime.now(timezone.utc))

    def check_playlist(self, playlist: PlaylistTrace):
        if playlist.platform is Platforms.spotify:
            playlist_info = self.spotify_controller.get_playlist(spotify_id=playlist.platform_id)
            tracks = self.spotify_controller.get_playlist_tracks(playlist_id=playlist.platform_id)
            track_ids = [track.spotify_id for track in tracks]

            mv_tracks = self.db_engine.get_mv_tracks()
            mv_tracks_ids = [track.sources[0].platform_id for track in mv_tracks]
            whitelist_count = len(set(mv_tracks_ids) & set(track_ids))

            updated_mv_track_count = None
            updated_follower_count = None
            if whitelist_count != playlist.mv_track_count:
                updated_mv_track_count = whitelist_count
                playlist.mv_track_count = whitelist_count
            if playlist_info.follower_count != playlist.follower_count:
                updated_follower_count = playlist_info.follower_count
                playlist.follower_count = playlist_info.follower_count

            self.db_engine.update_playlist(playlist_token=playlist.playlist_token,
                                           mv_track_count=updated_mv_track_count,
                                           follower_count=updated_follower_count)
            self._update_playlist_trace(trace=playlist)
        return playlist

    def track_new_playlist(self, platform_id: str, platform: Platforms):
        if platform is Platforms.spotify:
            playlist = self.spotify_controller.get_playlist(spotify_id=platform_id)
            new_user = SpotifyUser(name=playlist.owner.name,
                                   follower_count=playlist.owner.follower_count,
                                   spotify_id=playlist.owner.spotify_id)
            user_token = new_user.token
            if not self.db_engine.add_spotify_user(user=new_user):
                spotify_user = self.db_engine.get_spotify_user_by_spotify_id(spotify_id=new_user.spotify_id)
                user_token = spotify_user.token

            new_playlist = Playlist(owner_token=user_token,
                                    platform=platform,
                                    platform_id=platform_id,
                                    name=playlist.name,
                                    description=playlist.description,
                                    image_path=playlist.image_url,
                                    follower_count=playlist.follower_count,
                                    track_count=playlist.track_count)
            self.db_engine.add_playlist(new_playlist)

            trace = PlaylistTrace(playlist_token=new_playlist.token,
                                  platform=new_playlist.platform,
                                  platform_id=new_playlist.platform_id,
                                  mv_track_count=new_playlist.mv_track_count,
                                  follower_count=new_playlist.follower_count)
            self._track_playlist(playlist=trace)
            trace = self.check_playlist(playlist=trace)

            new_playlist.mv_track_count = trace.mv_track_count
            new_playlist.follower_count = trace.follower_count
        if self.verbose:
            sprint(f'[PLAYLIST_TRACKING] [NEW] [{platform.value.upper()}] [{platform_id}]', Colors.light_cyan)
        return new_playlist

    def add_track(self, platform_id: str, platform: Platforms):
        if platform is Platforms.spotify:
            if self.db_engine.check_track_existence(platform_id=platform_id, platform=platform):
                raise Exception('Track already exists')

            spotify_track: SpotifyTrack = try_extract(lambda: self.spotify_controller.get_tracks_info(track_ids=[platform_id])[0])
            if not spotify_track:
                raise Exception('Track not found')

            if not (artist := self.db_engine.get_artist_by_platform(platform_id=spotify_track.artist.spotify_id,
                                                                    platform=Platforms.spotify)):
                artist = Artist(name=spotify_track.artist.name,
                                image_path=spotify_track.artist.image_url,
                                sources=[ArtistSource(platform=Platforms.spotify,
                                                      platform_id=spotify_track.artist.spotify_id,
                                                      follower_count=spotify_track.artist.follower_count)])
                self.db_engine.add_artist(artist=artist)

            track = Track(artist_token=artist.token,
                          sources=[TrackSource(platform=Platforms.spotify, platform_id=spotify_track.spotify_id)],
                          name=spotify_track.name,
                          image_path=spotify_track.album.image_url,
                          mv_pass=True)

            self.db_engine.add_track(track=track)
            return track
        return None
        # TODO Todo check if a main object already exists for multiple platforms
