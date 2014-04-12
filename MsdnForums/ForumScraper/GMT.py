__author__ = 'Stephen'

from datetime import datetime, tzinfo, timedelta

class GMT(tzinfo):
      def utcoffset(self, dt):
          return timedelta(hours=0)
      def dst(self, dt):
          return timedelta(0)
      def tzname(self,dt):
           return "GMT"