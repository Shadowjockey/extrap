"""
This file is part of the Extra-P software (http://www.scalasca.org/software/extra-p)

Copyright (c) 2020,
Technische Universitaet Darmstadt, Germany

This software may be modified and distributed under the terms of
a BSD-style license. See the LICENSE file in the package base
directory for details.
"""
from PySide2.QtCore import QMargins

from PySide2.QtGui import *  # @UnusedWildImport
from PySide2.QtWidgets import *  # @UnusedWildImport
from PySide2.QtCore import *

from gui.Utils import formatNumber


class ColorWidget(QWidget):

    def __init__(self, parent):
        super(ColorWidget, self).__init__()

        self.max_label = QLabel()
        self.min_label = QLabel()
        self.initUI()

    def initUI(self):

        self.setMinimumHeight(40)
        self.setMinimumWidth(200)
        self.setWindowTitle('Colours')
        self.rect_width = 0
        self.rect_height = 0
        self.setContentsMargins(10, 10, 10, 10)

        self.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Fixed)
        grid = QGridLayout(self)
        grid.setContentsMargins(5, 0, 5, 0)
        self.setStyleSheet("QLabel {color : white; }")
        grid.addWidget(self.min_label, 0, 0)
        grid.addWidget(self.max_label, 0, 1, Qt.AlignRight)
        self.setLayout(grid)
        # self.red_component=0
        # self.green_component=0
        # self.blue_component=0
        self.show()

    def paintEvent(self, e):

        paint = QPainter()
        paint.begin(self)
        self.drawColors(paint)
        paint.end()

    def getColor(self, value):
        value = max(0.0, min(value, 1.0))  # prevent out of bounds
        # takes a value between 0 and 1 and returns a QColor
        if value < 0.25:
            # interpolate between blue (0,0,255) and light blue (0,255,255)
            interpolate = value * 4
            return QColor(0, interpolate * 255, 255)
        elif value < 0.5:
            # interpolate between light blue (0,255,255) and green (0,255,0)
            interpolate = (value - 0.25) * 4
            return QColor(0, 255, 255 - interpolate * 255)
        elif value < 0.75:
            # interpolate between green (0,255,0) and yellow (255,255,0)
            interpolate = (value - 0.5) * 4
            return QColor(interpolate * 255, 255, 0)
        else:
            # interpolate between yellow (255,255,0) and red (255,0,0)
            interpolate = (value - 0.75) * 4
            return QColor(255, 255 - interpolate * 255, 0)

    def drawColors(self, paint):

        self.rect_width = self.frameGeometry().width()
        self.rect_height = self.frameGeometry().height()
        (mleft, mtop, mright, mbottom) = self.getContentsMargins()

        for position in range(mleft, self.rect_width - mright):
            ratio = float(position) / self.rect_width
            color = self.getColor(ratio)
            paint.setPen(color)
            paint.setBrush(color)
            paint.drawRect(position, mtop, 1, self.rect_height - mbottom - mtop)

    def update_min_max(self, min_value, max_value):
        self.min_label.setText(formatNumber(str(min_value)))
        self.max_label.setText(formatNumber(str(max_value)))
