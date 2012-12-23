###
# Copyright (c) 2012, spline
# All rights reserved.
#
#
###

import os
import supybot.conf as conf
import supybot.registry as registry
from supybot.i18n import PluginInternationalization, internationalizeDocstring

_ = PluginInternationalization('Scores')

def configure(advanced):
    # This will be called by supybot to configure this module.  advanced is
    # a bool that specifies whether the user identified himself as an advanced
    # user or not.  You should effect your configuration by manipulating the
    # registry as appropriate.
    from supybot.questions import expect, anything, something, yn
    conf.registerPlugin('Scores', True)


Scores = conf.registerPlugin('Scores')
conf.registerChannelValue(Scores, 'disableANSI', registry.Boolean(False, """Do not display any ANSI (color/bold) in output."""))
conf.registerChannelValue(Scores, 'fullteams', registry.Boolean(True, """Display full team names in output for channel? (Uses db)"""))
conf.registerGlobalValue(Scores, 'dbLocation', registry.String(os.path.abspath(os.path.dirname(__file__)) + '/db/scores.db', """Absolute path for scores.db sqlite3 database file location."""))

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=250:
