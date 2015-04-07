###
# Copyright (c) 2015, reticulatingspline
# All rights reserved.
#
#
###
import requests
from bs4 import BeautifulSoup
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

    def _fetch(self, optsport):
        """Fetch and return HTML."""

        url = "https://m.yahoo.com/w/sports/%s/scores?.ts=1428390180&.intl=us&.lang=en" % optsport
        try:
            headers = {"User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:17.0) Gecko/17.0 Firefox/17.0"}
            page = requests.get(url, headers=headers)
            return page
        except Exception as e:
            self.log.error("ERROR. Could not open {0} message: {1}".format(url, e))
            return None

    def _scores(self, html):
        """Go through each "game" we receive and process the data."""

        soup = BeautifulSoup(html)
        games = soup.findAll('div', attrs={'class':'uip'})
        gameslist = []
        # go through each game
        for game in games:
            gametext = game.getText(separator=' ')
            gametext = ' '.join(gametext.split())
            gametext = gametext.replace(' EDT', '').replace(' pm', '').replace(' am', '')
            gameslist.append(gametext)
        # return the list of games.
        return gameslist

    ###################################
    # PUBLIC FUNCTIONS (ONE PER SPORT #
    ###################################

    def mlb(self, irc, msg, args):
        """
        Display MLB scores.
        """

        # first, declare sport.
        optsport = 'mlb'
        # base url.
        html = self._fetch(optsport)
        # container
        gameslist = self._scores(html.text)
        # strip color/bold/ansi if option is enabled.
        irc.reply("{0}".format(" | ".join(gameslist)))

    mlb = wrap(mlb)

    def nba(self, irc, msg, args):
        """
        Display NBA scores.
        """

        # first, declare sport.
        optsport = 'nba'
        # base url.
        html = self._fetch(optsport)
        # container
        gameslist = self._scores(html.text)
        # strip color/bold/ansi if option is enabled.
        irc.reply("{0}".format(" | ".join(gameslist)))

    nba = wrap(nba)

    def nhl(self, irc, msg, args):
        """
        Display NHL scores.
        """

        # first, declare sport.
        optsport = 'nhl'
        # base url.
        html = self._fetch(optsport)
        # container
        gameslist = self._scores(html.text)
        # strip color/bold/ansi if option is enabled.
        irc.reply("{0}".format(" | ".join(gameslist)))

    nhl = wrap(nhl)


Class = Scores

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
