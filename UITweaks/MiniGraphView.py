
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import Qt

from . import Util

import BinjaUI as ui

refs = []

class MiniGraphWidget(QtWidgets.QFrame):

    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.graph = None
        #self.setGeometry(0, 0, graph.width, graph.height)
        self.prevFunction = None

        self.trueBranchColor = QtGui.QColor(0xA2D9AF).darker()
        self.falseBranchColor = QtGui.QColor(0xDE8F97).darker()
        self.otherBranchColor = QtGui.QColor(0x80C6E9).darker()

    """
        Background: 0x2A2A2A
        Foreground: 0x4A4A4A
        Border    : 0x686868
    """
    def paintEvent(self, evt):

        curFun = Util.CurrentFunction()
        if not curFun:
            return

        if curFun != self.prevFunction:
            self.graph = curFun.create_graph()
            self.graph.layout_and_wait()
            self.prevFunction = curFun

        if not self.graph:
            return

        painter = QtGui.QPainter()
        painter.begin(self)
        painter.setPen(Qt.black)
        painter.fillRect(self.rect(), QtGui.QColor(0x2A2A2A))

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
            #painter.drawRect(node.x, node.y, node.width, node.height)

        painter.end()


class Plugin:

    def __init__(self):
        self.name = "mini-function-graph"
        self.ignore = False

    """
        EventFilter to install
    """
    def eventFilter(self, obj, evt):

        if self.ignore:
            return False

        if (self.widget == obj) and (evt.type() == QtCore.QEvent.Paint):
            self.ignore = True
            ui._app().notify(obj, evt)
            self.ignore = False
            return True

        return False

    """
        Install the UI plugin
    """
    def install(self, view_widget):

        widgets = view_widget.findChildren(QtWidgets.QTabWidget)
        tw = [x for x in widgets if x.__class__ is QtWidgets.QTabWidget][0]

        widget = MiniGraphWidget(tw)
        tw.addTab(widget, "Graph")

        self.widget = widget

        # For some reason, Python is losing my reference to the widget,
        # so it gets GC'd. Hold a ref to it so you don't lose the widget
        refs.append(self.widget)

        ui.Util.InstallEventFilterOnObject(ui._app(), self.eventFilter)

        widget.show()

        return True

