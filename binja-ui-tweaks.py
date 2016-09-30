
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt

import BinjaUI as ui
from BinjaUI import Components

import binaryninja as bn

def tweakFunctionList(bv):

    def AddNewView():

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
            Super Hacky EventFilter that gets installed on the QApplication
            so we can catch all KeyEvents that originated on our Table View.
            For some reason, I was unable to get keyPressEvent on the TableView
            to work correctly. I'm guessing it has to do with trying to inject
            a widget from Python into a native widget. No idea.

        """
        class MyEventFilter(QtCore.QObject):

            def __init__(self, view):
                QtCore.QObject.__init__(self, None)
                self.view = view
                self.ignore = False

            def eventFilter(self, obj, evt):
                # We're infinite looping when we notify
                # the target of its event, so disable
                # ourself if we're delivering the event
                if self.ignore:
                    return super(MyEventFilter,self).eventFilter(obj,evt)

                if not (evt.type() == QtCore.QEvent.KeyPress):
                    return False

                if obj == self.view:
                    self.ignore = True
                    ui._app().notify(self.view, evt)
                    self.ignore = False
                    return True

                return super(MyEventFilter,self).eventFilter(obj, evt)

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
                print self.sourceModel().data(index)
                symbols = bv.get_symbols_by_name(self.sourceModel().data(index))

                if len(symbols) == 1:
                    bv.file.navigate(bv.file.view, symbols[0].address)

                elif len(symbols) == 0:
                    print "No symbol with name [[{}]] found".format(self.sourceModel().data(index))

                else:
                    print "Multiple symbols found"

        # Get the function List from BinjaUI
        func_list = ui.Components.FunctionWindow()

        # Find the QListView that contains the original Function Model
        list_view = [x for x in func_list.children() if x.__class__ is QtWidgets.QListView][0]

        # Construct our new QTableView that forwards events on to the original ListView
        view = MyTableView(func_list, list_view)

        # For some reason, our QTableView isn't getting events. Install this EventFilter
        # globally (very hacky) and intercept any events triggered by the new QTableView
        view.evtFilter = MyEventFilter(view)
        ui._app().installEventFilter(view.evtFilter)

        # Add our new QTableView to the function widget.
        func_list.layout().addWidget(view)

        # Setup our proxy model
        orig_model = list_view.model()
        model = MyModel()
        view.activated.connect(model.onActivated)
        model.setSourceModel(orig_model)

        # This proxy model might be redundant, but I was having issues with
        # the headerData not being respected. I'm leaving it for now.
        sorter = QtCore.QSortFilterProxyModel(func_list)
        sorter.setSourceModel(model)
        sorter.setSortCaseSensitivity(Qt.CaseInsensitive)

        # Configure our new QTableView
        view.setModel(sorter)
        view.setFont(list_view.font())
        view.setShowGrid(False)
        view.setSortingEnabled(True)
        view.verticalHeader().setVisible(False)
        view.horizontalHeader().setStretchLastSection(True)

        # Get the active font, and apply it to this widget.
        # TODO: If the font changes, we should update it somehow...
        fm = QtGui.QFontMetrics(list_view.font())
        view.verticalHeader().setDefaultSectionSize(fm.height())

        # Sort the contents initially
        sorter.sort(Qt.DescendingOrder)

        # Hide the original view
        list_view.hide()

        # Show our view :D
        view.show()

        return view

    # Inject our changes into the GUI.
    wi = ui.WidgetInjector(AddNewView)
    wi.inject()


#Util.AddMenuTree( {'Mod Func Win' : setupUI} )
bn.PluginCommand.register("Tweak Function List", "Tweak Function List", tweakFunctionList)
print "binja-ui-tweaks done loading"
