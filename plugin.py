# coding=utf8
###
# Copyright (c) 2012, spline
# All rights reserved.
#
#
###

# my libs
import urllib2
from BeautifulSoup import BeautifulSoup, NavigableString
import re
import string
import datetime
import time
import sqlite3
import os
from itertools import groupby, izip, count

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

    def _splicegen(self, maxchars, stringlist):
        """ Return a list of slices to print based on maxchars string-length boundary."""
        count = 0  # start at 0
        slices = []  # master list to append slices to.
        tmpslices = []  # tmp list where we append slice numbers.

        for i, each in enumerate(stringlist):
            itemlength = len(each)
            runningcount = count + itemlength
            if runningcount < int(maxchars):
                count = runningcount
                tmpslices.append(i)
            elif runningcount > int(maxchars):
                slices.append(tmpslices)
                tmpslices = []
                count = 0 + itemlength
                tmpslices.append(i)
            if i==len(stringlist)-1:
                slices.append(tmpslices)
        return slices

    # new stuff
    def _batch(self, iterable, size):
        """http://code.activestate.com/recipes/303279/#c7"""
        c = count()
        for k, g in groupby(iterable, lambda x:c.next()//size):
            yield g

    def _validate(self, date, format):
        """Return true or false for valid date based on format."""
        try:
            datetime.datetime.strptime(str(date), format) # format = "%Y%m%D"
            return True
        except ValueError:
            return False

    def _b64decode(self, string):
        """Returns base64 encoded string."""
        import base64
        return base64.b64decode(string)

    def _stripcomma(self, string):
        """Return a string with everything after the comma removed."""
        strings = string.split(',',1)
        return strings[0]

    def _boldleader(self, atm, asc, htm, hsc):
        """Input away team, away score, home team, home score and bold the leader."""
        if int(asc) > int(hsc):
            return("{0} {1} {2} {3}".format(self._bold(atm), self._bold(asc), htm, hsc))
        elif int(hsc) > int(asc):
            return("{0} {1} {2} {3}".format(atm, asc, self._bold(htm), self._bold(hsc)))
        else:
            return("{0} {1} {2} {3}".format(atm, asc, htm, hsc))

    def _colorformatstatus(self, string):
        """Handle the formatting of a status with color."""
        table = {# Red
                 'Final':self._red('F'),'F/OT':self._red('F/OT'),'F/2OT':self._red('F/2OT'),
                 'Canc':self._red('CAN'),'F/SO':self._red('F/SO'),
                 # Green
                 '1st':self._green('1st'),'2nd':self._green('2nd'),'3rd':self._green('3rd'),
                 '4th':self._green('4th'),'OT':self._green('OT'),'SO':self._green('SO'),
                 # Yellow
                 'Half':self._yellow('H'),'Dly':self._yellow('DLY'),'DLY':self._yellow('DLY'),
                 'PPD':self._yellow('PPD'),'Del:':self._yellow('DLT'),'Int':self._yellow('INT')
                 }
        try:
            return table[string]
        except:
            return string

    def _handlestatus(self, string):
        """Handle working with the time/innings/status of a game."""
        strings = string.split(' ', 1 ) # split at space, everything in a list w/two.
        if len(strings) == 2: # if we have two items, like 3:00 4th
            return "{0} {1}".format(strings[0], self._colorformatstatus(strings[1])) # ignore time and colorize quarter/etc.
        else: # game is "not in progress"
            return self._colorformatstatus(strings[0]) # just return the colorized quarter/etc due to no time.

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

    def _fetch(self, optargs):
        """HTML Fetch."""
        url = self._b64decode('aHR0cDovL20uZXNwbi5nby5jb20v') + '%s&wjb=' % optargs
        try:
            req = urllib2.Request(url)
            #req.add_header("User-Agent","Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:17.0) Gecko/17.0 Firefox/17.0")
            html = (urllib2.urlopen(req)).read()
            return html
        except Exception, e:
            self.log.error("ERROR fetching: {0} message: {1}".format(url, e))
            return None

    # div = soup.find('div', attrs={'class':'sub dark'})
    # div.a.extract()
    # div.a.extract()
    # div = div.getText().replace('|','').strip()
    # today = datetime.datetime.now().strftime('%b %d').upper()

    def _scores(self, html, sport="", fullteams=True):
        """Go through each "game" we receive and process the data."""
        soup = BeautifulSoup(html)
        subdark = soup.find('div', attrs={'class':'sub dark'})
        games = soup.findAll('div', attrs={'id':re.compile('^game.*?')})
        # setup the list for output.
        gameslist = []

        # go through each game
        for game in games:
            gametext = self._stripcomma(game.getText())  # remove cruft after comma.
            if " at " not in gametext:  # game is in-action.
                if sport == 'nfl' or sport == 'ncb':  # special for NFL/NCB to display POS.
                    if game.find('b', attrs={'class': 'red'}):
                        gametext = gametext.replace('*', '<RZ>')
                    else:
                        gametext = gametext.replace('*', '<>')
                # make sure we split into parts and shove whatever status/time is in the rest.
                gparts = gametext.split(" ",4)
                if fullteams:  # gparts[0] = away/2=home. full translation table.
                    gparts[0] = self._transteam(gparts[0], optsport=sport)
                    gparts[2] = self._transteam(gparts[2], optsport=sport)
                # last exception: color <RZ> or * if we have them.
                if sport == 'nfl' or sport == 'ncb':  # cheap but works.
                    gparts[0] = gparts[0].replace('<RZ>', self._red('<RZ>')).replace('<>', self._red('<>'))
                    gparts[2] = gparts[2].replace('<RZ>', self._red('<RZ>')).replace('<>', self._red('<>'))
                # now bold the leader and format output.
                gamescore = self._boldleader(gparts[0], gparts[1], gparts[2], gparts[3])
                output = "{0} {1}".format(gamescore, self._handlestatus(gparts[4]))
                gameslist.append(output)
            else:  # TEAM at TEAM time for inactive games.
                gparts = gametext.split(" ", 3)  # remove AM/PM in split.
                if fullteams:  # full teams.
                    gparts[0] = self._transteam(gparts[0], optsport=sport)
                    gparts[2] = self._transteam(gparts[2], optsport=sport)
                output = "{0} at {1} {2}".format(gparts[0], gparts[2], gparts[3])
                gameslist.append(output)  # finally add whatever output is.
        return gameslist  # return the list of games.

    # translation function that needs a team and sport.
    def _transteam(self, optteam, optsport=""):
        # first check for db. bailout if not found.
        db_filename = self.registryValue('dbLocation')
        if not os.path.exists(db_filename):
            self.log.error("ERROR: I could not find: %s" % db_filename)
            return optteam
        # do some regex here to parse out the team.
        partsregex = re.compile(r'(?P<pre>\<RZ\>|\<\>)?(?P<team>[A-Z\-&;]+)(?P<rank>\(\d+\))?')
        self.log.info(optteam)
        m = partsregex.search(optteam)
        self.log.info(optteam)
        # replace optteam with the team if we have it
        if m.group('team'):
            optteam = m.group('team')
        self.log.info(optteam)
        conn = sqlite3.connect(db_filename)
        cursor = conn.cursor()
        cursor.execute("select full from teams where short=? and sport=?", (optteam, optsport))
        row = cursor.fetchone()
        cursor.close()
        # get team back if it's in the db.
        if row is None:
            team = optteam
        else:
            team = str(row[0])
        # now lets build for output.
        output = ""  # blank string to start.
        if m.group('pre'):   # readd * or <RZ>
            self.log.info("We have pre.")
            output += m.group('pre')
        self.log.info(output)
        output += team  # now team.
        self.log.info(output)
        if m.group('rank'):
            output += m.group('rank')
        self.log.info(output)
        # finally, return output.
        return output

    ###########################
    # start public functions. #
    ###########################

    def nba(self, irc, msg, args, optlist, optinput):
        """[--date YYYYMMDD] [optional]
        Display NBA scores.
        Use --date YYYYMMDD to display scores on specific date. Ex: --date 20121225
        Specify a string to match after to only display specific scores. Ex: Knick
        """

        # handle optlist.
        url = 'nba/scoreboard?'
        if optlist:
            for (key, value) in optlist:
                if key == 'date':
                    if len(str(value)) !=8 or not self._validate(value, '%Y%m%d'):
                        irc.reply("Invalid date. Must be YYYYmmdd. Ex: 20120904")
                        return
                    else:
                        url += 'date=%s' % value

        # fetch html and handle if we get back None for error.
        html = self._fetch(url)
        if html == 'None':
            irc.reply("Cannot fetch NBA scores.")
            return

        # now, process html and put all into gameslist.
        gameslist = self._scores(html, sport='nba', fullteams=self.registryValue('fullteams', msg.args[0]))

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
            else:  # no input. just display games.
                for splice in self._splicegen('380', gameslist):
                    irc.reply(string.join([gameslist[item] for item in splice], " | "))
        else:  # no games
            irc.reply("No NBA games listed.")

    nba = wrap(nba, [getopts({'date':('int')}), optional('text')])

    def nhl(self, irc, msg, args, optlist, optinput):
        """[--date YYYYMMDD] [optional]
        Display NHL scores.
        Use --date YYYYMMDD to display scores on specific date. Ex: --date 20121225
        Specify a string to match after to only display specific scores. Ex: Rang
        """

        # handle optlist.
        url = 'nhl/scoreboard?'
        if optlist:
            for (key, value) in optlist:
                if key == 'date':
                    if len(str(value)) !=8 or not self._validate(value, '%Y%m%d'):
                        irc.reply("Invalid date. Must be YYYYmmdd. Ex: 20120904")
                        return
                    else:
                        url += 'date=%s' % value

        # fetch html and handle if we get back None for error.
        html = self._fetch(url)
        if html == 'None':
            irc.reply("Cannot fetch NHL scores.")
            return

        # now, process html and put all into gameslist.
        gameslist = self._scores(html, sport='nhl', fullteams=self.registryValue('fullteams', msg.args[0]))

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
            else:  # no input. just display games.
                for splice in self._splicegen('380', gameslist):
                    irc.reply(string.join([gameslist[item] for item in splice], " | "))
        else:  # no games
            irc.reply("No NHL games listed.")

    nhl = wrap(nhl, [getopts({'date':('int')}), optional('text')])

    def nfl(self, irc, msg, args, optinput):
        """[team]
        Display NFL scores.
        Specify a string to match after to only display specific scores. Ex: Pat
        """

        # fetch html and handle if we get back None for error.
        html = self._fetch('nfl/scoreboard?')
        if html == 'None':
            irc.reply("Cannot fetch NFL scores.")
            return

        # now, process html and put all into gameslist.
        gameslist = self._scores(html, sport='nfl', fullteams=self.registryValue('fullteams', msg.args[0]))

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
            else:  # no input. just display games.
                for splice in self._splicegen('380', gameslist):
                    irc.reply(string.join([gameslist[item] for item in splice], " | "))
        else:  # no games
            irc.reply("No NFL games listed.")

    nfl = wrap(nfl, [optional('text')])

    def ncb(self, irc, msg, args, optconf):
        """[conference|team]
        Display College Basketball scores.
        Optional: input CONFERENCE or TEAM to search scores by conference or display an individual team's score.
        Ex: SEC or Bama
        """

        # basketball confs.
        validconfs = {'top25':'999', 'a10':'3', 'acc':'2', 'ameast':'1', 'big12':'8', 'bigeast':'4', 'bigsky':'5', 'bigsouth':'6', 'big10':'7',
                      'bigwest':'9', 'c-usa':'11', 'caa':'10', 'greatwest':'57', 'horizon':'45', 'independent':'43', 'ivy':'12', 'maac':'13',
                      'mac':'14', 'meac':'16', 'mvc':'18', 'mwc':'44', 'div-i':'50', 'nec':'19', 'non-div-i':'51', 'ovc':'20', 'pac12':'21',
                      'patriot':'22', 'sec':'23', 'southern':'24', 'southland':'25', 'summit':'49', 'sunbelt':'27', 'swac':'26', 'wac':'30', 'wcc':'29' }

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

        html = self._fetch(url)
        if html == 'None':
            irc.reply("Cannot fetch NCB scores.")
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
            else:  # no input. just display games.
                for splice in self._splicegen('380', gameslist):
                    irc.reply(string.join([gameslist[item] for item in splice], " | "))
        else:  # no games
            irc.reply("No college basketball games listed.")

    ncb = wrap(ncb, [optional('text')])

    def cfb(self, irc, msg, args, optconf, optinput):
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
            url = 'ncb/scoreboard?groupId=%s' % validconfs['i-a']
        elif optconf and not optinput:
            url = 'ncb/scoreboard?groupId=%s' % validconfs[optconf]
        else:
            url = 'ncb/scoreboard?groupId=%s' % validconfs['top25']

        html = self._fetch(url)
        if html == 'None':
            irc.reply("Cannot fetch CFB scores.")
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
            else:  # no input. just display games.
                for splice in self._splicegen('380', gameslist):
                    irc.reply(string.join([gameslist[item] for item in splice], " | "))
        else:  # no games
            irc.reply("No college football games listed.")

    cfb = wrap(cfb, [optional('text')])

    def mlb(self, irc, msg, args, optlist, optinput):
        """[--date YYYYMMDD] [optional]
        Display MLB scores.
        Use --date YYYYMMDD to display scores on specific date. Ex: --date 20121225
        Specify a string to match after to only display specific scores. Ex: Yank
        """

        # handle optlist.
        url = 'mlb/scoreboard?'
        if optlist:
            for (key, value) in optlist:
                if key == 'date':
                    if len(str(value)) !=8 or not self._validate(value, '%Y%m%d'):
                        irc.reply("Invalid date. Must be YYYYmmdd. Ex: 20120904")
                        return
                    else:
                        url += 'date=%s' % value

        # fetch html and handle if we get back None for error.
        html = self._fetch(url)
        if html == 'None':
            irc.reply("Cannot fetch MLB scores.")
            return

        # now, process html and put all into gameslist.
        gameslist = self._scores(html, sport='mlb', fullteams=self.registryValue('fullteams', msg.args[0]))

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
            else: # no input. just display games.
                for splice in self._splicegen('380', gameslist):
                    irc.reply(string.join([gameslist[item] for item in splice], " | "))
        else: # no games
            irc.reply("No MLB games listed.")

    mlb = wrap(mlb, [getopts({'date':('int')}), optional('text')])


    def tennis(self, irc, msg, args, optmatch):
        """[mens|womens|mensdoubles|womensdoubles|mixeddoubles]
        Display current Tennis scores. Defaults to Men's Singles.
        Call with argument to display others. Ex: womens
        """

        if optmatch:
            optmatch = optmatch.lower()
            if optmatch == "womens":
                matchType = "2"
            elif optmatch == "mensdoubles":
                matchType = "3"
            elif optmatch == "womensdoubles":
                matchType = "4"
            elif optmatch == "mixeddoubles":
                matchType = "6"
            else:
                matchType = "1"
        else:
            matchType = "1"

        html = self._fetch('general/tennis/dailyresults?matchType=%s' % matchType)
        if html == 'None':
            irc.reply("Cannot fetch Tennis scores.")
            return

        # one easy sanity check.
        if "There are no matches scheduled." in html:
            irc.reply("ERROR: There are no matches scheduled for: %s" % optmatch)
            return

        # process html.
        soup = BeautifulSoup(html,convertEntities=BeautifulSoup.HTML_ENTITIES)
        matches = soup.findAll('div', attrs={'class':re.compile('^ind|^ind alt')})
        if len(matches) < 1:  # second sanity check.
            irc.reply("ERROR: No %s tennis matches found" % optmatch)
            return
        title = soup.find('div', attrs={'class':'sec row'})
        tennisRound = soup.findAll('div', attrs={'class':'ind sub bold'})[1]

        # now iterate through each match and populate output.
        output = []
        for each in matches:
            if each.find('b'):  # <b> means it is a tennis match.
                status = each.find('b').extract()
                if status.text == "Final":
                    status = self._red("F")
                else:
                    status = self._bold(status.text)
                matchText = []
                for item in each.contents:
                    if isinstance(item, NavigableString):
                        matchText.append(item.strip())
                output.append("{0} :: {1}".format(status," ".join(matchText)))

        # now output.
        if len(output) < 1:
            irc.reply("Error: no matches to output.")
        elif len(output) < 6:
            irc.reply("{0} {1}".format(self._bold(title.getText()),self._bold(tennisRound.getText())))
            for each in output:
                irc.reply("{0}".format(each))
        else:
            irc.reply("{0} {1}".format(self._bold(title.getText()),self._bold(tennisRound.getText())))
            irc.reply("{0}".format(" | ".join(output)))

    tennis = wrap(tennis, [optional('somethingWithoutSpaces')])


    def golf(self, irc, msg, args):
        """
        Display current Golf scores from a PGA tournament.
        """

        html = self._fetch('golf/eventresult?')
        if html == 'None':
            irc.reply("Cannot fetch Golf scores.")
            return

        soup = BeautifulSoup(html)
        golfEvent = soup.find('div', attrs={'class': 'sub dark big'})
        golfStatus = soup.find('div', attrs={'class': 'sec row', 'style': 'white-space: nowrap;'})

        if str(golfEvent.getText()).startswith("Ryder Cup"):  # special status for Ryder Cup.
            rows = soup.find('div', attrs={'class':'ind'})

            irc.reply(ircutils.mircColor(golfEvent.getText(), 'green'))
            irc.reply("{0}".format(rows.getText()))
            return
        else:
            table = soup.find('table', attrs={'class':'wide'})
            if not table:
                irc.reply("Could not find golf results. Tournament not going on?")
                return
            rows = table.findAll('tr')[1:14]  # skip header row. max 13.

        append_list = []

        for row in rows:
            tds = row.findAll('td')
            pRank = tds[0].getText()
            pPlayer = tds[1].getText()
            pScore = tds[2].getText()
            pRound = tds[3].getText()
            if "am" in pRound or "pm" in pRound:
                appendString = str(pRank + ". " + ircutils.bold(pPlayer) + " " + pScore + " (" + pRound + ")")
            else:
                pRound = pRound.split()[1]  # 2nd element after space split.
                appendString = str(pRank + ". " + ircutils.bold(pPlayer) + " " + pScore + " " + pRound) # don't need "(" here because it already has it.
            append_list.append(appendString)

        if len(append_list) > 0:
            if golfEvent != None and golfStatus != None:
                irc.reply(ircutils.mircColor(golfEvent.getText(), 'green') + " - " + ircutils.bold(golfStatus.getText()))
            irc.reply(string.join([item for item in append_list], " | "))
        else:
            irc.reply("No current Golf scores.")

    golf = wrap(golf)

Class = Scores


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=250:
