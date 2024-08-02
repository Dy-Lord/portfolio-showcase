import enum
import traceback
from copy import copy
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


def reset_color():
    print(Style.RESET_ALL)


def timedelta_to_hours(delta: timedelta):
    return round(delta.total_seconds() / 3600, 4)


def hour_rounder(t: datetime):
    return t.replace(second=0, microsecond=0, minute=0)


def day_rounder(t: datetime):
    return t.replace(second=0, microsecond=0, minute=0, hour=0)


def try_extract(func, default_value=None):
    try:
        return func()
    except:
        return default_value


def get_scope_description(scopes: list[str]):
    return f'**SCOPES:\t[ {" ".join(scopes)} ]**'


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


class CacheStorage:
    def __init__(self, default_expiration: timedelta = None):
        self.default_expiration = default_expiration
        self.storage = {}
        self.index_dict = {}
        self.jobs: dict[str, CronThread] = {}

    def __del__(self):
        for key in list(self.jobs.keys()):
            self.jobs.pop(key).terminate()

    def add_index(self, obj_id: str, alter_id: str):
        self.index_dict.update({alter_id: obj_id})

    def get_object(self, obj_id: str):
        obj = try_extract(lambda: self.storage[obj_id]['data'])
        if obj is None:
            alter_id = try_extract(lambda: self.index_dict[obj_id])
            if alter_id is not None:
                obj = try_extract(lambda: self.storage[alter_id]['data'])
        return obj

    def get_object_expiration_time(self, obj_id: str):
        expiration = try_extract(lambda: self.storage[obj_id]['expires_in'])
        if expiration is None:
            alter_id = try_extract(lambda: self.index_dict[obj_id])
            if alter_id is not None:
                expiration = try_extract(lambda: self.storage[alter_id]['expires_in'])
        return expiration

    def delete_object(self, obj_id: str):
        if try_extract(lambda: self.storage.pop(obj_id)):
            for key, item in copy(self.index_dict).items():
                if item == obj_id:
                    self.index_dict.pop(key)
            try_extract(lambda: self.jobs.pop(obj_id))

    def add_object(self, obj_id: str, obj: dict, expiration: timedelta = None):
        if expiration is None:
            expiration = self.default_expiration if self.default_expiration is not None else timedelta(0)

        expires_in = datetime.now(timezone.utc) + expiration
        new_obj = {
            obj_id: {
                'data': obj,
                'expires_in': expires_in
            }
        }
        self.storage.update(new_obj)
        if expires_in:
            expiration_job = CronThread(start_time=expires_in, target=lambda: self.delete_object(obj_id),
                                        call_limit=1, marker=f'{obj_id}_object_expiration')
            self.jobs.update({obj_id: expiration_job})

