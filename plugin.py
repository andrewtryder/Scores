# -*- coding: utf-8 -*-
###
# Copyright (c) 2012-2013, spline
# All rights reserved.
###

# my libs
from BeautifulSoup import BeautifulSoup, NavigableString
import re
import datetime
import sqlite3
import os.path
from base64 import b64decode
# supybot libs
import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
from supybot.i18n import PluginInternationalization, internationalizeDocstring

_ = PluginInternationalization('Scores')


@internationalizeDocstring
class Scores(callbacks.Plugin):
    """Add the help for "@plugin help Scores" here
    This should describe *how* to use this plugin."""
    threaded = True

    def __init__(self, irc):
        self.__parent = super(Scores, self)
        self.__parent.__init__(irc)
        self.scoresdb = os.path.abspath(os.path.dirname(__file__)) + '/db/scores.db'
        self.WEEKDAYS = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']

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

    ##############
    # PROCESSING #
    ##############

    def _splicegen(self, maxchars, stringlist):
        """Return a group of splices from a list based on the maxchars
        string-length boundary.
        """

        runningcount = 0
        tmpslice = []
        for i, item in enumerate(stringlist):
            runningcount += len(item)
            if runningcount <= int(maxchars):
                tmpslice.append(i)
            else:
                yield tmpslice
                tmpslice = [i]
                runningcount = len(item)
        yield(tmpslice)

    def _validate(self, date, format):
        """Return true or false for valid date based on format."""

        try:
            datetime.datetime.strptime(str(date), format) # format = "%Y%m%D"
            return True
        except ValueError:
            return False

    def _splitevent(self, event):
        """Input event string and we return score and playoff information in dict."""

        #scoreregex = re.compile(r'^(?P<score>.*?),(.*?\s(?P<poff>G\d:.*?$)|$|.*?[A-Za-z0-9]+$)')
        scoreregex = re.compile(r'^(?P<score>.*?)(,|$)(.*?\s(?P<poff>G\d.*?$)|$|.*?[A-Za-z0-9]+$)')
        s = scoreregex.search(event)  # have regex and fallback split method.
        if s:  # if we match.
            eventstr = {'score': s.groupdict()['score'], 'poff': s.groupdict()['poff']}
        else:  # regex broke. log the "error" so we can fix.
            self.log.info("NOTICE: {0} did not match regex method.".format(event))
            eventstr = {'score': event.split(',', 1)[0], 'poff': None}
        # return our gamestr.
        return eventstr

    def _boldleader(self, atm, asc, htm, hsc):
        """Input away team, away score, home team, home score and bold the leader of the two."""

        if int(asc) > int(hsc):  # away winning.
            return("{0} {1} {2} {3}".format(self._bold(atm), self._bold(asc), htm, hsc))
        elif int(hsc) > int(asc):  # home winning.
            return("{0} {1} {2} {3}".format(atm, asc, self._bold(htm), self._bold(hsc)))
        else:  # tied.
            return("{0} {1} {2} {3}".format(atm, asc, htm, hsc))

    def _colorformatstatus(self, string):
        """Handle the formatting of a status with color."""

        table = {# Red
                 'Final':self._red('F'),'F/OT':self._red('F/OT'),'F/2OT':self._red('F/2OT'),
                 'F/3OT':self._red('F/3OT'),'F/4OT':self._red('F/4OT'),'F/5OT':self._red('F/5OT'),
                 'Canc':self._red('CAN'),'F/SO':self._red('F/SO'),
                 # Green
                 '1st':self._green('1st'),'2nd':self._green('2nd'),'3rd':self._green('3rd'),
                 '4th':self._green('4th'),'OT':self._green('OT'),'SO':self._green('SO'),
                 # Yellow
                 'Half':self._yellow('H'),'Dly':self._yellow('DLY'),'DLY':self._yellow('DLY'),
                 'PPD':self._yellow('PPD'),'Del:':self._yellow('DLY'),'Int':self._yellow('INT'),
                 'Del':self._yellow('DLY')
                 }
        try:  # try to colorize.
            return table[string]
        except:  # return if error.
            return string

    def _mlbformatstatus(self, string):
        """Handle MLB specific status here."""

        # conditionals for each.
        if string.startswith('F'):  # Final or F/10. Game is complete.
            string = string.replace('FINAL', 'F')  # FINAL to F.
            string = string.replace('Final', 'F')  # Final to F.
            string = string.replace(' ', '')  # Remove spaces (d1bb).
            string = self._red(string)
        elif string.startswith('Top ') or string.startswith('Bot ') or string.startswith('End') or string.startswith('Mid') or string.startswith('Bottom '):  # Top/Bot/End/Mid (Game Going on)
            string = string.replace('Top ', 'T')  # Top to T.
            string = string.replace('Bottom ', 'B')  # Bottom to B.
            string = string.replace('Bot ', 'B')  # Bot to B.
            string = string.replace('End ', 'E')  # End to E.
            string = string.replace('Mid ', 'M')  # Mid to M.
            string = string.replace('th', '').replace('nd', '').replace('rd', '').replace('st', '')  # remove endings.
            string = self._green(string)
        elif string.startswith('Dly') or string.startswith('PPD') or string.startswith('Del') or string.startswith('Susp'):  # delayed
            if string == "PPD":  # PPD is one thing, otherwise..
                string = self._yellow('PPD')
            else:  # it can be "DLY: End 5th." or "Susp: Bot 9th". I don't want to do conditionals here.
                string = self._yellow('DLY')
        # return now.
        return string

    def _handlestatus(self, sport, string):
        """Handle working with the time/status of a game."""

        if sport == 'mlb':  # handle mlb here.
            string = self._mlbformatstatus(string)
            return string
        if sport != 'mlb':  # everything else.
            strings = string.split(' ', 1)  # split at space, everything in a list w/two.
            if len(strings) == 2:  # if we have two items, like 3:00 4th.
                return "{0} {1}".format(strings[0], self._colorformatstatus(strings[1]))  # ignore time and colorize quarter/etc.
            else:  # game is "not in progress"
                return self._colorformatstatus(strings[0])  # just return the colorized quarter/etc due to no time.

    def _fetch(self, optargs, logurl=False):
        """Fetch and return HTML."""

        url = b64decode('aHR0cDovL20uZXNwbi5nby5jb20v') + '%s&wjb=' % optargs
        try:
            if logurl or self.registryValue('logURLs'):
                self.log.info("Trying to fetch: {0}".format(url))

            headers = {"User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:17.0) Gecko/17.0 Firefox/17.0"}
            page = utils.web.getUrl(url, headers=headers)
            return page
        except utils.web.Error as e:
            self.log.error("ERROR. Could not open {0} message: {1}".format(url, e))
            return None

    def _scores(self, html, sport="", fullteams=True, showlater=True):
        """Go through each "game" we receive and process the data."""

        soup = BeautifulSoup(html, convertEntities=BeautifulSoup.HTML_ENTITIES, fromEncoding='utf-8')
        # subdark = soup.find('div', attrs={'class': 'sub dark'})
        games = soup.findAll('div', attrs={'id': re.compile('^game.*?')})
        # setup the list for output.
        gameslist = []
        # go through each game
        for game in games:
            gamestr = self._splitevent(game.getText())  # convert to text.
            gametext = gamestr['score']  # returns a dict with score and poff.
            if " at " not in gametext:  # game is in-action.
                if sport == 'nfl' or sport == 'ncf':  # special for NFL/NCB to display POS.
                    if game.find('b', attrs={'class': 'red'}):
                        gametext = gametext.replace('*', '<RZ>')
                    else:
                        gametext = gametext.replace('*', '<>')
                # make sure we split into parts and shove whatever status/time is in the rest.
                gparts = gametext.split(" ", 4)
                if fullteams:  # gparts[0] = away/2=home. full translation table.
                    gparts[0] = self._transteam(gparts[0], optsport=sport)
                    gparts[2] = self._transteam(gparts[2], optsport=sport)
                # last exception: color <RZ> or * if we have them.
                if sport == 'nfl' or sport == 'ncb':  # cheap but works.
                    gparts[0] = gparts[0].replace('<RZ>', self._red('<RZ>')).replace('<>', self._red('<>'))
                    gparts[2] = gparts[2].replace('<RZ>', self._red('<RZ>')).replace('<>', self._red('<>'))
                # now bold the leader and format output.
                gamescore = self._boldleader(gparts[0], gparts[1], gparts[2], gparts[3])
                if gamestr['poff']:
                    output = "{0} {1} ({2})".format(gamescore, self._handlestatus(sport, gparts[4]), gamestr['poff'])
                else:
                    output = "{0} {1}".format(gamescore, self._handlestatus(sport, gparts[4]))
            else:  # TEAM at TEAM time for inactive games.
                if not showlater:  # don't show these if !
                    break
                gparts = gametext.split(" ", 3)  # remove AM/PM in split.
                if fullteams:  # full teams.
                    gparts[0] = self._transteam(gparts[0], optsport=sport)
                    gparts[2] = self._transteam(gparts[2], optsport=sport)
                if "AM" not in gparts[3] and "PM" not in gparts[3]:  # for PPD in something not started.
                    gparts[3] = self._colorformatstatus(gparts[3])
                #output = "{0} at {1} {2}".format(gparts[0], gparts[2], gparts[3])
                if gamestr['poff']:
                    output = "{0} at {1} {2} ({3})".format(gparts[0], gparts[2], gparts[3], gamestr['poff'])
                else:
                    output = "{0} at {1} {2}".format(gparts[0], gparts[2], gparts[3])
            # finally add whatever output is.
            gameslist.append(output)
        # return the list of games.
        return gameslist

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
        elif optdate in self.WEEKDAYS:  # weekday.
            weekdaynum = self.WEEKDAYS.index(optdate)  # day of the week (index) requested.
            dayoftheweek = datetime.datetime.now().isoweekday()  # today's day.
            if weekdaynum >= dayoftheweek:  # if day is ahead but not next week.
                datedelta = weekdaynum - dayoftheweek  # simple +math.
            else:
                datedelta = 7+(weekdaynum-dayoftheweek)  # add in the -dayoftheweek
        # calculate the datedelta and return a string.
        datestr = (datetime.date.today() + datetime.timedelta(days=datedelta)).strftime('%Y%m%d')
        # now return.
        return datestr

    ######################
    # DATABASE FUNCTIONS #
    ######################

    def _transteam(self, optteam, optsport=""):
        # do some regex here to parse out the team.
        partsregex = re.compile(r'(?P<pre>\<RZ\>|\<\>)?(?P<team>[A-Z\-&;]+)(?P<rank>\(\d+\))?')
        m = partsregex.search(optteam)
        # replace optteam with the team if we have it
        if m.group('team'):
            optteam = m.group('team')
        # connect and do the db translation.
        conn = sqlite3.connect(self.scoresdb)
        cursor = conn.cursor()
        cursor.execute("select full from teams where short=? and sport=?", (optteam, optsport))
        row = cursor.fetchone()
        cursor.close()
        # put the string/team back together with or without db output.
        if row is None:
            team = optteam
        else:
            team = str(row[0])
        # now lets build for output.
        output = ""  # blank string to start.
        if m.group('pre'):   # readd * or <RZ>
            output += m.group('pre')
        output += team  # now team.
        if m.group('rank'):
            output += m.group('rank')
        # finally, return output.
        return output

    ###################################
    # PUBLIC FUNCTIONS (ONE PER SPORT #
    ###################################

    def nba(self, irc, msg, args, optlist, optinput):
        """[--date YYYYMMDD] [optional]
        Display NBA scores.
        Use --date YYYYMMDD to display scores on specific date. Ex: --date 20121225
        Specify a string to match after to only display specific scores. Ex: Knick
        """

        # first, declare sport.
        optsport = 'nba'
        # base url.
        url = '%s/scoreboard?' % optsport
        # declare variables we manip with input + optlist.
        showlater = True  # show all. ! below negates.
        # first, we have to handle if optinput is today or tomorrow.
        if optinput:
            optinput = optinput.lower()  # lower to process.
            if optinput in ['yesterday', 'today', 'tomorrow', 'tonight'] or optinput in self.WEEKDAYS:
                url += 'date=%s' % self._datetodatetime(optinput)  # centralize our date ops.
                optinput = None  # have to declare so we're not looking for games below.
            elif optinput == "!":
                showlater = False  # only show completed and active (not future) games.
                optinput = None  # have to declare so we're not looking for games below.
        # handle optlist.
        if optlist:  # we only have --date, for now.
            for (key, value) in optlist:
                if key == 'date':  # this will override today and tomorrow.
                    if len(str(value)) != 8 or not self._validate(value, '%Y%m%d'):
                        irc.reply("ERROR: Invalid date. Must be YYYYmmdd. Ex: --date=20120904")
                        return
                    else:
                        url += 'date=%s' % value
        # process url and fetch.
        html = self._fetch(url)
        if not html:
            irc.error("ERROR: Cannot fetch {0} scores url. Try again in a minute.".format(optsport.upper()))
            return
        # process games.
        gameslist = self._scores(html, sport=optsport, fullteams=self.registryValue('fullteams', msg.args[0]), showlater=showlater)
        # strip color/bold/ansi if option is enabled.
        if self.registryValue('disableANSI', msg.args[0]):
            gameslist = [ircutils.stripFormatting(item) for item in gameslist]
        # output time.
        if len(gameslist) > 0:  # process here if we have games. sometimes we do not.
            if optinput:  # we're looking for a specific team/string.
                count = 0  # start at 0.
                for item in gameslist:  # iterate through our items.
                    if optinput in item.lower():  # we're lower from above. lower item to match.
                        if count < 10:  # if less than 10 items out.
                            irc.reply(item)  # output item.
                            count += 1  # ++count.
                        else:  # once we're over 10 items out.
                            irc.reply("ERROR: I found too many matches for '{0}' in {1}. Try something more specific.".format(optinput, optsport.upper()))
                            break
            else:  # no optinput so we are just displaying games.
                if self.registryValue('lineByLineScores', msg.args[0]):  # if you want line-by-line scores, even for all.
                    for game in gameslist:
                        irc.reply(game)  # output each.
                else:  # we're gonna display as much as we can on each line.
                    for splice in self._splicegen('380', gameslist):
                        irc.reply(" | ".join([gameslist[item] for item in splice]))
        else:  # we found no games to display.
            irc.reply("ERROR: No {0} games listed.".format(optsport.upper()))

    nba = wrap(nba, [getopts({'date': ('int')}), optional('text')])

    def wnba(self, irc, msg, args, optlist, optinput):
        """[--date YYYYMMDD] [optional]
        Display WNBA scores.
        Use --date YYYYMMDD to display scores on specific date. Ex: --date 20121225
        Specify a string to match after to only display specific scores. Ex: Minnesota
        """

        # first, declare sport.
        optsport = 'wnba'
        # base url.
        url = '%s/scoreboard?' % optsport
        # declare variables we manip with input + optlist.
        showlater = True  # show all. ! below negates.
        # first, we have to handle if optinput is today or tomorrow.
        if optinput:
            optinput = optinput.lower()  # lower to process.
            if optinput in ['yesterday', 'today', 'tomorrow', 'tonight'] or optinput in self.WEEKDAYS:
                url += 'date=%s' % self._datetodatetime(optinput)  # centralize our date ops.
                optinput = None  # have to declare so we're not looking for games below.
            elif optinput == "!":
                showlater = False  # only show completed and active (not future) games.
                optinput = None  # have to declare so we're not looking for games below.
        # handle optlist.
        if optlist:  # we only have --date, for now.
            for (key, value) in optlist:
                if key == 'date':  # this will override today and tomorrow.
                    if len(str(value)) != 8 or not self._validate(value, '%Y%m%d'):
                        irc.reply("ERROR: Invalid date. Must be YYYYmmdd. Ex: --date=20120904")
                        return
                    else:
                        url += 'date=%s' % value
        # process url and fetch.
        html = self._fetch(url)
        if not html:
            irc.error("ERROR: Cannot fetch {0} scores url. Try again in a minute.".format(optsport.upper()))
            return
        # process games.
        gameslist = self._scores(html, sport=optsport, fullteams=self.registryValue('fullteams', msg.args[0]), showlater=showlater)
        # strip color/bold/ansi if option is enabled.
        if self.registryValue('disableANSI', msg.args[0]):
            gameslist = [ircutils.stripFormatting(item) for item in gameslist]
        # output time.
        if len(gameslist) > 0:  # process here if we have games. sometimes we do not.
            if optinput:  # we're looking for a specific team/string.
                count = 0  # start at 0.
                for item in gameslist:  # iterate through our items.
                    if optinput in item.lower():  # we're lower from above. lower item to match.
                        if count < 10:  # if less than 10 items out.
                            irc.reply(item)  # output item.
                            count += 1  # ++count.
                        else:  # once we're over 10 items out.
                            irc.reply("ERROR: I found too many matches for '{0}' in {1}. Try something more specific.".format(optinput, optsport.upper()))
                            break
            else:  # no optinput so we are just displaying games.
                if self.registryValue('lineByLineScores', msg.args[0]):  # if you want line-by-line scores, even for all.
                    for game in gameslist:
                        irc.reply(game)  # output each.
                else:  # we're gonna display as much as we can on each line.
                    for splice in self._splicegen('380', gameslist):
                        irc.reply(" | ".join([gameslist[item] for item in splice]))
        else:  # we found no games to display.
            irc.reply("ERROR: No {0} games listed.".format(optsport.upper()))

    wnba = wrap(wnba, [getopts({'date': ('int')}), optional('text')])

    def nhl(self, irc, msg, args, optlist, optinput):
        """[--date YYYYMMDD] [optional]
        Display NHL scores.
        Use --date YYYYMMDD to display scores on specific date. Ex: --date 20121225
        Specify a string to match after to only display specific scores. Ex: Rang
        """

         # first, declare sport.
        optsport = 'nhl'
        # base url.
        url = '%s/scoreboard?' % optsport
        # declare variables we manip with input + optlist.
        showlater = True  # show all. ! below negates.
        # first, we have to handle if optinput is today or tomorrow.
        if optinput:
            optinput = optinput.lower()  # lower to process.
            if optinput in ['yesterday', 'today', 'tomorrow', 'tonight'] or optinput in self.WEEKDAYS:
                url += 'date=%s' % self._datetodatetime(optinput)  # centralize our date ops.
                optinput = None  # have to declare so we're not looking for games below.
            elif optinput == "!":
                showlater = False  # only show completed and active (not future) games.
                optinput = None  # have to declare so we're not looking for games below.
        # handle optlist.
        if optlist:  # we only have --date, for now.
            for (key, value) in optlist:
                if key == 'date':  # this will override today and tomorrow.
                    if len(str(value)) != 8 or not self._validate(value, '%Y%m%d'):
                        irc.reply("ERROR: Invalid date. Must be YYYYmmdd. Ex: --date=20120904")
                        return
                    else:
                        url += 'date=%s' % value
        # process url and fetch.
        html = self._fetch(url)
        if not html:
            irc.error("ERROR: Cannot fetch {0} scores url. Try again in a minute.".format(optsport.upper()))
            return
        # process games.
        gameslist = self._scores(html, sport=optsport, fullteams=self.registryValue('fullteams', msg.args[0]), showlater=showlater)
        # strip color/bold/ansi if option is enabled.
        if self.registryValue('disableANSI', msg.args[0]):
            gameslist = [ircutils.stripFormatting(item) for item in gameslist]
        # output time.
        if len(gameslist) > 0:  # process here if we have games. sometimes we do not.
            if optinput:  # we're looking for a specific team/string.
                count = 0  # start at 0.
                for item in gameslist:  # iterate through our items.
                    if optinput in item.lower():  # we're lower from above. lower item to match.
                        if count < 10:  # if less than 10 items out.
                            irc.reply(item)  # output item.
                            count += 1  # ++count.
                        else:  # once we're over 10 items out.
                            irc.reply("ERROR: I found too many matches for '{0}' in {1}. Try something more specific.".format(optinput, optsport.upper()))
                            break
            else:  # no optinput so we are just displaying games.
                if self.registryValue('lineByLineScores', msg.args[0]):  # if you want line-by-line scores, even for all.
                    for game in gameslist:
                        irc.reply(game)  # output each.
                else:  # we're gonna display as much as we can on each line.
                    for splice in self._splicegen('380', gameslist):
                        irc.reply(" | ".join([gameslist[item] for item in splice]))
        else:  # we found no games to display.
            irc.reply("ERROR: No {0} games listed.".format(optsport.upper()))

    nhl = wrap(nhl, [getopts({'date': ('int')}), optional('text')])

    def mlb(self, irc, msg, args, optlist, optinput):
        """[--date YYYYMMDD] [optional]
        Display MLB scores.
        Use --date YYYYMMDD to display scores on specific date. Ex: --date 20121225
        Specify a string to match after to only display specific scores. Ex: Yank
        """

        # first, declare sport.
        optsport = 'mlb'
        # base url.
        url = '%s/scoreboard?' % optsport
        # declare variables we manip with input + optlist.
        showlater = True  # show all. ! below negates.
        # first, we have to handle if optinput is today or tomorrow.
        if optinput:
            optinput = optinput.lower()  # lower to process.
            if optinput in ['yesterday', 'today', 'tomorrow', 'tonight'] or optinput in self.WEEKDAYS:
                url += 'date=%s' % self._datetodatetime(optinput)  # centralize our date ops.
                optinput = None  # have to declare so we're not looking for games below.
            elif optinput == "!":
                showlater = False  # only show completed and active (not future) games.
                optinput = None  # have to declare so we're not looking for games below.
        # handle optlist.
        if optlist:  # we only have --date, for now.
            for (key, value) in optlist:
                if key == 'date':  # this will override today and tomorrow.
                    if len(str(value)) != 8 or not self._validate(value, '%Y%m%d'):
                        irc.reply("ERROR: Invalid date. Must be YYYYmmdd. Ex: --date=20120904")
                        return
                    else:
                        url += 'date=%s' % value
        # process url and fetch.
        html = self._fetch(url)
        if not html:
            irc.error("ERROR: Cannot fetch {0} scores url. Try again in a minute.".format(optsport.upper()))
            return
        # process games.
        gameslist = self._scores(html, sport=optsport, fullteams=self.registryValue('fullteams', msg.args[0]), showlater=showlater)
        # strip color/bold/ansi if option is enabled.
        if self.registryValue('disableANSI', msg.args[0]):
            gameslist = [ircutils.stripFormatting(item) for item in gameslist]
        # output time.
        if len(gameslist) > 0:  # process here if we have games. sometimes we do not.
            if optinput:  # we're looking for a specific team/string.
                count = 0  # start at 0.
                for item in gameslist:  # iterate through our items.
                    if optinput in item.lower():  # we're lower from above. lower item to match.
                        if count < 10:  # if less than 10 items out.
                            irc.reply(item)  # output item.
                            count += 1  # ++count.
                        else:  # once we're over 10 items out.
                            irc.reply("ERROR: I found too many matches for '{0}' in {1}. Try something more specific.".format(optinput, optsport.upper()))
                            break
            else:  # no optinput so we are just displaying games.
                if self.registryValue('lineByLineScores', msg.args[0]):  # if you want line-by-line scores, even for all.
                    for game in gameslist:
                        irc.reply(game)  # output each.
                else:  # we're gonna display as much as we can on each line.
                    for splice in self._splicegen('380', gameslist):
                        irc.reply(" | ".join([gameslist[item] for item in splice]))
        else:  # we found no games to display.
            irc.reply("ERROR: No {0} games listed.".format(optsport.upper()))

    mlb = wrap(mlb, [getopts({'date': ('int')}), optional('text')])

    def nfl(self, irc, msg, args, optinput):
        """[team]
        Display NFL scores.
        Specify a string to match after to only display specific scores. Ex: Pat
        """

         # first, declare sport.
        optsport = 'nfl'
        # base url.
        url = '%s/scoreboard?' % optsport
        # process url and fetch.
        html = self._fetch(url)
        if not html:
            irc.error("ERROR: Cannot fetch {0} scores url. Try again in a minute.".format(optsport.upper()))
            return

        if optinput and optinput == "!":
            showlater = False
            optinput = None
        else:
            showlater = True

        gameslist = self._scores(html, sport='nfl', fullteams=self.registryValue('fullteams', msg.args[0]), showlater=showlater)

        if self.registryValue('disableANSI', msg.args[0]):
            gameslist = [ircutils.stripFormatting(item) for item in gameslist]

        if len(gameslist) > 0:
            if optinput:
                count = 0
                for item in gameslist:
                    if optinput.lower() in item.lower():
                        if count < 10:
                            irc.reply(item)
                            count += 1
                        else:
                            irc.reply("I found too many matches for '{0}'. Try something more specific.".format(optinput))
                            break
            else:
                if self.registryValue('lineByLineScores', msg.args[0]):
                    for game in gameslist:
                        irc.reply(game)
                else:
                    for splice in self._splicegen('380', gameslist):
                        irc.reply(" | ".join([gameslist[item] for item in splice]))
        else:
            irc.reply("ERROR: No {0} games listed.".format(optsport.upper()))

    nfl = wrap(nfl, [optional('text')])

    def ncb(self, irc, msg, args, optlist, optconf):
        """[--date YYYYMMDD] [tournament|conference|team]
        Display College Basketball scores.
        Optional: Use --date YYYYMMDD to display scores on specific date. Ex: --date 20121225
        Optional: input CONFERENCE or TEAM to search scor            page = utils.web.getUrl(url)
            return page
        except utils.web.Error as e:
            self.log.error("ERROR. Could not open {0} message: {1}".format(url, e))
            return Nonees by conference or display an individual team's score. Ex: SEC or Bama.
        Optional: input tournament to display scores. Ex: ncaa, nit.
        """

        # basketball confs.
        validconfs = {'top25':'999', 'a10':'3', 'acc':'2', 'ameast':'1', 'big12':'8', 'bigeast':'4', 'bigsky':'5', 'bigsouth':'6', 'big10':'7',
                      'bigwest':'9', 'c-usa':'11', 'caa':'10', 'greatwest':'57', 'horizon':'45', 'independent':'43', 'ivy':'12', 'maac':'13',
                      'mac':'14', 'meac':'16', 'mvc':'18', 'mwc':'44', 'div-i':'50', 'nec':'19', 'non-div-i':'51', 'ovc':'20', 'pac12':'21',
                      'patriot':'22', 'sec':'23', 'southern':'24', 'southland':'25', 'summit':'49', 'sunbelt':'27', 'swac':'26', 'wac':'30',
                      'wcc':'29', 'ncaa':'100', 'nit':'50', 'cbi':'55', 'cit':'56' }

        # if we have a specific conf to display, get the id.
        optinput = None
        if optconf:
            optconf = optconf.lower()
            if optconf not in validconfs:
                optinput = optconf

        # get top25 if no conf is specified.
        if optconf and optinput :  # no optinput because we got a conf above.
            url = 'ncb/scoreboard?groupId=%s' % validconfs['div-i']
        elif optconf and not optinput:
            url = 'ncb/scoreboard?groupId=%s' % validconfs[optconf]
        else:
            url = 'ncb/scoreboard?groupId=%s' % validconfs['top25']

        # handle date
        if optlist:
            for (key, value) in optlist:
                if key == 'date':
                    if len(str(value)) !=8 or not self._validate(value, '%Y%m%d'):
                        irc.reply("Invalid date. Must be YYYYmmdd. Ex: 20120904")
                        return
                    else:
                        url += '&date=%s' % value

        html = self._fetch(url)
        if not html:
            irc.error("ERROR: Cannot fetch NCB scores.")
            return
        # now, process html and put all into gameslist.
        gameslist = self._scores(html, sport='ncb', fullteams=self.registryValue('fullteams', msg.args[0]))

        # strip ANSI if needed.
        if self.registryValue('disableANSI', msg.args[0]):
            gameslist = [ircutils.stripFormatting(item) for item in gameslist]

        # finally, check if there is any games/output.
        if len(gameslist) > 0:  # if we have games
            if optinput:  # if we have input.
                count = 0
                for item in gameslist:
                    if optinput.lower() in item.lower():
                        if count < 10:
                            irc.reply(item)
                            count += 1
                        else:
                            irc.reply("I found too many matches for '{0}'. Try something more specific.".format(optinput))
                            break
            else:
                if self.registryValue('lineByLineScores', msg.args[0]):
                    for game in gameslist:
                        irc.reply(game)
                else:
                    for splice in self._splicegen('380', gameslist):
                        irc.reply(" | ".join([gameslist[item] for item in splice]))
        else:  # no games
            irc.reply("ERROR: No college basketball games listed.")

    ncb = wrap(ncb, [getopts({'date': ('int')}), optional('text')])

    def cfb(self, irc, msg, args, optconf):
        """[conference|team]
        Display College Football scores.
        Optional: input with conference to display all scores from conf. Use team to only display specific team scores.
        Ex: SEC or Bama or BIG10 or Notre
        """

        # football confs.
        validconfs = {'top25':'999', 'acc':'1', 'bigeast':'10', 'bigsouth':'40', 'big10':'5', 'big12':'4',
                      'bigsky':'20', 'caa':'48', 'c-usa':'12', 'independent':'18','ivy':'22', 'mac':'15',
                      'meac':'24', 'mvc':'21', 'i-a':'80','i-aa':'81', 'pac12':'9', 'southern':'29', 'sec':'8',
                      'sunbelt':'37', 'wac':'16'}

        # if we have a specific conf to display, get the id.
        optinput = None
        if optconf:
            optconf = optconf.lower()
            if optconf not in validconfs:
                optinput = optconf

        # get top25 if no conf is specified.
        if optconf and optinput :  # no optinput because we got a conf above.
            url = 'ncf/scoreboard?groupId=%s' % validconfs['i-a']
        elif optconf and not optinput:
            url = 'ncf/scoreboard?groupId=%s' % validconfs[optconf]
        else:
            url = 'ncf/scoreboard?groupId=%s' % validconfs['top25']

        html = self._fetch(url)
        if not html:
            irc.error("ERROR: Cannot fetch CFB scores.")
            return

        # now, process html and put all into gameslist.
        gameslist = self._scores(html, sport='ncf', fullteams=self.registryValue('fullteams', msg.args[0]))

        # strip ANSI if needed.
        if self.registryValue('disableANSI', msg.args[0]):
            gameslist = [ircutils.stripFormatting(item) for item in gameslist]

        # finally, check if there is any games/output.
        if len(gameslist) > 0: # if we have games
            if optinput: # if we have input.
                count = 0
                for item in gameslist:
                    if optinput.lower() in item.lower():
                        if count < 10:
                            irc.reply(item)
                            count += 1
                        else:
                            irc.reply("I found too many matches for '{0}'. Try something more specific.".format(optinput))
                            break
            else:
                if self.registryValue('lineByLineScores', msg.args[0]):
                    for game in gameslist:
                        irc.reply(game)
                else:
                    for splice in self._splicegen('380', gameslist):
                        irc.reply(" | ".join([gameslist[item] for item in splice]))
        else:  # no games
            irc.reply("ERROR: No college football games listed.")

    cfb = wrap(cfb, [optional('text')])

    def ncw(self, irc, msg, args, optlist, optconf):
        """[--date YYYYMMDD] [conference|team]
        Display Women's College Basketball scores.
        Optional: Use --date YYYYMMDD to display scores on specific date. Ex: --date 20121225
        Optional: input CONFERENCE or TEAM to search scores by conference or display an individual team's score. Ex: SEC or Bama.
        Optional: input tournament to display scores. Ex: ncaa, nit.
        """

        # basketball confs.
        validconfs = {'top25':'999', 'a10':'3', 'acc':'2', 'ameast':'1', 'big12':'8', 'bigeast':'4', 'bigsky':'5', 'bigsouth':'6', 'big10':'7',
                      'bigwest':'9', 'c-usa':'11', 'caa':'10', 'greatwest':'57', 'horizon':'45', 'independent':'43', 'ivy':'12', 'maac':'13',
                      'mac':'14', 'meac':'16', 'mvc':'18', 'mwc':'44', 'div-i':'50', 'nec':'19', 'non-div-i':'51', 'ovc':'20', 'pac12':'21',
                      'patriot':'22', 'sec':'23', 'southern':'24', 'southland':'25', 'summit':'49', 'sunbelt':'27', 'swac':'26', 'wac':'30',
                      'wcc':'29', 'ncaa':'100', 'nit':'50', 'cbi':'55' }

        # if we have a specific conf to display, get the id.
        optinput = None
        if optconf:
            optconf = optconf.lower()
            if optconf not in validconfs:
                optinput = optconf

        # get top25 if no conf is specified.
        if optconf and optinput :  # no optinput because we got a conf above.
            url = 'ncw/scoreboard?groupId=%s' % validconfs['div-i']
        elif optconf and not optinput:
            url = 'ncw/scoreboard?groupId=%s' % validconfs[optconf]
        else:
            url = 'ncw/scoreboard?groupId=%s' % validconfs['top25']

        # handle date
        if optlist:
            for (key, value) in optlist:
                if key == 'date':
                    if len(str(value)) !=8 or not self._validate(value, '%Y%m%d'):
                        irc.reply("Invalid date. Must be YYYYmmdd. Ex: 20120904")
                        return
                    else:
                        url += '&date=%s' % value

        html = self._fetch(url)
        if not html:
            irc.error("ERROR: Cannot fetch women's college basketball scores.")
            return

        # now, process html and put all into gameslist.
        gameslist = self._scores(html, sport='ncb', fullteams=self.registryValue('fullteams', msg.args[0]))

        # strip ANSI if needed.
        if self.registryValue('disableANSI', msg.args[0]):
            gameslist = [ircutils.stripFormatting(item) for item in gameslist]

        # finally, check if there is any games/output.
        if len(gameslist) > 0:  # if we have games
            if optinput:  # if we have input.
                count = 0
                for item in gameslist:
                    if optinput.lower() in item.lower():
                        if count < 10:
                            irc.reply(item)
                            count += 1
                        else:
                            irc.reply("I found too many matches for '{0}'. Try something more specific.".format(optinput))
                            break
            else:
                if self.registryValue('lineByLineScores', msg.args[0]):
                    for game in gameslist:
                        irc.reply(game)
                else:
                    for splice in self._splicegen('380', gameslist):
                        irc.reply(" | ".join([gameslist[item] for item in splice]))
        else:  # no games
            irc.reply("ERROR: No women's college basketball games listed.")

    ncw = wrap(ncw, [getopts({'date': ('int')}), optional('text')])

    def tennis(self, irc, msg, args, optmatch, optinput):
        """[mens|womens|mensdoubles|womensdoubles|mixeddoubles]
        Display current Tennis scores. Defaults to Men's Singles.
        Call with argument to display others. Ex: womens.
        Can also find a specific match via string. Ex: mens nadal or womensdoubles williams.
        """

        if optmatch:
            optmatch = optmatch.lower()
            if optmatch == "mens":
                matchType = "1"
            elif optmatch == "womens":
                matchType = "2"
            elif optmatch == "mensdoubles":
                matchType = "3"
            elif optmatch == "womensdoubles":
                matchType = "4"
            elif optmatch == "mixeddoubles":
                matchType = "6"
            else:  # default to mens.
                matchType = "1"
                optinput = optmatch  # if someone inputs tennis federer, this gets set.
        else:
            matchType = "1"
        # build and fetch url.
        html = self._fetch('general/tennis/dailyresults?matchType=' + matchType)
        if not html:
            irc.error("ERROR: Cannot fetch Tennis scores. Please wait a minute or two.")
            return
        # one easy sanity check.
        if "There are no matches scheduled." in html:
            irc.reply("ERROR: There are no tennis matches scheduled.")
            return
        # process html.
        soup = BeautifulSoup(html, convertEntities=BeautifulSoup.HTML_ENTITIES, fromEncoding='utf-8')
        matches = soup.findAll('div', attrs={'class':re.compile('^ind|^ind alt')})
        if len(matches) < 1:  # second sanity check.
            irc.reply("ERROR: No tennis matches found. No tournament going on?")
            return
        title = soup.find('div', attrs={'class':'sec row'}).getText()
        if self.registryValue('wilbonton'):  # this has to be set via the config and is a special option.
            title = title.replace('WIMBLEDON', 'WILBONTON')  # replace if on.
        tennisRound = soup.findAll('div', attrs={'class':'ind sub bold'})[1]  # there are two here so grab the 2nd (1).
        # output container.
        output = []
        # each 'each' is a match.
        for each in matches:
            if each.find('b'):  # <b> means it is a tennis match.
                status = each.find('b').extract()
                if status.text == "Final":
                    status = self._red("F")
                else:
                    status = self._bold(status.getText())
                matchText = []  # smoosh the results together into here.
                for item in each.contents:
                    if isinstance(item, NavigableString):
                        matchText.append(item.strip())
                output.append("{0} :: {1}".format(status, " ".join(matchText)))
        # now output.
        if not optinput:  # just display scores.
            irc.reply("{0} {1}".format(self._bold(title), self._bold(tennisRound.getText())))
            irc.reply("{0}".format(" | ".join(output)))
        else:  # looking for something specific.
            count = 0  # for max 5.
            for each in output:
                if optinput.lower() in each.lower():  # if we find a match.
                    if count == 0:  # display the title on the first.
                        irc.reply("{0} {1}".format(self._bold(title), self._bold(tennisRound.getText())))
                        irc.reply(each)
                        count += 1  # i++
                    elif count < 5:  # only show five.
                        irc.reply(each)
                        count += 1  # i++
                    else:  # above this, display the error.
                        irc.reply("I found too many results for '{0}'. Please specify something more specific".format(optinput))
                        break

    tennis = wrap(tennis, [optional('somethingWithoutSpaces'), optional('text')])

    def golf(self, irc, msg, args, optseries, optinput):
        """[pga|web.com|champions|lpga|euro]
        Display current Golf scores from a tournament. Specify a specific series to show different scores.
        Ex: lpga
        """

        if optseries:
            optseries = optseries.lower()
            if optseries == "pga":
                seriesId = "1"
            if optseries == "web.com":
                seriesId = "2"
            elif optseries == "champions":
                seriesId = "3"
            elif optseries == "lpga":
                seriesId = "4"
            elif optseries == "euro":
                seriesId = "5"
            else:  # default to pga tour.
                seriesId = "1"
                optinput = optseries  # this means someone did a command like 'golf woods' and wants tiger's score.
        else:  # go pga if we don't have a series.
            seriesId = "1"
        # build and fetch url.
        html = self._fetch('golf/eventresult?seriesId=' + seriesId)
        if not html:
            irc.error("ERROR: Cannot fetch Golf scores.")
            return
        # process html.
        soup = BeautifulSoup(html, convertEntities=BeautifulSoup.HTML_ENTITIES, fromEncoding='utf-8')
        golfEvent = soup.find('div', attrs={'class': 'sub dark big'})
        golfStatus = soup.find('div', attrs={'class': 'sec row', 'style': 'white-space: nowrap;'})
        # check for Ryder Cup.
        if golfEvent.getText().startswith("Ryder Cup"):  # if Ryder Cup found, it should just display scores.
            rows = soup.find('div', attrs={'class':'ind'})
            irc.reply(self._green(golfEvent.getText()))
            irc.reply("{0}".format(rows.getText()))
            return
        else:  # regular tournaments.
            table = soup.find('table', attrs={'class': 'wide'})
            if not table:
                irc.reply("ERROR: Could not find golf results. Tournament not going on?")
                return
            rows = table.findAll('tr')[1:]  # skip header row.
        # container for output.
        append_list = []
        # process rows. each row is a player.
        for row in rows:
            tds = row.findAll('td')
            pRank = tds[0].getText()
            pPlayer = tds[1].getText().encode('utf-8')
            pScore = tds[2].getText()
            pRound = tds[3].getText()
            pRound = pRound.replace('(', '').replace(')', '')  # remove ( ). We process pRound later.
            # handle strings differently, depending on if started or not. not started also includes cut.
            if "am" in pRound or "pm" in pRound or pScore == "CUT":  # append string conditional if they started or not.
                if pScore == "CUT":  # we won't have a pRound score in this case
                    appendString = "{0}. {1} {2}".format(pRank, self._bold(pPlayer), pScore)
                else:
                    appendString = "{0}. {1} {2} ({3})".format(pRank, self._bold(pPlayer), pScore, pRound)
            else:  # player has started.
                pRound = pRound.split(' ', 1)  # we split -2 (F), but might not be two.
                if len(pRound) == 2:  # normally, it looks like -2 (F). We want the F.
                    pRound = pRound[1]
                else:  # It is just -9 like for a playoff.
                    pRound = pRound[0]
                appendString = "{0}. {1} {2} ({3})".format(pRank, self._bold(pPlayer), pScore, pRound)
            # append now.
            append_list.append(appendString)
        # output time.
        if golfEvent and golfStatus:  # header/tournament
            irc.reply("{0} - {1}".format(self._green(golfEvent.getText()), self._bold(golfStatus.getText())))
        if not optinput:  # just show the leaderboard
            irc.reply(" | ".join([item for item in append_list]))
        else:  # display a specific player's score.
            count = 0  # for max 5.
            for each in append_list:
                if optinput.lower() in each.lower():  # if we find a match.
                    if count < 5:  # only show five.
                        irc.reply(each)
                        count += 1  # ++1
                    else:  # above this, display the error.
                        irc.reply("I found too many results for '{0}'. Please specify something more specific".format(optinput))
                        break

    golf = wrap(golf, [optional('somethingWithoutSpaces'), optional('text')])

    def nascar(self, irc, msg, args, optrace):
        """[sprintcup|nationwide|trucks]
        Display active NASCAR results from most current race.
        Defaults to Sprint Cup. Specify 'nationwide' or 'trucks' for other series.
        """

        if optrace:
            optrace = optrace.lower()
            if optrace == "sprintcup":
                raceType = "2"
            elif optrace == "nationwide":
                raceType = "3"
            elif optrace == "trucks":
                raceType = "4"
            else:  # default to sprintcup.
                raceType = "2"
        else:  # default to sprintcup.
            raceType = "2"
        # build and fetch url.
        html = self._fetch('rpm/nascar/eventresult?seriesId=' + raceType)
        if not html:
            irc.error("ERROR: Cannot fetch NASCAR standings.")
            return
        # process html.
        soup = BeautifulSoup(html, convertEntities=BeautifulSoup.HTML_ENTITIES, fromEncoding='utf-8')
        race = soup.find('div', attrs={'class': 'sub dark big'}).getText().replace(' Results', '').strip()
        racestatus = soup.find('div', attrs={'class': 'sec row'}).getText().strip()
        # table with results
        rtable = soup.find('table', attrs={'class': 'wide', 'cellspacing': '0', 'width': '100%'})
        rows = rtable.findAll('tr')[1:]  # header row is 0.
        # list container for out.
        standings = []
        # one row per driver.
        for row in rows:
            tds = [item.getText().strip() for item in row.findAll('td')]
            standings.append("{0}. {1} - {2}".format(tds[0], self._bold(tds[1].encode('utf-8')), tds[2]))
        # output time.
        irc.reply("{0} :: {1}".format(self._red(race), self._ul(racestatus)))
        irc.reply("{0}".format(" | ".join(standings)))

    nascar = wrap(nascar, [optional('somethingWithoutSpaces')])

    def racing(self, irc, msg, args, optrace):
        """[f1|indycar]
        Display various race results.
        Defaults to F1.
        Ex: f1 or indycar
        """

        if optrace:
            optrace = optrace.lower()
            if optrace == "f1":
                raceType = "6"
            elif optrace == "indycar":
                raceType = "1"
            else: # defaults to F1.
                raceType = "6"
        else:
            raceType = "6"
        # build and fetch url.
        html = self._fetch('rpm/eventresult?season=-1&seriesId=' + raceType)
        if not html:
            irc.error("ERROR: Cannot fetch racing results.")
            return
        # process html.
        soup = BeautifulSoup(html, convertEntities=BeautifulSoup.HTML_ENTITIES, fromEncoding='utf-8')
        race = soup.find('div', attrs={'class': 'sub dark big'}).getText().replace(' Results', '').strip()
        racestatus = soup.find('div', attrs={'class': 'sec row'}).getText().strip()
        # table with rows.
        rtable = soup.find('table', attrs={'class': 'wide', 'cellspacing': '0', 'width': '100%'})
        rows = rtable.findAll('tr')[1:]  # first is the header.
        # list container for output
        standings = []
        # one row per racer
        for row in rows:
            tds = [item.getText().strip() for item in row.findAll('td')]
            standings.append("{0}. {1}".format(tds[0], self._bold(tds[1])))
        # output time.
        irc.reply("{0} :: {1}".format(self._red(race), self._ul(racestatus)))
        irc.reply("{0}".format(" | ".join(standings)))

    racing = wrap(racing, [optional('somethingWithoutSpaces')])

    def d1bb(self, irc, msg, args, optinput):
        """<team>
        Display Division I baseball scores.
        """

        # build and fetch url.
        try:
            url = b64decode('aHR0cDovL3d3dy5kMWJhc2ViYWxsLmNvbS9kYWlseS90b2RheS5odG0=')
            html = utils.web.getUrl(url)
        except utils.web.Error as e:
            self.log.error("ERROR. Could not open {0} message: {1}".format(url, e))
            irc.reply("ERROR. Could not open {0} message: {1}".format(url, e))
            return
        # sanity check before processing html.
        if 'No games scheduled today' in html:
            irc.reply("Sorry, but no games are scheduled today.")
            return
        # process html
        soup = BeautifulSoup(html, convertEntities=BeautifulSoup.HTML_ENTITIES, fromEncoding='utf-8')
        tables = soup.findAll('table', attrs={'style':'table-layout:fixed'}) #[1:]
        # output list.
        d1games = []
        # page is odd but easy way to find games via iteration.
        for table in tables:  # multiple games in each table.
            games = table.findAll('table', attrs={'rules':'none', 'frame':'box', 'border':'1'})
            for game in games:  # iterate over games.
                # conf = game.findPrevious('h4').getText()
                away = game.findAll('td', attrs={'colspan':'2', 'align':'left', 'valign':'top'})[0]
                if away.find('a'):  # teams will always be in a link.
                    awayteam = away.find('a').extract()
                else:  # skip because we need two teams.
                    continue
                home = game.findAll('td', attrs={'colspan':'2', 'align':'left', 'valign':'top'})[1]
                if home.find('a'):  # teams will always be in a link.
                    hometeam = home.find('a').extract()
                else:  # skip, as well, if we're missing a hometeam.
                    continue
                awayscore = game.findAll('td', attrs={'align':'center', 'valign':'top'})[0].getText().strip()
                homescore = game.findAll('td', attrs={'align':'center', 'valign':'top'})[1].getText().strip()
                status = game.find('td', attrs={'width':'76'}).getText()
                # now we slowly build the string to append, conditionally.
                if away.text == '':  # no ranking.
                    at = "{0}".format(awayteam.getText().replace('&amp;', '&'))
                else:  # ranking, ie: #20 LSU.
                    at = "{0}({1})".format(awayteam.getText().replace('&amp;', '&'), away.getText().replace('#', ''))
                if home.text == '':  # no ranking.
                    ht = "{0}".format(hometeam.getText().replace('&amp;', '&'))
                else:  # ranking.
                    ht = "{0}({1})".format(hometeam.getText().replace('&amp;', '&'), home.getText().replace('#', ''))
                # if the game has happened or is happening, bold the leader.
                # so far, the only way to test/tell is by looking at status (AM,PM,:,/)
                if "PM" in status or "AM" in status or not awayscore.isdigit() or not homescore.isdigit():  # game has not started.
                    gamestr = "{0} vs. {1} {2}".format(at, ht, status)
                    gamesort = 1  # display these first.
                else:  # game has started.
                    gamescore = self._boldleader(at, awayscore, ht, homescore)
                    # add score and format status using mlbhandler above.
                    gamestr = "{0} {1}".format(gamescore, self._handlestatus('mlb', status))
                    gamesort = 2  # display these second.
                d1games.append({'gamestr':gamestr, 'gamesort':gamesort})  # finally, add.
        # now output.
        if optinput:  # if we're searching for a team.
            count = 0  # keep count so we don't flood.
            for each in d1games:  # iterate through all.
                if optinput.lower() in each['gamestr'].lower():  # match.
                    if count < 5:  # max will be 5 out.
                        count += 1  # bump counter.
                        irc.reply(each['gamestr'])
                    else:  # max found so print error and break.
                        irc.reply("Sorry, too many matches found for '{0}'. Please be more specific.".format(optinput))
                        break
        else:  # just display scores in one row. listcmp the games into a string.
            output = " | ".join([item['gamestr'] for item in sorted(d1games, key=lambda k: k['gamesort'], reverse=True)])
            irc.reply("{0}".format(output))

    d1bb = wrap(d1bb, [optional('text')])

    def cfl(self, irc, msg, args):
        """
        Display CFL scores.
        """

        try:
            url = b64decode('aHR0cDovL20udHNuLmNhL2NmbA==')
            html = utils.web.getUrl(url)
        except utils.web.Error as e:
            self.log.error("ERROR. Could not open {0} message: {1}".format(url, e))
            irc.reply("ERROR. Could not open {0} message: {1}".format(url, e))
            return
        # process html.
        soup = BeautifulSoup(html, convertEntities=BeautifulSoup.HTML_ENTITIES, fromEncoding='utf-8')
        divs = soup.findAll('div', attrs={'id':re.compile('^\d+_score.*?')})
        for div in divs:
            # handle status
            status = div.find('div', attrs={'class':'gameSummary'}).getText().strip()
            # away stuff
            away = div.find('tr', attrs={'class':re.compile('league_row away.*?')})
            at = away.find('td', attrs={'class':'league_team'}).getText().strip()
            awayscore = away.find('td', attrs={'class':'league_score'}).getText().strip()
            # home stuff
            home = div.find('tr', attrs={'class':re.compile('league_row home.*?')})
            ht = home.find('td', attrs={'class':'league_team'}).getText().strip()
            homescore = home.find('td', attrs={'class':'league_score'}).getText().strip()
            # bold leader.
            if (awayscore.isdigit() and homescore.isdigit()):  # make sure they're digits.
                gamescore = self._boldleader(at, awayscore, ht, homescore)
            else:  # if not (in the future).
                gamescore = "{0} {1} {2} {3}".format(at, awayscore, ht, homescore)
            # output.
            irc.reply("{0} {1}".format(gamescore, status))

    cfl = wrap(cfl)

Class = Scores

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=250:
