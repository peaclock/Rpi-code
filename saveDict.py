# ==========================================================================================================
# Create a textfile to save all cities and their timezones.
# Run this once initially to save all data on the Pi, so final_code_with_time_adjust.py will reference this.
# Textfile should have two columns: city, and respective timezone.
# ==========================================================================================================
import os
from urllib import urlretrieve
from urlparse import urljoin
from zipfile import ZipFile

geonames_url = 'http://download.geonames.org/export/dump/'
basename = 'cities15000' # all cities with a population > 15000 or capitals
filename = basename + '.zip'

# get file
if not os.path.exists(filename):
    urlretrieve(urljoin(geonames_url, filename), filename)
f = open("tzdict.txt","w")
# parse it
city2tz = {}
with ZipFile(filename) as zf, zf.open(basename + '.txt') as file:
    line = file.readline()
    while line:
        fields = line.split(b'\t')
        if fields: # geoname table http://download.geonames.org/export/dump/
            asciiname = fields[2]
            timezone = fields[-2]
            if timezone:
                city2tz[asciiname] = timezone
                f.write('{} {}'.format(asciiname, timezone)) # make two columns in textfile
                f.write('\n')
        line = file.readline()
f.close()
