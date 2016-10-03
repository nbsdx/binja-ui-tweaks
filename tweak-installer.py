
import os
import sys

from PyQt5 import QtCore, QtWidgets, QtGui

#sys.path.append('/home/neil/bin/binaryninja/python/')

import binaryninja as binja

import UITweaks as Tweaks

import BinjaUI as ui
from BinjaUI import Util

enabled = []
enabledTweaks = []
installedTweaks = []
done = False

# open the .tweaks file to get config
path = os.path.join(binja.user_plugin_path, ".tweaks")
try:
    f = open(path, 'r')
    for x in f:
        x = x.strip()
        if x[0] == '#':
            continue

        enabled.append(x)
except:
    done = True

if len(enabled) == 0:
    done = True

if not done:

    def StackedWidgetEventFilter(obj, evt):
        if obj == stackedWidget:
            if (evt.type() == QtCore.QEvent.ChildAdded) and (evt.child().isWidgetType()) and (evt.child().metaObject().className() == 'ViewFrame'):

                # Make sure we're setup.
                Tweaks.Util.InitUtils()

                # Install the view modification
                for tweak in enabledTweaks:
                    new_tweak = tweak()
                    wi = ui.WidgetInjector(lambda :new_tweak.install(evt.child()))
                    if wi.inject():
                        installedTweaks.append(new_tweak)


    tabWidgets    = [w for w in ui._app().allWidgets() if w.__class__ is QtWidgets.QTabWidget]
    mainTabWidget = [w for w in tabWidgets if w.parent().__class__ is QtWidgets.QMainWindow][0]
    stackedWidget = [w for w in mainTabWidget.children() if w.__class__ is QtWidgets.QStackedWidget][0]

    ui.Util.EventFilterManager.InstallOnObject(stackedWidget, StackedWidgetEventFilter)

    for tweak in Tweaks.Available:
        if tweak.name in enabled:
            enabledTweaks.append(tweak)

    binja.PluginCommand.register_for_function("__leakFunction", "", Tweaks.Util.__LeakFunction)

else:
    print 'No tweaks enabled.'
