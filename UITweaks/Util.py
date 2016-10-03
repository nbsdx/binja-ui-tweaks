
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import Qt

import BinjaUI as ui

import sys

_leakedFunction = None
_leakedView = None
_leakedFunctionAction = None

def __LeakFunction(bv, cf):
    global _leakedFunction
    global _leakedView

    _leakedView = bv
    _leakedFunction = cf

"""
    Leak the current function being viewed. This function
    is very noisy, since it logs stuff out to the Log, and
    does some other Plugin stuff.
"""
def CurrentFunction():
    global _leakedFunction
    global _leakedFunctionAction

    if _leakedFunctionAction:
        _leakedFunctionAction.trigger()
        return _leakedFunction

    else:
        return None

def CurrentView():
    global _leakedView
    global _leakedFunctionAction

    if _leakedFunctionAction:
        _leakedFunctionAction.trigger()
        return _leakedView

    else:
        return None

def InitUtils():

    # Find the __LeakFunction action.
    global _leakedFunction
    global _leakedFunctionAction

    if _leakedFunctionAction:
        return

    toolsMenu = ui.Components.Menu("Tools")

    # Remove the dummy function from the Tools menu
    # TODO: Remove it from the right-click menus
    for action in toolsMenu.actions():
        sys.__stdout__.write("[Action: {}]\n".format(action.text()))
        if action.text() == "__leakFunction":
            action.setVisible(False)
            toolsMenu.removeAction(action)
            _leakedFunctionAction = action
            sys.__stdout__.write("Found __leakFunction QAction\n")


