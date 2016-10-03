
import sys

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import Qt

import BinjaUI as ui

refs = []

"""
    Custom Table View so we can sort the function list.
    Also handles forwarding key events to the orignal
    view so we can leverage it's key pressed handler to
    do filtering.

"""
class MyTableView(QtWidgets.QTableView):

    def __init__(self, parent, list_view):
        QtWidgets.QTableView.__init__(self, parent)
        self.lv = list_view

    # We just forward the KeyPress to the old handler
    def keyPressEvent(self, evt):
        if evt.type() == QtCore.QEvent.KeyPress:
            ui._app().notify(self.lv, evt)

"""
    A custom QSortFilterProxyModel that does two things:
        1. Defines a header for the Function List
        2. Handles moving to a function in the UI
"""
class MyModel(QtCore.QSortFilterProxyModel):

    def __init__(self):
        QtCore.QSortFilterProxyModel.__init__(self)

    def headerData(self, sec, orientation, role=Qt.DisplayRole):
        if (sec == 0) and (orientation == Qt.Horizontal) and (role == Qt.DisplayRole):
            return "Function Name"
        return self.sourceModel().headerData(sec, orientation, role)

    """
        TODO: Present the user with a list of functions to choose from
        if there's more than one available.
    """
    def onActivated(self, index):
        from . import Util
        bv = Util.CurrentView()
        symbols = bv.get_symbols_by_name(self.data(index))

        if len(symbols) == 1:
            bv.file.navigate(bv.file.view, symbols[0].address)

        elif len(symbols) == 0:
            print "No symbol with name [[{}]] found".format(self.data(index))

        else:
            print "Multiple symbols found"

class Plugin:
    name = "sortable-function-window"

    def __init__(self):
        self.ignore = False
        self.isSearching = False
        self.widet = None
        self.old_widget = None
        self.filter_edit = None
        self.originalPosition = None

    def eventFilter(self, obj, evt):
        # We're infinite looping when we notify
        # the target of its event, so disable
        # ourself if we're delivering the event
        if self.ignore:
            return False

        # Get the keypresses on the QTableView we make. For some reason
        # we can't see them...
        if (obj == self.widget) and (evt.type() == QtCore.QEvent.KeyPress):

            if not self.isSearching:
                self.originalPosition = self.widget.verticalScrollBar().sliderPosition()

            self.isSearching = True
            self.ignore = True
            ui._app().notify(self.widget, evt)
            self.ignore = False
            return True

    def lineEditFilter(self, obj, evt):
        if (evt.type() == QtCore.QEvent.Hide) and obj == self.filter_edit:
            self.isSearching = False
            self.widget.setFocus(Qt.ActiveWindowFocusReason)
            if self.originalPosition:
                self.widget.verticalScrollBar().setSliderPosition(self.originalPosition)
                self.originalPosition = None
            return True
        return False

    def fontChangeFilter(self, obj, evt):
        if (evt.type() == QtCore.QEvent.FontChange) and (obj == self.old_widget):
            self.widget.setFont(self.old_widget.font())
            fm = QtGui.QFontMetrics(self.old_widget.font())
            self.widget.verticalHeader().setDefaultSectionSize(fm.height())

            return True
        return False

    def install(self, view_widget):

        widgets = view_widget.findChildren(QtWidgets.QAbstractScrollArea)
        func_list = [x for x in widgets if x.metaObject().className() == 'FunctionList'][0]

        # Get the function List from BinjaUI
        #func_list = ui.Components.FunctionWindow()

        # Find the QListView that contains the original Function Model
        #sys.__stdout__.write("FunctionList.children(): {}\n".format(func_list.children()))
        #self.old_widget = [x for x in func_list.children() if x.__class__ is QtWidgets.QListView][0]
        self.old_widget = func_list
        ui.Util.EventFilterManager.InstallOnObject(self.old_widget, self.fontChangeFilter)

        # Construct our new QTableView that forwards events on to the original ListView
        self.widget = MyTableView(func_list, self.old_widget)

        # For some reason, our QTableView isn't getting events. Install this EventFilter
        # globally (very hacky) and intercept any events triggered by the new QTableView
        self.filter_edit = func_list.parent().findChildren(QtWidgets.QLineEdit)[0]
        #self.filter_edit = [x for x in func_list.children() if x.__class__ is QtWidgets.QLineEdit][0]
        ui.Util.EventFilterManager.InstallOnObject(self.filter_edit, self.lineEditFilter)
        #ui.Util.InstallEventFilterOnObject(ui._app(), self.eventFilter)
        #ui.Util.InstallEventFilterOnObject(view_widget, self.eventFilter)
        ui.Util.EventFilterManager.InstallOnObject(view_widget, self.eventFilter)

        # Add our new QTableView to the function widget.
        func_list.parent().layout().addWidget(self.widget)

        # Setup our proxy model
        orig_model = self.old_widget.model()
        sorter = MyModel()
        self.widget.activated.connect(sorter.onActivated)
        sorter.setSourceModel(orig_model)

        # Configure our new QTableView
        self.widget.setModel(sorter)
        self.widget.setFont(self.old_widget.font())
        font_object = self.old_widget.font()

        self.widget.setShowGrid(False)
        self.widget.setSortingEnabled(True)
        self.widget.verticalHeader().setVisible(False)
        self.widget.horizontalHeader().setStretchLastSection(True)

        # Get the active font, and apply it to this widget.
        fm = QtGui.QFontMetrics(self.old_widget.font())
        self.widget.verticalHeader().setDefaultSectionSize(fm.height())

        # Sort the contents initially
        self.widget.sortByColumn(0, Qt.AscendingOrder)

        # Hide the original view
        self.old_widget.hide()

        # Show our view :D
        self.widget.show()

        # Recenter view on active function
        from . import Util
        current_function = Util.CurrentFunction()
        if current_function:
            func_name = current_function.symbol.full_name
            index_list = sorter.match(sorter.index(0,0), Qt.DisplayRole, func_name, -1, QtCore.Qt.MatchExactly)
            if len(index_list) != 0:
                self.widget.scrollTo(index_list[0], QtWidgets.QAbstractItemView.PositionAtCenter)
                print sorter.itemData(index_list[0])

        refs.append(self.widget)

        return True

