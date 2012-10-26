# coding=utf8
###
# Copyright (c) 2012, spline
# All rights reserved.
#
#
###

import urllib2
from BeautifulSoup import BeautifulSoup
import re
import string
import datetime
import time

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
    
    def _validate(self, date, format):
        """Return true or false for valid date based on format."""
        try:
            datetime.datetime.strptime(date, format) # format = "%m/%d/%Y"
            return True
        except ValueError:
            return False

    def _b64decode(self, string):
        """Returns base64 encoded string."""
        import base64
        return base64.b64decode(string)

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
        string = string.replace('Half', ircutils.mircColor('H', 'yellow')).replace('Final', ircutils.mircColor('F', 'red')).replace('F/OT', ircutils.mircColor('F/OT', 'red'))
        string = string.replace('F/OT2', ircutils.mircColor('F/OT2', 'red')).replace('1st', ircutils.mircColor('1st', 'green')).replace('2nd', ircutils.mircColor('2nd', 'green'))
        string = string.replace('3rd', ircutils.mircColor('3rd', 'green')).replace('4th', ircutils.mircColor('4th', 'green')).replace('PPD', ircutils.mircColor('PPD', 'yellow'))
        string = string.replace('Dly', ircutils.mircColor('DLY', 'yellow')).replace('Del:', ircutils.mircColor('DLY', 'yellow')).replace('PPD',ircutils.mircColor('PPD', 'yellow'))
        string = string.replace('Del', ircutils.mircColor('DLY', 'yellow')).replace('F/OT3', ircutils.mircColor('F/OT3', 'red'))
        return string

    def _fetch(self, optargs):
        """Fetch scores."""
        
        url = self._b64decode('aHR0cDovL20uZXNwbi5nby5jb20v') + '%s&wjb=' % optargs
        
        #self.log.info(url)
                
        try:
            req = urllib2.Request(url)
            html = (urllib2.urlopen(req)).read()
            return html
        except:
            return None


    ###########################
    # start public functions. #
    ###########################
    

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
            url += 'groupId=%s' % validconfs['i-a']
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
    
    
    def nba(self, irc, msg, args, optdate):
        """<YYYYmmdd>
        Display NBA scores. Optional: add in date to specify games/scores on date.
        """
        
        if optdate:
            testdate = self._validate(optdate, '%Y%m%d')
            if not testdate:
                irc.reply("Invalid year. Must be YYYYmmdd. Ex: 20120904")
                return
        else: # use today's date here, instead of with others. 
            optdate = datetime.datetime.now().strftime("%Y%m%d")

        url = 'nba/scoreboard?'
        
        if optdate:
            url += 'date=%s' % optdate
        
        html = self._fetch(url)

        if html == 'None':
            irc.reply("Cannot fetch NBA scores.")
            return
        
        soup = BeautifulSoup(html)
        divs = soup.findAll('div', attrs={'id':re.compile('game.*?')})
        
        append_list = []
        
        for div in divs:
            game = self._stringFmt(div.getText()) # strip all past ,
            game = self._colorizeString(game) # colorize the status.
            
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
            
            append_list.append(game)
        
        if len(append_list) > 0:
            irc.reply(string.join([item for item in append_list], " | "))
        else:
            irc.reply("No current NBA games.")
    
    nba = wrap(nba, [optional('somethingWithoutSpaces')])
    
    
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
