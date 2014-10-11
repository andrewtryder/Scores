###
# Copyright (c) 2012-2014, spline
# All rights reserved.
###

from supybot.test import *

class ScoresTestCase(PluginTestCase):
    plugins = ('Scores',)
    
    def testScores(self):
        #  cfb, cfl, d1bb, golf, mlb, nascar, nba, ncb, ncw, nfl, nhl, racing, tennis, and wnba
        conf.supybot.plugins.Scores.disableANSI.setValue('True')
        self.assertNotError('cfb')
        self.assertNotError('cfl')
        self.assertNotError('d1bb')
        self.assertNotError('golf')
        self.assertNotError('mlb')
        self.assertNotError('nascar')
        self.assertNotError('nba')
        self.assertNotError('ncb')
        self.assertNotError('ncw')
        self.assertNotError('nfl')
        self.assertNotError('nhl')
        self.assertNotError('racing f1')
        self.assertNotError('tennis')
        self.assertNotError('wnba')
        



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
