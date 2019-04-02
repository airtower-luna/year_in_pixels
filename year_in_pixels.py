#!/usr/bin/python3
# PYTHON_ARGCOMPLETE_OK

# Copyright (c) 2019 Fiona Klute
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Year in Pixels logger and renderer

Idea from: https://twitter.com/JuniperDog/status/1077993408885600261"""
import csv
import matplotlib.pyplot as plt
from datetime import datetime, date
from enum import Enum, auto, unique

# Color definitions (red, green, blue)
pink = (0xff, 0, 0xff)
lblue = (0, 0xff, 0xff)
mblue = (0, 0, 0xff)
green = (0, 0xff, 0)
navy = (0, 0, 0x80)
yellow = (0xff, 0xff, 0)
orange = (0xff, 0xa5, 0x00)
black = (0, 0, 0)

@unique
class DayMood(Enum):
    """Supported moods for each day"""
    amazing = ('amazing, fantastic day', pink)
    good = ('really good, happy day', lblue)
    normal = ('normal, average day', mblue)
    tired = ('exhausted, tired day', green)
    sad = ('depressed, sad day', navy)
    angry = ('frustrated, angry day', yellow)
    stressed = ('stressed out, frantic day', orange)

    def __init__(self, desc, color):
        # Description string for the mood
        self.desc = desc
        # Color to display a day with this mood
        self.color = color

class DayEntry:
    """Daily mood entry, containing the date, mood (see DayMood), and
    optionally a comment.

    """
    def __init__(self, date, mood, comment):
        self.date = date
        self.mood = mood
        self.comment = comment

    def __repr__(self):
        return 'DayEntry({}, {}, {})'.format(repr(self.date),
                                             self.mood,
                                             repr(self.comment))

    def __str__(self):
        if self.comment:
            return '{}: {} ({})'.format(self.date,
                                        self.mood.desc,
                                        self.comment)
        else:
            return '{}: {}'.format(self.date, self.mood.desc)

    def to_dict(self):
        return {'date': self.date,
                'mood': self.mood.name,
                'comment': self.comment}

def date_from_iso(s):
    """
    >>> date_from_iso('2019-01-14')
    datetime.date(2019, 1, 14)
    """
    return datetime.strptime(s, '%Y-%m-%d').date()

def display_year(days):
    """Format a list of days into a year chart.

    WARNING: This function ASSUMES that 'days' contains entries from
    only one calendar year.
    """
    # Plot modified from:
    # https://matplotlib.org/gallery/images_contours_and_fields/image_zcoord.html
    # See also: https://matplotlib.org/api/_as_gen/matplotlib.axes.Axes.imshow.html
    w = 12
    h = 31
    X = [[black for x in range(w)] for y in range(h)]
    # first coordinate: day, second coordinate: month (each -1)
    for d in days:
        X[d.date.day - 1][d.date.month - 1] = d.mood.color
    fig, ax = plt.subplots()
    ax.imshow(X, interpolation='none')
    plt.show()

def read_days_from_file(file):
    with open(file, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        return [
            DayEntry(date_from_iso(row['date']),
                     DayMood[row['mood']],
                     row['comment'])
            for row in reader
        ]
    return None

def enter_daily_data():
    d = date.today()
    print('Which date do you want to log for? [{}]'.format(d))
    s = input('> ')
    if s:
        try:
            d = date_from_iso(s)
        except ValueError:
            print('Invalid date: "{}"'.format(s))
            exit(1)
    if d == date.today():
        s = 'today'
    else:
        s = 'on {}'.format(d)
    print('How was your mood {}? Please enter one of the following:'
          .format(s))
    for m in DayMood:
        print('  {:<10}{}'.format(m.name, m.desc))
    s = input('> ')
    try:
        mood = DayMood[s]
    except KeyError:
        print('Invalid mood string: "{}"'.format(s))
        exit(1)
    print('If you like, you can enter a comment how this was a {} day.'
          .format(mood.name))
    comment = input('> ')
    return DayEntry(d, mood, comment)

if __name__ == "__main__":
    @unique
    class Command(Enum):
        render = 'render'
        log = 'log'

        def __str__(self):
            return self.name

    import argparse
    import tempfile

    parser = argparse.ArgumentParser(description="Year in Pixels logger "
                                     "and renderer")
    parser.add_argument("command",
                        help='command to execute, default: "render"',
                        nargs="?", default="render",
                        type=Command, choices=list(Command))
    # TODO: $HOME based default, possibly configurable. Maybe
    # something like ~/.year_in_pixels/YEAR.csv?
    parser.add_argument("-f", "--file", default='year_in_pixels.csv',
                        help='file for daily log data')

    # enable bash completion if argcomplete is available
    try:
        import argcomplete
        argcomplete.autocomplete(parser)
    except ImportError:
        pass

    args = parser.parse_args()

    if args.command is Command.render:
        days = read_days_from_file(args.file)
        if days:
            display_year(days)

    elif args.command is Command.log:
        day = enter_daily_data()
        print(str(day))
        print(repr(day))

        try:
            days = read_days_from_file(args.file)
        except FileNotFoundError:
            days = []
        days = list(filter(lambda d: d.date != day.date, days))
        # TODO: Maybe (re-)sort the list by date, or insert the new
        # entry at a specific position. Could apply sorted() builtin
        # to the filter output before collecting into a list.
        # file:///usr/share/doc/python3/html/library/functions.html#sorted
        days.append(day)

        with tempfile.NamedTemporaryFile(delete=False, newline='', mode='w') as csvout:
            fieldnames = ['date', 'mood', 'comment']
            writer = csv.DictWriter(csvout, fieldnames=fieldnames, dialect='unix')
            writer.writeheader()
            for d in days:
                writer.writerow(d.to_dict())
            print(csvout.name)

        # move the temporary file to replace the previous version
        import shutil
        shutil.move(csvout.name, args.file)
