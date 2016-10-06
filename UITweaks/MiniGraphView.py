
import sys

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import Qt

from . import Util

import BinjaUI as ui

refs = []

class MiniGraphWidget(QtWidgets.QFrame):

    def __init__(self, view, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.graph = None
        #self.setGeometry(0, 0, graph.width, graph.height)
        self.prevFunction = None
        self.view = view

        self.trueBranchColor = QtGui.QColor(0xA2D9AF).darker()
        self.falseBranchColor = QtGui.QColor(0xDE8F97).darker()
        self.otherBranchColor = QtGui.QColor(0x80C6E9).darker()

        self.verticalPadding = 0
        self.horizontalPadding = 0

    def paintEvent(self, evt):

        if not self.pixmap:
            updateRendering()

        painter = QtGui.QPainter()
        painter.begin(self)

        # Draw the cached rendering of the graph
        painter.drawPixmap(self.rect(), self.pixmap)


        # TODO: Don't duplicate this code....
        # We need to scale off of the font... because reasons...
        font_object = ui.Util.GetFont()
        fm = QtGui.QFontMetrics(font_object)
        fw = fm.width('W')
        fh = fm.height()

        # Scale in two phases:
        #   1. Scale to fit on the x-axis
        #   2. Scale to fit on the y-axis if we need to

        aspect_ratio = float(fh) / fw

        x_scale = self.size().width() / float(self.graph.width)
        y_scale = x_scale * aspect_ratio

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

        painter.translate(x_off, y_off)

        # Actually draw the bounding box on the preview
        # Figure out what part of the view we're looking at and draw it on the panel

        x_ticks = float(self.view.horizontalScrollBar().maximum())
        y_ticks = float(self.view.verticalScrollBar().maximum())

        x_tick = float(self.view.horizontalScrollBar().value())
        y_tick = float(self.view.verticalScrollBar().value())

        paint_width = float(self.width() - (x_off * 2))
        paint_height = float(self.height() - (y_off * 2))

        real_view_width = self.view.viewport().width() + x_ticks
        real_view_height = self.view.viewport().height() + y_ticks


        if x_ticks:
            _x = (paint_width - (self.view.viewport().width()/real_view_width)*paint_width) * (x_tick/x_ticks)
            _width = (self.view.viewport().width()/real_view_width)*paint_width
        else:
            _x = 0
            _width = paint_width

        if y_ticks:
            _y = (paint_height - (self.view.viewport().height()/real_view_height)*paint_height) * (y_tick/y_ticks)
            _height = (self.view.viewport().height()/real_view_height)*paint_height
        else:
            _y = 0
            _height = paint_height

        painter.setPen(Qt.magenta)
        painter.drawRect(_x, _y, _width, _height)

        #painter.drawPoint(_x, _y)

        painter.end()

    def updateRendering(self):

        curFun = Util.CurrentFunction()
        if not curFun:
            return

        if (not self.prevFunction) or (curFun.start != self.prevFunction.start):
            self.graph = curFun.create_graph()
            self.graph.layout_and_wait()
            self.prevFunction = curFun

        if not self.graph:
            return

        self.pixmap = QtGui.QPixmap(self.width(), self.height())

        painter = QtGui.QPainter()
        painter.begin(self.pixmap)
        painter.setPen(Qt.black)

        painter.fillRect(self.rect(), QtGui.QColor(Qt.black))

        # We need to scale off of the font... because reasons...
        font_object = ui.Util.GetFont()
        fm = QtGui.QFontMetrics(font_object)
        fw = fm.width('W')
        fh = fm.height()

        # Scale in two phases:
        #   1. Scale to fit on the x-axis
        #   2. Scale to fit on the y-axis if we need to

        aspect_ratio = float(fh) / fw

        x_scale = self.size().width() / float(self.graph.width)
        y_scale = x_scale * aspect_ratio

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

        self.horizontalPadding = x_off
        self.verticalPadding = y_off

        # Translate and scale
        painter.translate(x_off, y_off)
        painter.scale(x_scale, y_scale)
        painter.scale(ratio, ratio)

        painter.fillRect(QtCore.QRect(0, 0, self.graph.width, self.graph.height), QtGui.QColor(0x2A2A2A))

        for node in self.graph:

            for edge in node.outgoing_edges:
                pen = QtGui.QPen()
                pen.setWidth(1)
                pen.setCosmetic(True)

                if edge.type == 'TrueBranch':
                    pen.setColor(self.trueBranchColor)
                elif edge.type == 'FalseBranch':
                    pen.setColor(self.falseBranchColor)
                else:
                    pen.setColor(self.otherBranchColor)

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

        painter.resetTransform()
        painter.translate(x_off, y_off)

        painter.end()

    def moveSourceViewToPoint(self, globalPoint):
        localPoint = self.mapFromGlobal(globalPoint)

        _width = self.rect().width() - float(self.horizontalPadding) * 2
        _height = self.rect().height() - float(self.verticalPadding) * 2

        hBar = self.view.horizontalScrollBar()
        vBar = self.view.verticalScrollBar()

        view_rect = self.view.viewport().rect()

        if hBar.isVisible() and hBar.maximum():
            scene_width = hBar.maximum() + view_rect.width()
        else:
            scene_width = view_rect.width()

        if vBar.isVisible() and vBar.maximum():
            scene_height = vBar.maximum() + view_rect.height()
        else:
            scene_height = view_rect.height()

        localPoint.setX(localPoint.x() - self.horizontalPadding)
        localPoint.setY(localPoint.y() - self.verticalPadding)

        if self.view.horizontalScrollBar().isVisible() and self.view.horizontalScrollBar().maximum():
            outline_width = view_rect.width() / float(scene_width) * _width
            slider_width = _width - outline_width/2.0
            localPoint.setX(localPoint.x() - outline_width/2.0)

            self.view.horizontalScrollBar().setValue(
                    (self.view.horizontalScrollBar().maximum() + (view_rect.width()/2)) * (localPoint.x() / slider_width)
                )

        if self.view.verticalScrollBar().isVisible() and self.view.verticalScrollBar().maximum():
            outline_height = view_rect.height() / float(scene_height) * _height
            slider_height = _height - outline_height/2.0
            localPoint.setY(localPoint.y() - outline_height/2.0)

            self.view.verticalScrollBar().setValue(
                    (self.view.verticalScrollBar().maximum() + (view_rect.height()/2)) * (localPoint.y() / slider_height)
                )

class Plugin:
    name = "mini-function-graph"

    def __init__(self):
        self.ignore = False
        self.mousePressed = False

    """
        EventFilter to install
    """
    def eventFilter(self, obj, evt):

        if self.ignore:
            return False

        # TODO: Figure out what is causing this repaint - I don't know
        if (evt.type() == QtCore.QEvent.Paint):
            self.widget.update()

        elif (evt.type() == QtCore.QEvent.LayoutRequest):
            self.widget.updateRendering()

        elif (evt.type() == QtCore.QEvent.MouseButtonPress) or (evt.type() == QtCore.QEvent.MouseButtonDblClick):
            if QtWidgets.QApplication.widgetAt(evt.globalPos()) == self.widget:
                self.widget.moveSourceViewToPoint(evt.globalPos())
                self.mousePressed = True

        elif (evt.type() == QtCore.QEvent.MouseButtonRelease):
            if QtWidgets.QApplication.widgetAt(evt.globalPos()) == self.widget:
                self.mousePressed = False

        elif (evt.type() == QtCore.QEvent.MouseMove) and self.mousePressed:
            if QtWidgets.QApplication.widgetAt(evt.globalPos()) == self.widget:
                self.widget.moveSourceViewToPoint(evt.globalPos())

        return False

    def toggled(self, state):

        print "TOGGLED: {}".format(state)

    """
        Install the UI plugin
    """
    def install(self, view_widget):

        widgets = view_widget.findChildren(QtWidgets.QTabWidget)
        tw = [x for x in widgets if x.__class__ is QtWidgets.QTabWidget][0]

        scroll_areas = view_widget.findChildren(QtWidgets.QAbstractScrollArea)
        dis_view = [x for x in scroll_areas if x.metaObject().className() == 'DisassemblyView'][0]

        widget = MiniGraphWidget(dis_view, tw)
        tw.addTab(widget, "Graph")

        self.widget = widget
        self.widget.__plugin = self

        # For some reason, Python is losing my reference to the widget,
        # so it gets GC'd. Hold a ref to it so you don't lose the widget
        refs.append(self.widget)

        ui.Util.EventFilterManager.InstallOnObject(view_widget, self.eventFilter)

        """
        mainwindow = [x for x in ui._app().allWidgets() if x.__class__ is QtWidgets.QMainWindow][0]
        sb = mainwindow.statusBar()
        for x in sb.children():
            sys.__stdout__.write("{}\n".format(x.metaObject().className()))

        options_menu = [x for x in sb.children() if x.metaObject().className() == 'StatusBarWidget'][0]

        for x in options_menu.children():
            print x.__class__
            if x.__class__ is QtWidgets.QAction and x.isCheckable():
                aw = x.associatedWidgets()
                for x in aw:
                    QtCore.QObject.connect(we, QtCore.SIGNAL('toggled'), self.triggered)
                    #x.triggered.connect(self.triggered)
        """
        widget.show()

        return True

