# coding=utf8
###
# Copyright (c) 2012, spline
# All rights reserved.
#
#
###

# my libs
import urllib2
from BeautifulSoup import BeautifulSoup
import re
import string
import datetime
import time
import sqlite3
import os

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
    
    def _dateFmt(self, string):
        """Return a short date string from a full date string."""
        return time.strftime('%m/%d', time.strptime(string, '%A, %B %d'))
    
    def _stringFmt(self, string):
        """Return a string split at a comma and everything before since most junk is the comma and after. Also remove common junk"""
        string2 = string.split(',', 1 )
        returnString = string2[0].replace(' PM','').replace(' AM','')
        return returnString
        
    def _colorizeString(self, string):
        """Return a string containing colorized portions of common game elements."""
        string = string.replace('Half', ircutils.mircColor('H', 'yellow')).replace('Final', ircutils.mircColor('F', 'red')).replace('1st', ircutils.mircColor('1st', 'green'))
        string = string.replace('2nd', ircutils.mircColor('2nd', 'green')).replace('3rd', ircutils.mircColor('3rd', 'green')).replace('4th', ircutils.mircColor('4th', 'green'))
        string = string.replace('Dly', ircutils.mircColor('DLY', 'yellow')).replace('Del:', ircutils.mircColor('DLY', 'yellow')).replace('PPD',ircutils.mircColor('PPD', 'yellow'))
        string = string.replace('Del', ircutils.mircColor('DLY', 'yellow')).replace('F/3OT', ircutils.mircColor('F/3OT', 'red')).replace('F/4OT', ircutils.mircColor('F/4OT', 'red'))
        string = string.replace('1OT', ircutils.mircColor('1OT', 'green')).replace('2OT', ircutils.mircColor('2OT', 'green')).replace('3OT', ircutils.mircColor('3OT', 'green'))
        string = string.replace('4OT', ircutils.mircColor('4OT', 'green')).replace('F/2OT', ircutils.mircColor('F/2OT', 'red')).replace('F/OT', ircutils.mircColor('F/OT', 'red'))
        return string
        
    # new stuff
    def _validate(self, date, format):
        """Return true or false for valid date based on format."""
        try:
            datetime.datetime.strptime(str(date), format) # format = "%m/%d/%Y"
            return True
        except ValueError:
            return False

    def _b64decode(self, string):
        """Returns base64 encoded string."""
        import base64
        return base64.b64decode(string)
    
    def _stripcomma(self, string):
        """Return a string with everything after the comma removed."""
        strings = string.split(',', 1 )
        return strings[0]
    
    def _boldleader(self, atm, asc, htm, hsc, colorize=True):
        """Input away team, away score, home team, home score and bold the leader. Adds bold if colorize=True."""
        if asc > hsc:
            if colorize:
                return("{0} {1} {2} {3}".format(self._bold(atm), self._bold(asc), htm, hsc))
            else:
                return("*{0} {1} {2} {3}".format(atm, asc, htm, hsc))
        elif hsc > asc:
            if colorize:
                return("{0} {1} {2} {3}".format(atm, asc, self._bold(htm), self._bold(hsc)))
            else:
                return("{0} {1} *{2} {3}".format(atm, asc, htm, hsc))
        else:
            return("{0} {1} {2} {3}".format(atm, asc, htm, hsc))
    
    def _formatstatus(self, string):
        """handle the formating of status without color."""
        table = {'Final':'F','Dly':'DLY','Del:':'DLY','Del':'DLY'}        
        try:
            return table[string]
        except:
            return string
    
    def _colorformatstatus(self, string):
        """Handle the formatting of a status with color."""
        table = {'Final':self._red('F'),'F/OT':self._red('F/OT'),'F/2OT':self._red('F/2OT'),
                 '1st':self._green('1st'),'2nd':self._green('2nd'),'3rd':self._green('3rd'),
                 '4th':self._green('4th'),
                 
                 'Dly':self._yellow('DLY'),'DLY':self._yellow('DLY'),'PPD':self._yellow('PPD'),
                 'Del:':self._yellow('DLT')
                 }
        try:
            return table[string]
        except:
            return string
    
    def _handlestatus(self, string, colorize=True):
        """Handle working with the time/innings/status of a game. Issue colorize=False to not colorize."""
        strings = string.split(' ', 1 ) # split at space, everything in a list w/two.       
        if len(strings) == 2: # if we have two items, like 3:00 4th
            if colorize:
                return "{0} {1}".format(strings[0], self._colorformatstatus(strings[1])) # ignore time and colorize quarter/etc.
            else:
                return "{0} {1}".format(strings[0], self._formatstatus(strings[1])) # ignore time and format quarter/etc.
        else: # game is "not in progress"
            if colorize:
                return self._colorformatstatus(strings[0]) # just return the colorized quarter/etc due to no time.
            else:
                return self._formatstatus(strings[0]) # just return the quarter/etc due to no time.
                
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
            html = (urllib2.urlopen(req)).read()
            return html
        except Exception, e:
            self.log.error("ERROR fetching: {0} message: {1}".format(url, e))
            return None

    def _scores(self, html, colorize=True, sport="", fullteams=True):
        """Go through each "game" we receive and process the data."""
        soup = BeautifulSoup(html)
        subdark = soup.find('div', attrs={'class':'sub dark'})
        games = soup.findAll('div', attrs={'id':re.compile('^game.*?')})
        gameslist = []

        for game in games: # go through each game
            game = self._stripcomma(game.getText()) # remove comma/network            
            if " at " not in game: # game is in-action.
                gparts = game.split(" ", 4) # make sure we split into parts and shove whatever status/time is in the rest. colorize if true.
                if fullteams: # should we use full team names? 
                    if sport == 'nfl' or sport == 'cfb': # conditional on NFL/CFB due to the *
                        if gparts[0].startswith('*'):
                            gparts[0] = self._transteam(gparts[0].replace('*',''), optsport=sport)
                            if game.findParent('div').findParent('div').find('b', attrs={'class':'red'}):
                                gparts[0] = "{0}{1}".format(self._red("<RZ>"),gparts[0])
                            else:
                                gparts[0] = "{0}{1}".format(self._red("<>"),gparts[0])
                        elif gparts[2].startswith('*'):
                            if game.findParent('div').findParent('div').find('b', attrs={'class':'red'}):
                                gparts[2] = "{0}{1}".format(self._red("<RZ>"),gparts[2])
                            else:
                                gparts[2] = "{0}{1}".format(self._red("<>"),gparts[2]) 
                    else: # sport is not NFL or CFB.
                        gparts[0] = self._transteam(gparts[0], optsport=sport)
                        gparts[2] = self._transteam(gparts[2], optsport=sport)
                # now handle the formatting of all items (teams, status, etc.)
                if not colorize: # work with colorization.                   
                    gamescore = self._boldleader(gparts[0], gparts[1], gparts[2], gparts[3], colorize=False)
                    output = "{0} {1}".format(gamescore, self._handlestatus(gparts[4], colorize=False))                
                else: # dont colorize.
                    gamescore = self._boldleader(gparts[0], gparts[1], gparts[2], gparts[3], colorize=True)
                    output = "{0} {1}".format(gamescore, self._handlestatus(gparts[4], colorize=True))
            else: # TEAM at TEAM time for inactive games.
                if fullteams:
                    gparts = game.replace(' PM','').replace(' AM','').split(" ", 3)
                    gparts[0] = self._transteam(gparts[0], optsport=sport)
                    gparts[2] = self._transteam(gparts[2], optsport=sport)
                    output = "{0} at {1} {2}".format(gparts[0], gparts[2], gparts[3])
                else:
                    output = game.replace(' PM','').replace(' AM','') # remove AM or PM.
            # finally add whatever output is.
            gameslist.append(output) 
        # finally, return.
        return gameslist

    def _transteam(self, optteam, optsport=""):
        db_filename = self.registryValue('dbLocation')
        
        if not os.path.exists(db_filename):
            self.log.error("ERROR: I could not find: %s" % db_filename)
            return
        
        conn = sqlite3.connect(db_filename)
        cursor = conn.cursor()
        cursor.execute("select full from teams where short=? and sport=?", (optteam, optsport))
        row = cursor.fetchone()
        cursor.close()
        if row is None:
            return optteam
        else:      
            return (str(row[0])) 

    ###########################
    # start public functions. #
    ###########################
    
    def nba(self, irc, msg, args, optlist):
        """[--date YYYYMMDD]
        Display NBA scores.
        """      
        
        # handle optlist.
        if optlist:
            for (key, value) in optlist:
                if key == 'date':
                    pass
        
        # fetch html and handle if we get back None for error.
        html = self._fetch('nba/scoreboard?')
        if html == 'None':
            irc.reply("Cannot fetch NBA scores.")
            return
        
        # process the data we get back, checking for color.
        if self.registryValue('disableANSI', msg.args[0]):
            gameslist = self._scores(html, colorize=False, sport='nba', fullteams=self.registryValue('fullteams', msg.args[0]))
        else:
            gameslist = self._scores(html, colorize=True, sport='nba', fullteams=self.registryValue('fullteams', msg.args[0]))
        
        # finally, check if there is any games/output.
        if len(gameslist) > 0:
            irc.reply(string.join([item for item in gameslist], " | "))
        else:
            irc.reply("No NBA games listed.")
    
    nba = wrap(nba, [getopts({'date':''})])
    
    def ncb(self, irc, msg, args, optconf):
        """<conference>
        Display NCB scores. Optional: add in conference to display all scores from conference.
        By default, it will display only active I-A games.
        """

        validconfs = {  'top25':'999', 'a10':'3', 'acc':'2', 'ameast':'1', 'big12':'8', 'bigeast':'4', 'bigsky':'5', 'bigsouth':'6', 'big10':'7',
                        'bigwest':'9', 'c-usa':'11', 'caa':'10', 'greatwest':'57', 'horizon':'45', 'independent':'43', 'ivy':'12', 'maac':'13',
                        'mac':'14', 'meac':'16', 'mvc':'18', 'mwc':'44', 'div-i':'50', 'nec':'19', 'non-div-i':'51', 'ovc':'20', 'pac12':'21',
                        'patriot':'22', 'sec':'23', 'southern':'24', 'southland':'25', 'summit':'49', 'sunbelt':'27', 'swac':'26', 'wac':'30', 'wcc':'29'
        }
        
        if optconf:
            optconf = optconf.lower()        
            if optconf not in validconfs:
                irc.reply("Conference must be one of: %s" % validconfs.keys())
                return
            
        url = 'ncb/scoreboard?'
        
        if not optconf:
            url += 'groupId=%s' % validconfs['top25']
        else:
            url += 'groupId=%s' % validconfs[optconf]
                        
        html = self._fetch(url)
        
        if html == 'None':
            irc.reply("Cannot fetch NCB scores.")
            return

        soup = BeautifulSoup(html)
        divs = soup.findAll('div', attrs={'id':re.compile('^game.*?')})

        append_list = []

        for div in divs:
            rows = div.findAll('a')
            for row in rows:
                game = row.text.strip().replace(';','')
                game = self._stringFmt(game)
                
                if " at " not in game: 
                    gamesplit = game.split(' ') 
                    awayteam = gamesplit[0]
                    awayscore = gamesplit[1]
                    hometeam = gamesplit[2]
                    homescore = gamesplit[3]
                    time = gamesplit[4:]
                    time = " ".join(time)
                    
                    if int(awayscore) > int(homescore):
                        awayteam = ircutils.bold(awayteam)
                        awayscore = ircutils.bold(awayscore)
                    elif int(homescore) > int(awayscore):
                        hometeam = ircutils.bold(hometeam)
                        homescore = ircutils.bold(homescore)
                    
                    game = str(awayteam + " " + awayscore + " " + hometeam + " " + homescore + " " + time) 
                
                if not optconf: # by default, only show active I-A games.
                    if " at " not in game and "Final" not in game and "F/" not in game and "PPD" not in game:
                        game = self._colorizeString(game)
                        append_list.append(game)
                else:
                    game = self._colorizeString(game)
                    append_list.append(game)
        
        if len(append_list) > 0:       
            irc.reply(string.join([item for item in append_list], " | "))
        else:
            irc.reply("No NCB games matched criteria. Try specifying a conference to show non-active games. Ex: SEC")
            
    ncb = wrap(ncb, [optional('somethingWithoutSpaces')])
    

    def cfb(self, irc, msg, args, optconf):
        """<conference>
        Display CFB scores. Optional: add in conference to display all scores from conference.
        By default, it will display only active I-A games.
        """
        
        validconfs = { 'top25':'999', 'acc':'1', 'bigeast':'10', 'bigsouth':'40', 'big10':'5', 'big12':'4',
                'bigsky':'20', 'caa':'48', 'c-usa':'12', 'independent':'18',
                'ivy':'22', 'mac':'15', 'meac':'24', 'mvc':'21', 'i-a':'80',
                'i-aa':'81', 'pac12':'9', 'southern':'29', 'sec':'8',
                'sunbelt':'37', 'wac':'16'
        }
        
        if optconf:
            optconf = optconf.lower()        
            if optconf not in validconfs:
                irc.reply("Conference must be one of: %s" % validconfs.keys())
                return
            
        url = 'ncf/scoreboard?'
        if not optconf:
            url += 'groupId=%s' % validconfs['top25']
        else:
            url += 'groupId=%s' % validconfs[optconf]
                        
        html = self._fetch(url)
        
        if html == 'None':
            irc.reply("Cannot fetch CFB scores.")
            return

        soup = BeautifulSoup(html)
        divs = soup.findAll('div', attrs={'id':re.compile('^game.*?')})

        append_list = []

        for div in divs:
            rows = div.findAll('a')
            for row in rows:
                game = row.text.strip().replace(';','')
                game = self._stringFmt(game)
                
                # rz/pos display
                if row.findParent('div').findParent('div').find('b', attrs={'class':'red'}): 
                    game = game.replace('*', ircutils.mircColor('<RZ>','red'))
                else:
                    game = game.replace('*', ircutils.mircColor('<>','red'))
                
                if " at " not in game: 
                    gamesplit = game.split(' ') 
                    awayteam = gamesplit[0]
                    awayscore = gamesplit[1]
                    hometeam = gamesplit[2]
                    homescore = gamesplit[3]
                    time = gamesplit[4:]
                    time = " ".join(time)
                    
                    if int(awayscore) > int(homescore):
                        awayteam = ircutils.bold(awayteam)
                        awayscore = ircutils.bold(awayscore)
                    elif int(homescore) > int(awayscore):
                        hometeam = ircutils.bold(hometeam)
                        homescore = ircutils.bold(homescore)
                    
                    game = str(awayteam + " " + awayscore + " " + hometeam + " " + homescore + " " + time) 
                
                if not optconf: # by default, only show active I-A games.
                    if " at " not in game and "Final" not in game and "F/" not in game and "PPD" not in game:
                        game = self._colorizeString(game)
                        append_list.append(game)
                else:
                    game = self._colorizeString(game)
                    append_list.append(game)
        
        if len(append_list) > 0:       
            irc.reply(string.join([item for item in append_list], " | "))
        else:
            irc.reply("No CFB games matched criteria. Try specifying a conference to show non-active games. Ex: SEC")
            
    cfb = wrap(cfb, [optional('somethingWithoutSpaces')])
    

    def nfl(self, irc, msg, args):
        """
        Display NFL scores.
        """
        
        url = 'nfl/scoreboard?'
        html = self._fetch(url)
        
        if html == 'None':
            irc.reply("Cannot fetch NFL scores.")
            return
            
        html = html.replace('class="ind alt', 'class="ind')
        
        if "No games" in html:
            irc.reply("No games on today.")
            return

        soup = BeautifulSoup(html)
        divs = soup.findAll('div', attrs={'id':re.compile('game.*?')})

        object_list = []

        for div in divs:
            rows = div.findAll('a')
            for row in rows:
                game = row.text.strip()
                game = self._stringFmt(game)
                
                if row.findParent('div').findParent('div').find('b', attrs={'class':'red'}):
                    game = game.replace('*', ircutils.mircColor('<RZ>','red'))
                else:
                    game = game.replace('*', ircutils.mircColor('<>','red'))
                
                game = self._colorizeString(game)
                
                if " at " not in game: 
                    gamesplit = game.split(' ') 
                    awayteam = gamesplit[0]
                    awayscore = gamesplit[1]
                    hometeam = gamesplit[2]
                    homescore = gamesplit[3]
                    time = gamesplit[4:]
                    time = " ".join(time)
                    
                    # bold the leader
                    if int(awayscore) > int(homescore):
                        awayteam = ircutils.bold(awayteam)
                        awayscore = ircutils.bold(awayscore)
                    elif int(homescore) > int(awayscore):
                        hometeam = ircutils.bold(hometeam)
                        homescore = ircutils.bold(homescore)
                
                    game = str(awayteam + " " + awayscore + " " + hometeam + " " + homescore + " " + time) 

                object_list.append(game)

        if len(object_list) > 0:
            irc.reply(string.join([item for item in object_list], " | "))
        else:
            irc.reply("No NFL games listed.")

    nfl = wrap(nfl)
    
    def mlb(self, irc, msg, args, optdate):
        """<YYYYmmdd>
        Display MLB scores. Optional: Add in date to display scores on date. Ex: 20120904.
        """
    
        if optdate:
            testdate = self._validate(optdate, '%Y%m%d')
            if not testdate:
                irc.reply("Invalid date. Must be YYYYmmdd. Ex: 20120904")
                return

        url = 'mlb/scoreboard?'

        if optdate:
            url += 'date=%s' % optdate

        html = self._fetch(url)

        if html == 'None':
            irc.reply("Cannot fetch mlb scores.")
            return
            
        html = html.replace('class="ind alt', 'class="ind')
        
        if "No games" in html:
            irc.reply("No games on today.")
            return

        soup = BeautifulSoup(html)
        rows = soup.findAll('div', attrs={'class':'ind', 'style':'white-space: nowrap;'})

        object_list = []

        for row in rows:
            game = row.find('a').text.strip()
            game = self._stringFmt(game) # remove after comma.
            game = game.replace('SDG', 'SD').replace('SFO', 'SF').replace('TAM', 'TB').replace('WAS', 'WSH').replace('KAN', 'KC').replace('CHW', 'CWS') # fix teams.            
            game = self._colorizeString(game) # colorize status.
            
            if " at " not in game: 
                game = game.replace('Bot ','B').replace('Top ','T').replace('Mid ','M').replace('End ','E') # innings
                game = game.replace('st','').replace('th','').replace('rd','').replace('nd','') # abbr
                gamesplit = game.split(' ') 
                awayteam = gamesplit[0]
                awayscore = gamesplit[1]
                hometeam = gamesplit[2]
                homescore = gamesplit[3]
                innings = gamesplit[4]

                if int(awayscore) > int(homescore):
                    awayteam = ircutils.bold(awayteam)
                    awayscore = ircutils.bold(awayscore)
                elif int(homescore) > int(awayscore):
                    hometeam = ircutils.bold(hometeam)
                    homescore = ircutils.bold(homescore)
                
                game = str(awayteam + " " + awayscore + " " + hometeam + " " + homescore + " ") 
                if innings.startswith('F'):
                    innings = innings.replace('Final','F')
                    game += ircutils.mircColor(innings, 'red')
                else:
                    game += ircutils.mircColor(innings, 'green')

            object_list.append(game)

        if len(object_list) > 0:
            irc.reply(string.join([item for item in object_list], " | "))
        else:
            irc.reply("No current MLB games.")

    mlb = wrap(mlb, [optional('somethingWithoutSpaces')])
    
    
    def tennis(self, irc, msg, args, optmatch):
        """<mens|womens|mensdoubles|womensdoubles>
        Display current Tennis scores. Defaults to Men's Singles.
        """
        
        if optmatch:
            if optmatch == "womens":
                matchType = "2"
            elif optmatch == "mensdoubles":
                matchType = "3"
            elif optmatch == "womensdoubles":
                matchType = "4"
            else:
                matchType = "1"
        else:
            matchType = "1"
        
        url = 'general/tennis/dailyresults?matchType=%s' % matchType
        
        html = self._fetch(url)
        
        if html == 'None':
            irc.reply("Cannot fetch Tennis scores.")
            return
        
        soup = BeautifulSoup(html)
        tournament = soup.find('div', attrs={'class': 'sec row', 'style': 'white-space: nowrap;'})
        tournRound = soup.findAll('div', attrs={'class': 'ind sub bold'})[1] # there are two here, only display the 2nd, which is status.
        divs = soup.findAll('div', attrs={'class':re.compile('^ind$|^ind alt$')}) 

        append_list = []

        for div in divs:
            if "a href" not in div.renderContents(): # only way to get around this as the divs are not in a container.
                status = div.find('b') # find bold, which is status.
                if status:
                    status.extract() # extract so we may bold.
                
                div = div.renderContents().strip().replace('<br />',' ').replace('  ',' ')
                div = div.replace('v.',ircutils.mircColor('v.','green')).replace('d.',ircutils.mircColor('d.','red')) # colors.
                append_list.append(str(ircutils.underline(status.getText()) + " " + div.strip()))
            
        if len(append_list) > 0: # Sanity check.
            if tournament and tournRound:
                irc.reply(ircutils.mircColor(tournament.getText(), 'red') + " - " + ircutils.bold(tournRound.getText()))
                
            irc.reply(" | ".join(item for item in append_list))
        else:
            irc.reply("I did not find any active tennis matches.") 

    tennis = wrap(tennis, [optional('somethingWithoutSpaces')])
    
    
    def golf(self, irc, msg, args):
        """
        Display current Golf scores from a PGA tournament.
        """
        
        url = 'golf/eventresult?'
        
        html = self._fetch(url)
        
        if html == 'None':
            irc.reply("Cannot fetch Golf scores.")
            return
        
        soup = BeautifulSoup(html)
        golfEvent = soup.find('div', attrs={'class': 'sub dark big'})
        golfStatus = soup.find('div', attrs={'class': 'sec row', 'style': 'white-space: nowrap;'})

        if str(golfEvent.getText()).startswith("Ryder Cup"): # special status for Ryder Cup.
            rows = soup.find('div', attrs={'class':'ind'})
            
            irc.reply(ircutils.mircColor(golfEvent.getText(), 'green'))
            irc.reply("{0}".format(rows.getText()))
            return
        else:
            table = soup.find('table', attrs={'class':'wide'})
            if not table:
                irc.reply("Could not find golf results. Tournament not going on?")
                return    
            rows = table.findAll('tr')[1:14] # skip header row. max 13.

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
                pRound = pRound.split()[1] # 2nd element after space split.
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
