import csv
import sys
import os
from datetime import datetime
from pytz import timezone

orig_file = sys.argv[1]
new_file = sys.argv[2]
interim_file = 'tempfile.csv'

# something is funny, the offset between the two is right, but it's not always doing DST correctly, I think
pacific = timezone('US/Pacific')
eastern = timezone('US/Eastern')

replacement_char_bytes = b'\xef\xbf\xbd'


def get_seconds(timestring):
    timestring = timestring.split(':')
    seconds = float(timestring[0])*3600+float(timestring[1])*60+float(timestring[2])
    return seconds


# Could make this only happen in an except if there's a UnicodeDecodeError from the csv reader
with open(orig_file, "rb") as f:
    file_bytes = f.read()
    utf8 = file_bytes.decode(encoding='utf-8', errors='replace')

# It would be better to not write and then immediately open this.
# Using for convenience now, to get benefit of csv reader/writer
with open(interim_file, 'w', encoding='utf-8') as interim:
    interim.write(utf8)

# Using dictreader would be more reader-friendly, to use headers instead of row indices.
with open(interim_file, 'r', encoding='utf-8') as interim:
    reader = csv.reader(interim)
    rows = list(reader)

keep_rows = [rows[0]]

# Go through each line and fix the time format. First row is headers.
for row in rows[1:]:
    # this is clunky here, ran up against time. would be better as a function or a class method.
    bad_char = False
    parse_sensitive = [row[0], row[2], row[4], row[5], row[7]] #7 added for testing
    for item in parse_sensitive:
        if replacement_char_bytes.decode('utf-8') in item:
            print(f'WARNING: Row removed due to invalid unicode character: {row}', file=sys.stderr)
            bad_char = True
    if bad_char:
        continue  # prevents row from being processed and appended to list to write
    # time stuff
    date_obj = datetime.strptime(row[0], "%m/%d/%y %H:%M:%S %p")
    # print('plain date', date_obj.isoformat())
    tz_aware = pacific.localize(date_obj)
    # print('pacific time', tz_aware.isoformat())
    est_time = tz_aware.astimezone(eastern)
    # print('eastern time', est_time.isoformat())
    row[0] = est_time.isoformat()
    # zip code stuff
    row[2] = row[2].zfill(5) # Numbers and excel both delete leading zeroes
    # Full name to upper
    row[3] = row[3].upper()
    # FooDuration
    row[4] = get_seconds(row[4])
    # BarDuration
    row[5] = get_seconds(row[5])
    # TotalDuration
    row[6] = row[4]+row[5]
    keep_rows.append(row)

with open(new_file, 'w', encoding='utf-8') as normalized:
    writer = csv.writer(normalized)
    writer.writerows(keep_rows)

# Clean up file that doesn't need to be seen
os.remove(interim_file)
