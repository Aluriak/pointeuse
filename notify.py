"""Run notify-send whenever given amount of hours of work is reached"""

import argparse
import subprocess
import temps

def parse_cli():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--hours-per-day', type=float, help="how many hours you should work per day to reach your total workload", default=7.4)
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_cli()
    stats = temps.run('stats', hours_per_day=args.hours_per_day)
    if stats['total_difftime'] > 10:
        sup = temps.minutes_to_hr(stats['total_difftime'])
        subprocess.Popen(['notify-send', f'OVERWORK: {sup}'])
    if stats['total_difftime'] < 10:
        sup = temps.minutes_to_hr(-stats['total_difftime'])
        subprocess.Popen(['notify-send', f'WORK NEEDED: {sup}'])
