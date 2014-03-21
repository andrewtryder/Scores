###
# Copyright (c) 2012-2014, spline
# All rights reserved.
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
conf.registerChannelValue(Scores, 'fullteams', registry.Boolean(False, """Display full team names in output for channel? (Uses db)"""))
conf.registerChannelValue(Scores, 'lineByLineScores', registry.Boolean(False, """Display full team names in output for channel? (Uses db)"""))
conf.registerGlobalValue(Scores, 'logURLs', registry.Boolean(False, """Should we log all URL calls?"""))
conf.registerGlobalValue(Scores, 'wilbonton', registry.Boolean(False, """DONT TURN THIS ON UNLESS YOU KNOW WHAT IT IS."""))

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=250:
