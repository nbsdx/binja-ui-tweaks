
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt

import BinjaUI as ui
from BinjaUI import Components

import binaryninja as bn

refs = []
font_object = None

leakedFunction = None
leakFunctionAction = None

is_initialized = False

def leakCurrentFunction(bv, current_function):
    global leakedFunction
    leakedFunction = current_function

def CurrentFunction():
    global leakedFunction
    global leakFunctionAction

    if leakFunctionAction:
        leakFunctionAction.trigger()

    return leakedFunction

"""
    Makes sure "CurrentFunction" is enabled, and does some cleanup
"""
def Initialize():
    global is_initialized
    global leakFunctionAction

    if is_initialized:
        return

    toolsMenu = ui.Components.Menu("Tools")

    for a in toolsMenu.actions():
        if a.text() == "__leak_function":
            a.setVisible(False)
            leakFunctionAction = a

    menus = [x for x in ui._app().allWidgets() if x.__class__ is QtWidgets.QMenu]


    # TODO: the right-click menus are generated dynamically,
    # need to intercept them and remove our secret actions
    for x in menus:
        if toolsMenu == x:
            continue
        for a in x.actions():
            if a.text() == "__leak_function":
                a.setVisible(False)
                x.removeAction(a)
                break

    is_initialized = True

"""

    Tweak Function Window

"""
def tweakFunctionList(bv, current_function):

    Initialize()

    def AddNewView():
        global font_object

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

            def __init__(self, old_view, view, edit):
                QtCore.QObject.__init__(self, None)
                self.old_view = old_view
                self.view = view
                self.edit = edit
                self.ignore = False
                self.isSearching = False
                self.originalPosition = None

            def eventFilter(self, obj, evt):
                # We're infinite looping when we notify
                # the target of its event, so disable
                # ourself if we're delivering the event
                if self.ignore:
                    return super(MyEventFilter,self).eventFilter(obj,evt)

                # Get the keypresses on the QTableView we make. For some reason
                # we can't see them...
                if (obj == self.view) and (evt.type() == QtCore.QEvent.KeyPress):

                    if not self.isSearching:
                        self.originalPosition = view.verticalScrollBar().sliderPosition()

                    self.isSearching = True
                    self.ignore = True
                    ui._app().notify(self.view, evt)
                    self.ignore = False
                    return True

                # Refocus on the function list when the line edit hides itself
                elif (obj == self.edit) and (evt.type() == QtCore.QEvent.Hide):
                    self.isSearching = False
                    view.setFocus(Qt.ActiveWindowFocusReason)
                    if self.originalPosition:
                        view.verticalScrollBar().setSliderPosition(self.originalPosition)
                        self.originalPosition = None

                    return True

                # Handle Font Changes
                elif (obj == self.old_view) and (evt.type() == QtCore.QEvent.FontChange):
                    global font_object
                    font_object = self.old_view.font()
                    self.view.setFont(self.old_view.font())
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
                symbols = bv.get_symbols_by_name(self.data(index))

                if len(symbols) == 1:
                    bv.file.navigate(bv.file.view, symbols[0].address)

                elif len(symbols) == 0:
                    print "No symbol with name [[{}]] found".format(self.data(index))

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
        view.evtFilter = MyEventFilter(list_view, view, [x for x in func_list.children() if x.__class__ is QtWidgets.QLineEdit][0])
        ui._app().installEventFilter(view.evtFilter)

        # Add our new QTableView to the function widget.
        func_list.layout().addWidget(view)

        # Setup our proxy model
        orig_model = list_view.model()
        sorter = MyModel()
        view.activated.connect(sorter.onActivated)
        sorter.setSourceModel(orig_model)

        # Configure our new QTableView
        view.setModel(sorter)
        view.setFont(list_view.font())
        font_object = list_view.font()

        view.setShowGrid(False)
        view.setSortingEnabled(True)
        view.verticalHeader().setVisible(False)
        view.horizontalHeader().setStretchLastSection(True)

        # Get the active font, and apply it to this widget.
        fm = QtGui.QFontMetrics(list_view.font())
        view.verticalHeader().setDefaultSectionSize(fm.height())

        # Sort the contents initially
        view.sortByColumn(0, Qt.AscendingOrder)

        # Hide the original view
        list_view.hide()

        # Show our view :D
        view.show()

        # Recenter view on active function
        func_name = current_function.symbol.full_name
        index_list = sorter.match(sorter.index(0,0), Qt.DisplayRole, func_name, -1, QtCore.Qt.MatchExactly)
        if len(index_list) != 0:
            view.scrollTo(index_list[0], QtWidgets.QAbstractItemView.PositionAtCenter)
            print sorter.itemData(index_list[0])

        refs.append(view)

        return view

    # Inject our changes into the GUI.
    wi = ui.WidgetInjector(AddNewView)
    wi.inject()


"""

    Add the graph viewer

"""
def addMiniGraphView(bv, current_function):

    Initialize()

    def CreateMiniGraphView():

        class MiniGraphWidgetEventFilter(QtCore.QObject):
            def __init__(self, mgw, parent=None):
                QtCore.QObject.__init__(self, parent)
                self.mgw = mgw
                self.ignore = False

            def eventFilter(self, obj, evt):

                if obj == self:
                    return False

                if self.ignore:
                    return False

                if (obj == self.mgw) and (evt.type() == QtCore.QEvent.Paint):
                    self.ignore = True
                    ui._app().notify(obj, evt)
                    self.ignore = False
                    #return True

                return QtCore.QObject.eventFilter(self, obj, evt)


        class MiniGraphWidget(QtWidgets.QFrame):

            def __init__(self, graph, parent=None):
                QtWidgets.QFrame.__init__(self, parent)
                self.graph = graph
                self.setGeometry(0, 0, graph.width, graph.height)
                self.prevFunction = None

            """
                Background: 0x2A2A2A
                Foreground: 0x4A4A4A
                Border    : 0x686868
            """
            def paintEvent(self, evt):

                curFun = CurrentFunction()
                if curFun != self.prevFunction:
                    self.graph = curFun.create_graph()
                    self.graph.layout_and_wait()
                    self.prevFunction = curFun

                painter = QtGui.QPainter()
                painter.begin(self)
                painter.setPen(Qt.black)
                painter.fillRect(self.rect(), QtGui.QColor(0x2A2A2A))

                # We need to scale off of the font... because reasons...
                # TODO: need a better way to do this. This is gonna be reallllly slow.
                # Since we can't depend on the improved function list to be enabled, we can't
                # get the global font_object
                font_object = [x for x in ui.Components.FunctionWindow().children() if x.__class__ is QtWidgets.QListView][0].font()
                fm = QtGui.QFontMetrics(font_object)
                fw = fm.width('W')
                fh = fm.height()

                # Scale in two phases:
                #   1. Scale to fit on the x-axis
                #   2. Scale to fit on the y-axis if we need to

                aspect_ratio = float(fh) / fw

                x_scale = self.size().width() / float(self.graph.width)
                y_scale = x_scale * aspect_ratio #self.size().height() / float(self.graph.height)

                ratio = 1.0
                if (self.size().height() < (self.graph.height * y_scale)):
                    ratio = float(self.size().height()) / (self.graph.height * y_scale)

                # Adjust so that it's centered
                x_off = 0
                y_off = 0
                if (self.graph.width * x_scale * ratio < self.size().width()):
                    x_off = (self.size().width() - (self.graph.width * x_scale * ratio)) / 2.0

                if (self.graph.height * y_scale * ratio < self.size().height()):
                    y_off = (self.size().height() - (self.graph.height * y_scale * ratio)) / 2.0

                # Translate and scale
                painter.translate(x_off, y_off)
                painter.scale(x_scale, y_scale)
                painter.scale(ratio, ratio)

                for node in self.graph:

                    for edge in node.outgoing_edges:
                        pen = QtGui.QPen()
                        pen.setWidth(1)
                        pen.setCosmetic(True)

                        if edge.type == 'TrueBranch':
                            pen.setColor(QtGui.QColor(0xA2D9AF))
                        elif edge.type == 'FalseBranch':
                            pen.setColor(QtGui.QColor(0xDE8F97))
                        else:
                            pen.setColor(QtGui.QColor(0x80C6E9))

                        painter.setPen(pen)
                        path = QtGui.QPainterPath()
                        path.moveTo(edge.points[0][0], edge.points[0][1])
                        for point in edge.points[1:]:
                            path.lineTo(point[0], point[1])
                        painter.drawPath(path)

                    pen = QtGui.QPen()
                    pen.setWidth(1)
                    pen.setCosmetic(True)
                    pen.setColor(QtGui.QColor(0x909090))
                    painter.setPen(pen)

                    painter.fillRect(node.x, node.y, node.width, node.height, QtGui.QColor(0x4A4A4A))
                    painter.drawRect(node.x, node.y, node.width, node.height)

                painter.resetTransform()

                #print CurrentFunction()

                # Draw the active region on the graph
                #header = [x for x in ui._app().allWidgets() if x.metaObject().className() == 'DisassemblyFunctionHeader']
                #p = header[0].parent()
                #scroll_area = [x for x in p.children() if x.__class__ is QtWidgets.QAbstractScrollArea][0]
                #print "Scroll Area: ({},{})".format(scroll_area.size().width(), scroll_area.size().height())
                #print "Graph  Size: ({},{})".format(self.graph.width, self.graph.height)

                painter.end()


        tw = ui.Components.TabWidget()
        graph = current_function.create_graph()
        graph.layout()
        mgv = MiniGraphWidget(graph, tw)
        tw.addTab(mgv, "Graph")

        mgv.filter = MiniGraphWidgetEventFilter(mgv, mgv)
        ui._app().installEventFilter(mgv.filter)

        mgv.show()

        refs.append(mgv)
        return mgv

    wi = ui.WidgetInjector(CreateMiniGraphView)
    wi.inject()

#Util.AddMenuTree( {'Mod Func Win' : setupUI} )
bn.PluginCommand.register_for_function("Tweak Function List", "Tweak Function List", tweakFunctionList)
bn.PluginCommand.register_for_function("Add Graph Preview", "Add Graph Preview", addMiniGraphView)
bn.PluginCommand.register_for_function("__leak_function", "", leakCurrentFunction)

print "binja-ui-tweaks done loading"
