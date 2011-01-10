from django.conf import settings
from django.core.management.base import BaseCommand
from django.contrib.gis.geos import fromstr as geo_from_str

import os
import logging
import time
import re
import datetime

from gheat_kazni.kazni.models import KazenTocka

from geopy import geocoders

class Command(BaseCommand):

    def handle(self, *args, **options):
	help = 'Parses the prepared kazni.txt'

	LOG_FILENAME = 'kazni_parser.log'
	logging.basicConfig(filename=LOG_FILENAME,level=logging.DEBUG)

	file = open(args[0], 'r')

	g = geocoders.Google('ABQIAAAAVlqrrVSbz3C1GeepsZahiRQlxAPqwOs55Ezp72xHBnWJQMD8ORTctpF5AovPLRFPNxMhkOQYYTLKpw')

	for line in file:
		index = int(line.split(';')[0])
		name = line.split(';')[1]
		date_parsed = line.split(';')[2]
		penalty_parsed = line.split(';')[3].strip()
		try:
			penalty = int(penalty_parsed)
		except:
			penalty = int(penalty_parsed.rpartition(',')[0].replace('.', ''))

		date_re = re.search('(\d{1,2})\.(\d{1,2})\.(\d{4})\s(\d{1,2}):(\d{2})', date_parsed)
		date = datetime.datetime(int(date_re.group(3)), int(date_re.group(2)), int(date_re.group(1)), int(date_re.group(4)), int(date_re.group(5)))
		logging.debug('Processing: %d, %s' % (index, name))
	
		# if index already in db, don't import
		if not KazenTocka.objects.filter(index__exact=index):

			# if name already exists in db ...
			if KazenTocka.objects.filter(name__exact=name).count() != 0:
				# ... use its geometry
				geometry = KazenTocka.objects.filter(name__exact=name)[0].geometry
				entry = KazenTocka(
						name = name,
						index = index,
						geometry = geometry,
						date = date,
						penalty = penalty
					)
				entry.save()
				logging.debug('Using geometry from from an already inserted street.')
				logging.debug('Inserted: %d, %s, %s, %s, %s' % (index, name, geometry, date, penalty))
			
			# if it's not in the db, ask google for geometry
			else:
				try:
					# wait a bit so we won't make google angry
					time.sleep(0.5)

					place = list(g.geocode(name, exactly_one=False))[0]
		
					latitude = place[1][0]
					longitude = place[1][1]

					coordstr = "POINT(%s %s)" % (longitude, latitude)
					entry = KazenTocka(
							name = name,
							index = index,
							geometry = geo_from_str(coordstr),
							date = date,
							penalty = penalty
						)
					entry.save()
					logging.debug('Using geometry from google')
					logging.debug('Inserted: %d, %s, %s, %s, %s' % (index, name, geometry, date, penalty))

				except geocoders.google.GTooManyQueriesError:
					logging.debug('Google blocked us!')
					sys.exit(1)
				except Exception, e:
					logging.debug(e)
		else:
			logging.debug('Skipping, index already in the db...')
