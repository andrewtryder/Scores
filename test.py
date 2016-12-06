###
# Copyright (c) 2015, reticulatingspline
# All rights reserved.
#
#
###

from supybot.test import *


class ScoresTestCase(PluginTestCase):
    plugins = ('Scores',)

    def testNfl(self):
        self.assertNotError('nfl')

    def testMlb(self):
        self.assertNotError('mlb')

    def testNba(self):
        self.assertNotError('nba')

    def testCfb(self):
        self.assertNotError('cfb')

    def testNhl(self):
        self.assertNotError('nhl')

    def testGolf(self):
        self.assertNotError('golf')


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
