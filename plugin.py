###
# Copyright (c) 2015, reticulatingspline
# All rights reserved.
#
#
###
import requests
from bs4 import BeautifulSoup
import re
import datetime
from time import time
import re
# supybot libs
import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('Scores')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x


class Scores(callbacks.Plugin):
    """sports scores"""
    threaded = True

    def __init__(self, irc):
        self.__parent = super(Scores, self)
        self.__parent.__init__(irc)
        self.DAYS = ['yesterday', 'tonight', 'today', 'tomorrow'] #, 'sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']

    ##############
    # FORMATTING #
    ##############

    def _red(self, string):
        """Returns a red string."""
        return ircutils.mircColor(string, 'red')

    def _yellow(self, string):
        """Returns a yellow string."""
        return ircutils.mircColor(string, 'yellow')

    def _green(self, string):
        """Returns a green string."""
        return ircutils.mircColor(string, 'green')

    def _bold(self, string):
        """Returns a bold string."""
        return ircutils.bold(string)

    def _ul(self, string):
        """Returns an underline string."""
        return ircutils.underline(string)

    def _bu(self, string):
        """Returns a bold/underline string."""
        return ircutils.bold(ircutils.underline(string))

    def _sf(self, string):
        """Returns a string with stripped formatting."""
        return ircutils.stripFormatting(string)

    ####################
    # HELPER FUNCTIONS #
    ####################


    def _datetodatetime(self, optdate):
        """Convert a string like yesterday to datetime object and return YYYYMMDD string."""

        if optdate == "lastweek":
            datedelta = -7
        elif optdate == "yesterday":
            datedelta = -1
        elif optdate == "today" or optdate =="tonight":
            datedelta = 0
        elif optdate == "tomorrow":
            datedelta = 1
        elif optdate == "nextweek":
            datedelta = 7
        elif optdate in self.DAYS:  # weekday.
            weekdaynum = self.DAYS.index(optdate)  # day of the week (index) requested.
            dayoftheweek = datetime.datetime.now().isoweekday()  # today's day.
            if weekdaynum >= dayoftheweek:  # if day is ahead but not next week.
                datedelta = weekdaynum - dayoftheweek  # simple +math.
            else:
                datedelta = 7+(weekdaynum-dayoftheweek)  # add in the -dayoftheweek
        # calculate the datedelta and return a string.
        datestr = (datetime.date.today() + datetime.timedelta(days=datedelta)).strftime('%Y-%m-%d')
        # now return.
        return datestr

    def _boldleader(self, atm, asc, htm, hsc):
        """Input away team, away score, home team, home score and bold the leader of the two."""

        if int(asc) > int(hsc):  # away winning.
            #self.log.info("HOME: {0} {1} {2} {3}".format(atm, asc, htm, hsc))
            #return("{0} {1} {2} {3}".format(self._bu(atm), self._bu(asc), htm, hsc))
            return("{0} {1}".format(self._bold(atm + " " + asc), self._sf(htm + " " + hsc)))
        elif int(hsc) > int(asc):  # home winning.
            #self.log.info("AWAY: {0} {1} {2} {3}".format(htm, hsc, atm, asc))
            return("{0} {1}".format(self._sf(atm + " " + asc), self._bold(htm + " " + hsc)))
            # return("{0} {1} {2} {3}".format(atm, asc, self._bu(htm), self._bu(hsc)))
        else:  # tied.
            return("{0} {1} {2} {3}".format(atm, asc, htm, hsc))

    def _fetch(self, optsport, date=None):
        """Fetch and return HTML."""

        if date:
            url = "http://m.yahoo.com/w/sports/%s/scores?date=%s&.ts=%s&.intl=us&.lang=en" % (date, optsport, time.time())
        else:
            url = "http://m.yahoo.com/w/sports/%s/scores?.ts=%s&.intl=us&.lang=en" % (optsport, time.time())
        try:
            headers = {"User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:17.0) Gecko/17.0 Firefox/17.0"}
            page = requests.get(url, headers=headers, verify=False)
            return page
        except Exception as e:
            self.log.error("ERROR. Could not open {0} message: {1}".format(url, e))
            return None

    def _urlfetch(self, url):
        """Fetch and return HTML."""

        try:
            headers = {"User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:17.0) Gecko/17.0 Firefox/17.0"}
            page = requests.get(url, headers=headers, verify=False)
            return page
        except Exception as e:
            self.log.error("ERROR. Could not open {0} message: {1}".format(url, e))
            return None

    def _parseline(self, l):
        # OAK 1 HOU 6 Final
        # LAD 0 SFO 4 Bot 8
        # NYR 2 TAM 0 9:15 1st
        # CHC @ SDG 10:10
        # MIN 4 PIT 3 Final 13 
        ls = l.split(' ')  # we split on space.
        # lets check on the length of the split
        llen = len(ls)
        # lets wrap in try except.
        try:
            if "@" in l:  # game has not started. return base string.
                return l
            elif llen == 5:  # this should match Final but not Final 13 or Final OT
                # bold the leader and color everything after.
                return l
            elif llen == 6:  # this should match an active game.
                return l
        except Exception as e:
            self.log.info("_parseline :: ERROR :: {0}".format(e))
            return l

    def _scores(self, html):
        """Go through each "game" we receive and process the data."""

        soup = BeautifulSoup(html)
        games = soup.findAll('div', attrs={'class':'uip'}) # re.compile('^uic$')}) #'uip'})
        gameslist = []
        # go through each game
        for game in games:
            #self.log.info("{0}".format(game))
            gametext = game.getText(separator=' ')
            gametext = ' '.join(gametext.split())
            gametext = gametext.replace('Eastern ', '').replace('Western ', '')
            gametext = gametext.replace(' EDT', '').replace(' pm', '').replace(' am', '')
            gametext = gametext.strip()
            #self.log.info("{0}".format(gametext))
            # some exceptions.
            if gametext == "Final":
                continue
            else:
                gameslist.append(gametext)
        # return the list of games.
        return gameslist

    ###################################
    # PUBLIC FUNCTIONS (ONE PER SPORT #
    ###################################
    
    # FUTURE IDEA http://sports.yahoo.com/__xhr/sports/scoreboard/gs/?lid=nhl&week=&date=2015-04-23&phase=&conf=&division=&season=&format=realtime&

    def mlb(self, irc, msg, args, optinput):
        """[date]
        Display MLB scores.
        """

        # check optinput
        d = None
        if optinput:
            optinput = optinput.lower()
            if optinput in self.DAYS:
                d = self._datetodatetime(optinput)
        # url dependent on d
        if d:
            url = "http://m.yahoo.com/w/sports/mlb/scores?date=%s&.ts=1429099057&.intl=us&.lang=en" % d
        else:
            url = "http://m.yahoo.com/w/sports/mlb/scores?.ts=1428390180&.intl=us&.lang=en"
        # base url.
        html = self._urlfetch(url)
        # container
        gameslist = self._scores(html.text)
        # strip color/bold/ansi if option is enabled.
        irc.reply("{0}".format(" | ".join(gameslist)))

    mlb = wrap(mlb, [optional('text')])

    def nba(self, irc, msg, args, optinput):
        """[date]
        Display NBA scores.
        """

        # check optinput
        d = None
        if optinput:
            optinput = optinput.lower()
            if optinput in self.DAYS:
                d = self._datetodatetime(optinput)
        if d:
            url = "http://m.yahoo.com/w/sports/nba/scores?date=%s&.ts=1429099057&.intl=us&.lang=en" % d
        else:
            url = "http://m.yahoo.com/w/sports/nba/scores?.ts=1428390180&.intl=us&.lang=en"
        # base url.
        html = self._urlfetch(url)
        # container
        gameslist = self._scores(html.text)
        # strip color/bold/ansi if option is enabled.
        irc.reply("{0}".format(" | ".join(gameslist)))

    nba = wrap(nba, [optional('text')])

    def nhl(self, irc, msg, args, optinput):
        """
        Display NHL scores.
        """

        # check optinput
        d = None
        if optinput:
            optinput = optinput.lower()
            if optinput in self.DAYS:
                d = self._datetodatetime(optinput)
        if d:
            url = "http://m.yahoo.com/w/sports/nhl/scores?date=%s&.ts=1429099057&.intl=us&.lang=en" % d
        else:
            url = "http://m.yahoo.com/w/sports/nhl/scores?.ts=1428390180&.intl=us&.lang=en"
        # base url.
        html = self._urlfetch(url)
        # container
        gameslist = self._scores(html.text)
        # strip color/bold/ansi if option is enabled.
        irc.reply("{0}".format(" | ".join(gameslist)))

    nhl = wrap(nhl, [optional('text')])

    def golf(self, irc, msg, args):
        """
        Display Golf Scores.
        """
        
        url = "http://espn.go.com/golf/leaderboard"
        headers = {'User-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:37.0) Gecko/20100101 Firefox/37.0'}
        r = requests.get(url, headers=headers)
        rtext = r.text
        soup = BeautifulSoup(rtext)
        # tourney
        tourney = soup.find('h1', attrs={'class':'tourney-name'}).getText().encode('utf-8')
        # find the table
        table = soup.find('table', attrs={'class':re.compile('.*leaderboard.*')})
        # container
        o = []
        rows = table.find('tbody').findAll('tr', attrs={'id':re.compile('.*?player.*?')})
        # iterate
        for row in rows:
            tds = [i.getText() for i in row.findAll('td')]
            if len(tds) == 3:  # tournament not begun yet.
                cty = tds[0]
                plyr = tds[1]
                teetime = tds[2]
                out = "{0} {1}".format(plyr, teetime)
            else:  # begun.
                pos = tds[0]
                plyr = tds[3]
                score = tds[4]
                thru = tds[6]
                out = "{0} {1} {2} {3}".format(pos, plyr, score, thru)
            # append.
            o.append(out)
        # display
        irc.reply("{0} :: {1}".format(tourney, " | ".join(i for i in o)))
        
    golf = wrap(golf)


Class = Scores

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
