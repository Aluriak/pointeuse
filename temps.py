#!/usr/bin/env python3
"""Save effective working hours, and compute general stats on it.

"""

import argparse
import datetime
import csv
from collections import defaultdict

ACTIONS = 'arrive', 'quit', 'stats'


def parse_cli():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=ACTIONS, type=str, help="what to do")
    parser.add_argument('--dry-run', '-d', action='store_true', help="don't modify anything")
    parser.add_argument('--overwrite', '-o', action='store_true', help="if data already exists, overwrite it")
    parser.add_argument('--porcelain', '-p', action='store_true', help="output data in a parsable way")
    parser.add_argument('--hours-per-day', type=float, help="how many hours you should work per day to reach your total workload", default=None)
    parser.add_argument('--not-today', '-n', action='store_true', help="don't consider today in stats")
    parser.add_argument('--timefile', '-f', type=str, default='./temps', help="The file containing the times")
    return parser.parse_args()


class Entry:

    def __init__(self, date_base, time_start, time_stop):
        self.date_base = date_base
        self.time_start = time_start
        self.time_stop = time_stop

    def __str__(self) -> str:
        return ' '.join(tuple(self))

    def __iter__(self) -> iter:
        yield from (self.hr_date, self.hr_start, self.hr_stop)

    @property
    def hr_date(self) -> str:
        "Human readable date"
        return self.date_base.strftime("%y/%m/%d")

    @property
    def hr_start(self) -> str:
        "Human readable time"
        return self.time_start.strftime("%Hh%M")

    @property
    def hr_stop(self) -> str:
        "Human readable time"
        return '' if self.is_unfinished() else self.time_stop.strftime("%Hh%M")

    @property
    def working_time(self) -> datetime.time:
        "describe how much work time was produced"
        start = self.time_start.hour * 60 + self.time_start.minute
        if self.is_unfinished():
            now = datetime_time_from_now()
            stop = now.hour * 60 + now.minute
        else:
            stop = self.time_stop.hour * 60 + self.time_stop.minute
        working_time = stop - start
        return datetime.time(hour=working_time // 60, minute=working_time % 60)

    def is_unfinished(self) -> bool:
        return self.time_stop is None

    def is_today(self) -> bool:
        return self.hr_date == date_from_now()

    def set_finish_now(self):
        assert self.is_unfinished(), self
        self.time_stop = datetime_time_from_now()

    def set_start_now(self):
        assert self.is_unfinished(), self
        self.time_start = datetime_time_from_now()


    @staticmethod
    def from_tuple(date_, start, stop):
        date = datetime_date_from_date(date_)
        date_start = datetime_time_from_hour(start)
        if stop is None or stop == '':
            date_stop = None
        else:
            date_stop = datetime_time_from_hour(stop)
        return Entry(date, date_start, date_stop)

    @staticmethod
    def now_arrived():
        return Entry.from_tuple(date_from_now(), time_from_now(), None)


def datetime_from_date_and_time(date:datetime.date, time:datetime.time) -> datetime.datetime:
    return datetime.datetime(year=date.year, month=date.month, day=date.day, hour=time.hour, minute=time.minute)

def date_from_now() -> str:
    return datetime.datetime.now().strftime("%y/%m/%d")

def time_from_now() -> str:
    return datetime.datetime.now().strftime("%Hh%M")

def datetime_time_from_now() -> datetime.time:
    now = datetime.datetime.now()
    return datetime.time(hour=now.hour, minute=now.minute)

def datetime_time_from_hour(hour:str) -> datetime.time:
    if hour is None: return None
    _ = datetime.datetime.strptime(hour, "%Hh" if hour.endswith('h') else "%Hh%M")
    return datetime.time(_.hour, _.minute)

def datetime_date_from_date(date:str) -> datetime.date:
    _ = datetime.datetime.strptime(date, "%y/%m/%d")
    return datetime.date(_.year, _.month, _.day)


def get_data(fname:str='temps'):
    with open(fname) as fd:
        reader = csv.reader(fd, delimiter=',')
        for date, start, stop in reader:
            yield Entry.from_tuple(date, start, stop)

def set_data(entries:[Entry], fname:str='temps'):
    with open(fname, 'w') as fd:
        for entry in entries:
            writer = csv.writer(fd, delimiter=',')
            writer.writerow(tuple(entry))

def add_data(entry:Entry, fname:str='temps'):
    with open(fname, 'a') as fd:
        writer = csv.writer(fd, delimiter=',')
        writer.writerow(tuple(entry))



def run(action, entries:[Entry]=None, overwrite:bool=False, dry_run:bool=False, hours_per_day:float=7.4, porcelain:bool=False, include_today:bool=True) -> str or None or [Entry]:
    if entries is None:
        entries = tuple(get_data())
    if porcelain:
        print = lambda *a, **k: None
    else:
        print = __builtins__.print
    assert max(date for date, _, _ in entries) == entries[-1].hr_date
    last_entry_is_today = entries[-1].hr_date == Entry.now_arrived().hr_date
    diff = Entry.now_arrived().date_base - entries[-1].date_base
    if last_entry_is_today:
        print('Last entry is today.')
    else:
        print(f'Last entry is {diff} ago.')

    if action == 'arrive':
        if entries[-1].is_unfinished():
            if args.overwrite:
                entries[-1].set_start_now()
                print('Changed last arrival at now.')
            else:  # just report the error
                return print('Oops! The last entry is unfinished. You either never quit, or used the wrong command.')
        else:
            entries = entries + (Entry.now_arrived(),)
            print('Added a new entry, arrival now.')

    elif action == 'quit':
        if entries[-1].is_unfinished():
            entries[-1].set_finish_now()
            print('Changed last entry, quitting now.')
        else:
            if args.overwrite:
                entries[-1].set_finish_now()
                print('Changed last quit at now.')
            else:
                return print('Oops! No unfinished entry. You either never arrived, or used the wrong command.')

    elif action == 'stats':
        outdata = {}  # used if porcelain mode is active
        workamount = defaultdict(int)  # day -> worktime amount in minutes
        total_worktime = 0
        if not include_today:
            entries = list(entries)
            while entries[-1].hr_date == Entry.now_arrived().hr_date:
                entries.pop()
            entries = tuple(entries)
        for entry in entries:
            worktime = entry.working_time
            worktime = (worktime.hour * 60 + worktime.minute)
            total_worktime += worktime
            workamount[entry.hr_date] += worktime

        outdata['nb_day'] = len(workamount)
        outdata['first_day'] = entries[0].hr_date
        outdata['last_day'] = entries[-1].hr_date
        desc_today = 'in' if include_today else 'ex'
        print(f"Statistics on {outdata['nb_day']} worked days ({desc_today}cluding today), from {outdata['first_day']} to {outdata['last_day']}")
        print(f"You worked a total of {minutes_to_hr(total_worktime)}.")
        outdata['total_worktime'] = total_worktime

        if hours_per_day:
            optimal_worktime = int(hours_per_day * 60)
            difftime = []  # list of deviation from hour_per_day
            for day in workamount:
                # print(day, workamount[day])
                difftime.append(workamount[day] - optimal_worktime)
            outdata['total_difftime'] = sum(difftime)
            if outdata['total_difftime'] > 0:
                print(f"You worked {minutes_to_hr(outdata['total_difftime'])} too much since {entries[0].hr_date}.")
            else:
                print(f"You have to work {minutes_to_hr(-outdata['total_difftime'])} much.")

        outdata['average_per_day'] = round(sum(workamount.values()) / len(workamount))
        print(f"You are working an average of {minutes_to_hr(outdata['average_per_day'])} per day.")

        if porcelain:
            for k, v in outdata.items():
                __builtins__.print(k, v)
            return outdata
        else:
            return outdata

    return entries


def minutes_to_hr(minutes:int) -> str:
    return "{:02d}h{:02d}m".format(minutes // 60, minutes % 60)
def datetime_time_to_minutes(time:datetime.time) -> int:
    return time.minute + time.hour * 60


if __name__ == '__main__':
    args = parse_cli()
    entries = tuple(get_data(args.timefile))
    ret = run(args.action, entries, args.overwrite, args.dry_run, args.hours_per_day, args.porcelain, not args.not_today)
    if ret and not args.dry_run:
        if isinstance(ret, tuple) and all(isinstance(e, Entry) for e in ret):
            set_data(ret)
        else:
            pass
