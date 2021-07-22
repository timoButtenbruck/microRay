# -*- encoding: utf-8 -*-

import time

from PyQt4 import QtGui, QtCore

from core.command import Command
from core.engineeringNotation.engineeringNotation import EngNumber

from baseCommand import BaseCommand
from gui.graphicItems.floatValidator import FloatValidator
from gui.graphicItems.lineEditDoubleClickSpecial import LineEditDoubleClickSpecial
from gui.graphicItems.listWidgetSpecial import ListWidgetSpecial
from gui.graphicItems.button import SymbolButton
from gui.graphicItems.commandWidgets.smallGenericCommandSettingsWindow import SmallGenericCommandSettingsWindow


from gui.constants import *


class SmallGenericCommand(BaseCommand):
    def __init__(self, command):
        super(SmallGenericCommand, self).__init__(command)

        self.command.inputMethodChanged.connect(self.actualizeInputMethod)

        self.width = 370
        self.height = 70

        self.hValueSpace = 100
        self.vValueSpace = 25


        self.labelAreaHeight = 30
        self.editAreaHeight = self.height - self.labelAreaHeight

        self.editAreaHCenter = self.labelAreaHeight + 0.5 * self.editAreaHeight

        self.separatingLinePath = QtGui.QPainterPath()
        self.separatingLinePath.moveTo(1, self.labelAreaHeight)
        self.separatingLinePath.lineTo(self.width - 2, self.labelAreaHeight)


        self.commandNameFont = QtGui.QFont("sans-serif", 12, QtGui.QFont.Bold)
        self.otherFont = QtGui.QFont("sans-serif", 12)
        self.redFont = QtGui.QFont("sans-serif", 12)

        self.blackPen = QtGui.QPen(QtCore.Qt.black)


        self.valueLineEdit = self._layoutLineEdit(LineEditDoubleClickSpecial())


        self.historyListWidget = ListWidgetSpecial()
        listWidgetProxy = QtGui.QGraphicsProxyWidget()
        listWidgetProxy.setWidget(self.historyListWidget)
        self.historyListWidget.closeMe.connect(self.closeHistory)
        self.historyListWidget.valueSelected.connect(self.setFromHistory)
        self.historyListWidget.hide()

        self.pendingButton = SymbolButton(SymbolButton.TEXT, parent=self)
        self.pendingButton.setPos(55, self.editAreaHCenter - 0.5 * self.pendingButton.boundingRect().height())
        self.pendingButton.clicked.connect(self.togglePendingMode)
        if self.command.getPendingSendMode() is True:
            self.pendingButton.symbol.setColor(QtCore.Qt.red)
        else:
            self.pendingButton.symbol.setColor(QtCore.Qt.darkGray)
        self.pendingButton.drawBorder = False
        self.pendingButton.symbol.setText(u"P")



        self.toggleButton = SymbolButton(SymbolButton.TEXT, parent=self)
        self.toggleButton.setPos(85, self.editAreaHCenter - 0.5 * self.pendingButton.boundingRect().height())
        self.toggleButton.clicked.connect(self.switchToMaxAndThenToMin)
        self.toggleButton.symbol.setText(u"T")
        self.toggleButton.hide()
        # self.toggleButton.drawBorder = False

        borderPen = QtGui.QPen()
        borderPen.setColor(QtGui.QColor(0, 0, 0))
        borderPen.setCosmetic(True)
        borderPen.setWidth(1)
        self.toggleButton.borderPen = borderPen



        self.switchButton = SymbolButton(SymbolButton.TEXT, parent=self)
        self.switchButton.setPos(85, self.editAreaHCenter - 0.5 * self.switchButton.boundingRect().height())
        self.switchButton.clicked.connect(self.toggleMaxAndMin)
        self.switchButton.hide()
        # self.switchButton.drawBorder = False
        self.switchButton.borderPen = borderPen


        self.switchBoxState = False
        self.switchButton.symbol.setText(u"1")
        if self.command.valueOfLastResponse > 0.5:
            self.switchBoxState = True
            self.switchButton.symbol.setText(u"0")


        # horizonal Slider implementierung
        self.horizontalSlider = QtGui.QSlider()
        self.horizontalSliderProxy = QtGui.QGraphicsProxyWidget(self)
        self.horizontalSliderProxy.setWidget(self.horizontalSlider)

        self.horizontalSlider.setGeometry(QtCore.QRect(85, self.editAreaHCenter - 0.5 * self.switchButton.boundingRect().height(), 110, 28))
        self.horizontalSlider.setOrientation(QtCore.Qt.Horizontal)
        self.horizontalSlider.setMinimum(0)
        self.horizontalSlider.setMaximum(100)
        self.horizontalSlider.sliderReleased.connect(self.updateSlider)
        self.sliderLowerLimit = 0
        self.sliderUpperLimit = 100
        self.horizontalSlider.hide()


        # the order of initializing the proxies affects the tab order

        self.valueLineEditProxy = QtGui.QGraphicsProxyWidget(self)
        self.valueLineEditProxy.setWidget(self.valueLineEdit)


        self.commandNameLabelRect = QtCore.QRectF(10, 0, self.width - 50, self.labelAreaHeight)
        self.inputLabelRect = QtCore.QRectF(10, self.labelAreaHeight, 50, self.editAreaHeight)
        self.pendingLabelRect = QtCore.QRectF(55, self.labelAreaHeight, 10, self.editAreaHeight)
        self.returnLabelRect = QtCore.QRectF(205, self.labelAreaHeight, 50, self.editAreaHeight)
        self.returnValueRect = QtCore.QRectF(self.width - 10 - self.hValueSpace,
                                             self.editAreaHCenter - 0.5 * self.vValueSpace,
                                             self.hValueSpace,
                                             self.vValueSpace)


        self.valueLineEdit.move(85, self.editAreaHCenter - 0.5 * self.valueLineEdit.height())
        self.valueLineEditValidator = FloatValidator()
        self.valueLineEdit.setValidator(self.valueLineEditValidator)
        # self.valueLineEdit.setText(str(self.command.getValue()))
        self.valueLineEdit.editingFinished.connect(self.valueEditingFinished)
        self.valueLineEdit.returnPressed.connect(self.valueEditingReturnPressed)
        self.valueLineEdit.downArrowPressed.connect(self.showHistory)
        self.valueLineEdit.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.valueLineEdit.doubleClick.connect(self.showHistory)



        self.userInputWarningStyleSheet = """.LineEditDoubleClickSpecial {
                                             background-color: orange;
                                             border: 1px solid black; }"""

        self.normalStyleSheet = """.LineEditDoubleClickSpecial {
                                   background-color: white;
                                   border: 1px solid black; }"""

        self.valuePendingStyleSheet = """.LineEditDoubleClickSpecial {
                                         border: 3px solid red; }"""


        self.valueLineEdit.setStyleSheet(self.normalStyleSheet)
        self.valueLineEdit.hide()


        self.settingsButton = SymbolButton(SymbolButton.SETTINGS, self)
        self.settingsButton.setPos(self.width - self.settingsButton.boundingRect().width() - 5, 2)
        self.settingsButton.drawBorder = False
        self.settingsButton.clicked.connect(self.showSettingsWindow)

        self.settingsWindow = SmallGenericCommandSettingsWindow()
        self.settingsWindow.lineEditMin.setValidator(FloatValidator())
        self.settingsWindow.lineEditMax.setValidator(FloatValidator())



        self.onePixelGrayPen = QtGui.QPen()
        self.onePixelGrayPen.setWidth(1)
        # self.onePixelGrayPen.setCosmetic(True)
        self.onePixelGrayPen.setColor(QtGui.QColor(50, 50, 50))

        self.onePixelLightGrayPen = QtGui.QPen()
        self.onePixelLightGrayPen.setWidth(1)
        self.onePixelLightGrayPen.setCosmetic(True)
        self.onePixelLightGrayPen.setColor(QtGui.QColor(200, 200, 200))
        # self.onePixelLightGrayPen.setColor(QtCore.Qt.black)

        self.pendingValuePen = QtGui.QPen()
        self.pendingValuePen.setColor(PENDING_VALUE_COLOR)
        self.pendingValuePenGray = QtGui.QPen()
        self.pendingValuePenGray.setColor(QtCore.Qt.darkGray)

        self.boundingRectPath = QtGui.QPainterPath()
        self.boundingRectPath.addRect(0, 0, 200, self.height)

        self.headerAreaPath = QtGui.QPainterPath()
        self.headerAreaPath.addRect(0, 0, self.width, self.labelAreaHeight)
        self.headerAreaBrush = QtGui.QBrush(QtGui.QColor(0, 153, 153, 50))

        self.editAreaPath = QtGui.QPainterPath()
        self.editAreaPath.addRect(0, self.labelAreaHeight, self.width, self.editAreaHeight)
        self.editAreaBrush = QtGui.QBrush(QtGui.QColor(0, 153, 250, 30))

        self.outerPath = QtGui.QPainterPath()
        self.outerPath.moveTo(0, 0)
        self.outerPath.lineTo(self.width, 0)
        self.outerPath.lineTo(self.width, self.height)
        self.outerPath.lineTo(0, self.height)
        self.outerPath.closeSubpath()

        self.returnValueRectPath = QtGui.QPainterPath()
        self.returnValueRectPath.addRect(self.returnValueRect)

        self.littleTimer = QtCore.QTimer()
        self.littleTimer.setSingleShot(True)
        self.littleTimer.timeout.connect(self.switchToMin)

        self.actualizeInputMethod()


    def showHistory(self):
        # print self.command.history

        self.historyListWidget.clear()
        for aValueString in self.command.history:
            self.historyListWidget.addItem(str(aValueString))
        self.historyListWidget.show()
        self.historyListWidget.move(self.valueLineEdit.pos().x() + 0, self.valueLineEdit.pos().y() + self.valueLineEdit.height())
        self.historyListWidget.setFocus(QtCore.Qt.PopupFocusReason)
        self.historyListWidget.setCurrentRow(0)

    def closeHistory(self):
        self.historyListWidget.hide()

    def setFromHistory(self, value):
        self.command.setValue(value)
        self.historyListWidget.hide()

    def _layoutLineEdit(self, lineEdit):

        lineEdit.setFixedSize(self.hValueSpace, self.vValueSpace)
        p = QtGui.QPalette()
        p.setBrush(QtGui.QPalette.Window, QtGui.QBrush(QtGui.QColor(0,0,0,0)))
        # label.setStyleSheet("""border: none; background-color: rgba(0, 0, 0, 0);""")     #; margin-top: 8px """)
        lineEdit.setPalette(p)
        # lineEdit.move(self.width - 10 - self.valueLineEdit.width(), self.labelAreaHeight + 0.5 * self.editAreaHeight - 0.5 * self.valueLineEdit.height())
        # lineEdit.setText("0.0")
        # lineEdit.setMaxLength(6)
        lineEdit.setFont(QtGui.QFont("sans-serif", 12))
        return lineEdit

    def switchToOneAndThenToZero(self):
        self.command.setValue(1.0)
        self.toggleButton.symbol.setText(u"0")
        self.littleTimer.start(100)

    def switchToZero(self):
        self.command.setValue(0.0)
        self.toggleButton.symbol.setText(u"T")

    def toggleOneAndZero(self):
        if self.switchBoxState is False:
            self.command.setValue(1.0)
            self.switchButton.symbol.setText(u"0")
        else:
            self.command.setValue(0.0)
            self.switchButton.symbol.setText(u"1")
        self.switchBoxState = not self.switchBoxState

    def switchToMaxAndThenToMin(self):
        self.command.setValue(self.command.getUpperLimit())
        self.toggleButton.symbol.setText(u"0")
        self.littleTimer.start(100)

    def switchToMin(self):
        self.command.setValue(self.command.getLowerLimit())
        self.toggleButton.symbol.setText(u"T")

    def toggleMaxAndMin(self):
        if self.switchBoxState is False:
            self.command.setValue(self.command.getUpperLimit())
            self.switchButton.symbol.setText(u"0")
        else:
            self.command.setValue(self.command.getLowerLimit())
            self.switchButton.symbol.setText(u"1")
        self.switchBoxState = not self.switchBoxState


    def showSettingsWindow(self):
        self.settingsWindow.lineEditDisplayName.setText(self.command.displayName)
        self.settingsWindow.lineEditMin.setText(str(self.command.getLowerLimit()))
        self.settingsWindow.lineEditMax.setText(str(self.command.getUpperLimit()))

        if self.command.getInputMethod() == Command.VALUE_INPUT:
            self.settingsWindow.radioButtonValueMode.setChecked(True)
        elif self.command.getInputMethod() == Command.TOGGLE_INPUT:
            self.settingsWindow.radioButtonToggleMode.setChecked(True)
        elif self.command.getInputMethod() == Command.SWITCH_INPUT:
            self.settingsWindow.radioButtonSwitchMode.setChecked(True)
        elif self.command.getInputMethod() == Command.SLIDER_INPUT:
            self.settingsWindow.radioButtonSliderMode.setChecked(True)

        self.settingsWindow.checkBoxPendingMode.setChecked(self.command.getPendingSendMode())

        if self.settingsWindow.exec_() == QtGui.QDialog.Accepted:
            self.setSettingsFromSettingsWindow()
        else:
            pass

    def setSettingsFromSettingsWindow(self):


        self.valueLineEdit.hide()
        self.toggleButton.hide()
        self.switchButton.hide()
        self.horizontalSlider.hide()

        self.command.displayName = unicode(self.settingsWindow.lineEditDisplayName.text())
        self.command.setPendingSendMode(self.settingsWindow.checkBoxPendingMode.isChecked())

        minText = self.settingsWindow.lineEditMin.text()
        self.setMinimum(minText)

        maxText = self.settingsWindow.lineEditMax.text()
        self.setMaximum(maxText)

        if self.settingsWindow.radioButtonValueMode.isChecked() is True:
            self.valueLineEdit.show()
            self.command.setInputMethod(Command.VALUE_INPUT)
        if self.settingsWindow.radioButtonSwitchMode.isChecked() is True:
            self.switchButton.show()
            self.command.setInputMethod(Command.SWITCH_INPUT)
        if self.settingsWindow.radioButtonToggleMode.isChecked() is True:
            self.toggleButton.show()
            self.command.setInputMethod(Command.TOGGLE_INPUT)
        if self.settingsWindow.radioButtonSliderMode.isChecked() is True:
            self.horizontalSlider.show()
            self.command.setInputMethod(Command.SLIDER_INPUT)
            self.updateSliderRange()



        self.update()

    def updateSliderRange(self):

        low = self.command.getLowerLimit()
        high = self.command.getUpperLimit()

        self.horizontalSlider.setMinimum(low)
        self.horizontalSlider.setMaximum(high)
        self.horizontalSlider.setValue(low)
        self.command.setValue(self.horizontalSlider.value())
        # if low < 0 and high > 0:
        #     self.sliderLowerLimit = -50
        #     self.sliderUpperLimit = 50
        # elif low == 0 and high > 0:
        #     self.sliderLowerLimit = 0
        #     self.sliderUpperLimit = 100
        # elif low < 0 and high == 0:
        #     self.sliderLowerLimit = -100
        #     self.sliderUpperLimit = 0
        # elif low < 0 and high < 0:
        #     self.sliderLowerLimit = -101
        #     self.sliderUpperLimit = -1
        # elif low > 0 and high > 0:
        #     self.sliderLowerLimit = 1
        #     self.sliderUpperLimit = 101

        # self.horizontalSlider.setMinimum(self.sliderLowerLimit)
        # self.horizontalSlider.setMaximum(self.sliderUpperLimit)
        self.update()

    def updateSlider(self):
        # lowerLimit = self.command.getLowerLimit()
        # upperLimit = self.command.getUpperLimit()
        # limitDif = upperLimit - lowerLimit
        #
        # sliderDif = self.sliderUpperLimit - self.sliderLowerLimit
        #
        # self.horizontalSlider.setTickInterval(100)
        # self.command.setValue(self.horizontalSlider.value() * limitDif / sliderDif)
        self.command.setValue(self.horizontalSlider.value())

    def actualizeInputMethod(self):
        self.valueLineEdit.hide()
        self.switchButton.hide()
        self.toggleButton.hide()
        self.horizontalSlider.hide()

        if self.command.getInputMethod() == Command.VALUE_INPUT:
            self.valueLineEdit.show()
        if self.command.getInputMethod() == Command.SWITCH_INPUT:
            self.switchButton.show()
        if self.command.getInputMethod() == Command.TOGGLE_INPUT:
            self.toggleButton.show()
        if self.command.getInputMethod() == Command.SLIDER_INPUT:
            self.horizontalSlider.show()


    # TODO move to settings window
    def setMinimum(self, text):
        if text == "":
            min = 0
        else:
            min = float(text)
        if min > self.command.getUpperLimit():
            self.command.setLowerLimit(self.command.getUpperLimit(), self)
        else:
            self.command.setLowerLimit(min, self)

    def setMaximum(self, text):
        if text == "":
            max = 0
        else:
            max = float(text)

        if max < self.command.getLowerLimit():
            self.command.setUpperLimit(self.command.getLowerLimit(), self)
        else:
            self.command.setUpperLimit(max, self)

    def valueEditingFinished(self):
        if self.command.getPendingValue() is None and self.valueLineEdit.hasFocus() is False:
            self.valueLineEdit.clear()
            self.valueLineEdit.setStyleSheet(self.normalStyleSheet)


    def valueEditingReturnPressed(self):
        text = self.valueLineEdit.text()
        # print "command given", text

        self.command.clearPendingValue()

        # if nothing is in the textBox, the lower limit of the command will be set to the text box but not send
        if len(text) is 0:
            # self.valueLineEdit.setText(str(self.command.getLowerLimit()))
            # self.valueLineEdit.setCursorPosition(len(self.valueLineEdit.text()))
            # self.valueLineEdit.selectAll()
            self.activateUserInputWarning()
        else:
            # allowed for the decimal point are a comma and a dot
            text = text.replace(",", ".")

            number = float(text)
            if number < self.command.getLowerLimit():
                self.valueLineEdit.setText(str(self.command.getLowerLimit()))
                self.valueLineEdit.setCursorPosition(len(self.valueLineEdit.text()))
                # self.valueLineEdit.selectAll()
                self.activateUserInputWarning()
            elif number > self.command.getUpperLimit():
                self.valueLineEdit.setText(str(self.command.getUpperLimit()))
                self.valueLineEdit.setCursorPosition(len(self.valueLineEdit.text()))
                # self.valueLineEdit.selectAll()
                self.activateUserInputWarning()
            else:
                self.command.setValue(number, self)
                self.clearUserInputWarning()
                self.valueLineEdit.clear()
                if self.command.getPendingSendMode() is True:
                    self.valueLineEdit.setStyleSheet(self.valuePendingStyleSheet)
                    self.valueLineEdit.setText(str(self.command.getPendingValue()))


        # TODO how to set color back to black
        # if self.command.getPendingSendMode() is True:
        #     self.valueLineEdit.setStyleSheet(""".LineEditDoubleClickSpecial { color: red; }""")



        # self.valueLineEdit.setText(str(self.command.getValue()))
        # self.valueLineEdit.setCursorPosition(0)
        # self.valueLineEdit.selectAll()


    def valueChangedPerWidget(self, widgetInstance):
        pass

    def minChangedPerWidget(self, widgetInstance):
        pass

    def maxChangedPerWidget(self, widgetInstance):
        pass

    def togglePendingMode(self):
        if self.command.getPendingSendMode() is True:
            self.command.setPendingSendMode(False)
        else:
            self.command.setPendingSendMode(True)

    @QtCore.pyqtSlot()
    def pendingModeChanged(self, command=None):
        super(SmallGenericCommand, self).pendingModeChanged(command)
        if self.command.getPendingSendMode() is False:
            self.valueLineEdit.setStyleSheet(self.normalStyleSheet)
            self.valueLineEdit.clear()
            self.pendingButton.symbol.setColor(QtCore.Qt.darkGray)
        else:
            self.pendingButton.symbol.setColor(QtCore.Qt.red)

    @QtCore.pyqtSlot()
    def pendingValueCanceled(self, command=None):
        super(SmallGenericCommand, self).pendingValueCanceled(command)
        self.valueLineEdit.clear()
        self.valueLineEdit.setStyleSheet(self.normalStyleSheet)

    def sameValueReceived(self):
        super(SmallGenericCommand, self).sameValueReceived()
        # self.returnValueDisplay.setStyleSheet(
        #     """.LineEditDoubleClickSpecial { background-color: lightgray;
        #                                      border-style: solid;
        #                                      border-color: black; }""")
        self.update()

    # overwrites method of super class
    def differentValueReceived(self):
        # this call is needed to start the blink timer
        super(SmallGenericCommand, self).differentValueReceived()

        # self.returnValueDisplay.setStyleSheet(
        #     """.LineEditDoubleClickSpecial { background-color: red;
        #                                      border-style: solid;
        #                                      border-color: black; }""")



        # self.valueLineEdit.setText(str(self.command.getValue()))
        # self.valueLineEdit.setCursorPosition(0)

    def activateUserInputWarning(self):
        super(SmallGenericCommand, self).activateUserInputWarning()
        self.valueLineEdit.setStyleSheet(self.userInputWarningStyleSheet)

    def clearUserInputWarning(self):
        super(SmallGenericCommand, self).clearUserInputWarning()
        self.valueLineEdit.setStyleSheet(self.normalStyleSheet)

    def paint(self, QPainter, QStyleOptionGraphicsItem, QWidget_widget=None):
        QPainter.setRenderHint(QtGui.QPainter.Antialiasing, True)

        # draw background of the label
        QPainter.fillPath(self.headerAreaPath, self.headerAreaBrush)

        # draw background of edit area
        QPainter.fillPath(self.editAreaPath, self.editAreaBrush)


        # # draw a warning
        # if self.showUserInputWarning is True:
        #     QPainter.fillPath(self.editAreaPath, self.userInputWarningBrush)

        # # draw a warning
        # if self.showCommFailureWarning is True:
        #     QPainter.fillPath(self.editAreaPath, self.commFailureWarningBrush)

        # draw background of return value
        QPainter.fillPath(self.returnValueRectPath, QtGui.QBrush(QtGui.QColor(200, 200, 200)))

        # draw a warning
        if self.showDifferentValueReceivedWarning is True:
            QPainter.fillRect(self.returnValueRect, self.differentValueReceivedWarningBrush)


        # draw return value
        QPainter.setFont(self.otherFont)
        # engNumber = EngNumber(self.command.valueOfLastResponse)
        # numberToShow = "".format(engNumber.__repr__())
        # if isinstance(self.command.valueOfLastResponse, float):
        #     numberToShow = u"{:0.2E}".format(self.command.valueOfLastResponse)
        # if isinstance(self.command.valueOfLastResponse, int):
        #     numberToShow = u"{}".format(self.command.valueOfLastResponse)
        QPainter.drawText(self.returnValueRect,
                         QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter,
                         QtCore.QString(str(self.command.getValue())))
                         # QtCore.QString(str(self.command.valueOfLastResponse)))
                         # QtCore.QString(u"{:0.2e}".format(self.command.valueOfLastResponse)))
                         # QtCore.QString(numberToShow))

        QPainter.setPen(self.blackPen)

        # draw the command name
        QPainter.setFont(self.commandNameFont)
        if len(self.command.displayName) > 0:
            QPainter.drawText(self.commandNameLabelRect,
                             QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter,
                             QtCore.QString(self.command.displayName))
        else:
            QPainter.drawText(self.commandNameLabelRect,
                             QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter,
                             QtCore.QString(self.command.name))

        # draw input label
        QPainter.setFont(self.otherFont)
        QPainter.drawText(self.inputLabelRect,
                         QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter,
                         QtCore.QString(u"Input"))

        # draw return value label
        QPainter.setFont(self.otherFont)
        QPainter.drawText(self.returnLabelRect,
                         QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter,
                         QtCore.QString(u"aktuell"))

        # draw bounding paths
        QPainter.setPen(self.onePixelGrayPen)
        # QPainter.drawPath(self.headerAreaPath)
        # QPainter.drawPath(self.editAreaPath)
        QPainter.drawPath(self.outerPath)

        # draw a line to separate edit area and header area
        QPainter.setRenderHint(QtGui.QPainter.Antialiasing, False)
        QPainter.setPen(self.onePixelLightGrayPen)
        QPainter.drawPath(self.separatingLinePath)

    def boundingRect(self):
        return QtCore.QRectF(0, 0, self.width, self.height)



