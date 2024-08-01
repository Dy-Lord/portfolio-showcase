import enum
import re
import traceback
from datetime import timedelta, datetime, timezone
from threading import Timer

from colorama import Fore, Style


class Colors(enum.Enum):
    light_green = Fore.LIGHTGREEN_EX
    light_yellow = Fore.LIGHTYELLOW_EX
    light_blue = Fore.LIGHTBLUE_EX
    light_magenta = Fore.LIGHTMAGENTA_EX
    light_cyan = Fore.LIGHTCYAN_EX
    light_red = Fore.LIGHTRED_EX
    light_black = Fore.LIGHTBLACK_EX


def sprint(text: str, color: Colors = Colors.light_yellow, permanent: bool = False):
    print(color.value + text + (Style.RESET_ALL if not permanent else ''))


def validate_email_format(email: str):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def base62_validator(data: str):
    return bool(re.fullmatch("^[0-9A-Za-z_-]{22}$", data))


def extract_spotify_id_from_urs(url: str):
    return url.split('?')[0].split('/')[-1]


def timedelta_to_hours(delta: timedelta):
    return round(delta.total_seconds() / 3600, 4)


def hour_rounder(t: datetime):
    return t.replace(second=0, microsecond=0, minute=0)


def day_rounder(t: datetime):
    return t.replace(second=0, microsecond=0, minute=0, hour=0)


def next_weekday(d: datetime, weekday: int):
    d = d.replace(second=0, microsecond=0, minute=0, hour=0)
    days_ahead = weekday - d.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    return d + timedelta(days_ahead)


def try_extract(func, default_value=None):
    try:
        return func()
    except:
        return default_value


def get_scope_description(scopes: list[str]):
    return f'**SCOPES:\t[ {" ".join(scopes)} ]**'


def get_spotify_playlist_url(playlist_id: str):
    return f'https://open.spotify.com/playlist/{playlist_id}'


def get_spotify_track_url(playlist_id: str):
    return f'https://open.spotify.com/track/{playlist_id}'


def format_number(num):
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    return '%.0f%s' % (num, ['', 'K', 'M', 'G', 'T', 'P'][magnitude])


def slice_format(text: str, max_length: int):
    return text[:max_length] + '...' if len(text) > max_length else text


def group_into_bunches(data: list, bunch_size: int):
    return [data[i:i+bunch_size] for i in range(0, len(data), bunch_size)]


class RepeatThread(Timer):
    def run(self):
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)


class CronThreadEvents(enum.Enum):
    terminate = 'terminate'


class CronThread:
    def __init__(self, start_time: datetime, target: object, recall_time: timedelta = timedelta(hours=24),
                 marker: str = None, round_next_month: bool = False, call_limit: int = None, silent_mode: bool = False):
        self.marker = marker
        self.next_call = None
        self.target = target
        self.recall_time = recall_time
        self.start_time = start_time
        self.round_next_month = round_next_month
        self.call_limit = call_limit
        self.silent_mode = silent_mode

        assert call_limit is None or call_limit > 0, 'The call limit must be greater than 0'
        assert self.start_time > datetime.now(timezone.utc), 'The start time must be in the future and in UTC format'

        self.next_call = self.start_time - datetime.now(timezone.utc)

        if not self.silent_mode:
            sprint(f'CronThread [{self.marker}] next job call in [{self.next_call}] at [{self.start_time}]', Colors.light_green)
        self.cron_thread = RepeatThread(self.next_call.total_seconds(), self.cron_job)
        self.cron_thread.start()

    def __del__(self):
        if not self.silent_mode:
            sprint(f'CronThread [{self.marker}] shutting down...', Colors.light_red)
        self.cron_thread.cancel()

    def terminate(self):
        self.__del__()

    def cron_job(self):
        current_cron = self.cron_thread
        current_cron.cancel()

        self.start_time += self.recall_time
        if self.round_next_month:
            self.start_time = self.start_time.replace(day=1)
        self.next_call = self.start_time - datetime.now(timezone.utc)

        if self.call_limit is not None:
            self.call_limit -= 1
            if self.call_limit == 0:
                if not self.silent_mode:
                    sprint(f'CronThread [{self.marker}] All jobs has been completed', Colors.light_cyan)

        if self.call_limit is None or self.call_limit > 0:
            if not self.silent_mode:
                sprint(f'CronThread [{self.marker}] next job call in [{self.next_call}]', Colors.light_green)
            self.cron_thread = RepeatThread(self.next_call.total_seconds(), self.cron_job)
            self.cron_thread.start()

        try:
            response = self.target()
            if response is CronThreadEvents.terminate:
                if not self.silent_mode:
                    sprint(f'CronThread [{self.marker}] Job terminated via termination response', Colors.light_red)
                self.cron_thread.cancel()
        except:
            print(f'CronThread [{self.marker}] Job exception')
            print(traceback.format_exc())

