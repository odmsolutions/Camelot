
from customeditor import *
from camelot.view.art import Icon

class ColoredFloatEditor(CustomEditor):
  """Widget for editing a float field, with a calculator"""
    
  def __init__(self,
               parent,
               precision=2,
               minimum=camelot_minfloat,
               maximum=camelot_maxfloat, 
               editable=True,
               **kwargs):
    CustomEditor.__init__(self, parent)
    action = QtGui.QAction(self)
    action.setShortcut(Qt.Key_F3)
    self.setFocusPolicy(Qt.StrongFocus)
    self.spinBox = QtGui.QDoubleSpinBox(parent)
    self.spinBox.setReadOnly(not editable)
    self.spinBox.setDisabled(not editable)
    self.spinBox.setEnabled(editable)
    self.spinBox.setRange(minimum, maximum)
    self.spinBox.setDecimals(precision)
    self.spinBox.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
    self.spinBox.setSingleStep(1.0)
    self.spinBox.addAction(action)
    self.arrow = QtGui.QLabel()
    self.arrow.setPixmap(Icon('tango/16x16/actions/go-up.png').getQPixmap())

    self.arrow.setAutoFillBackground(False)
    self.arrow.setMaximumWidth(19)

    calculatorButton = QtGui.QToolButton()
    icon = Icon('tango/16x16/apps/accessories-calculator.png').getQIcon()
    calculatorButton.setIcon(icon)
    calculatorButton.setAutoRaise(True)

    self.connect(calculatorButton,
                 QtCore.SIGNAL('clicked()'),
                 lambda:self.popupCalculator(self.spinBox.value()))
    self.connect(action,
                 QtCore.SIGNAL('triggered(bool)'),
                 lambda:self.popupCalculator(self.spinBox.value()))
    self.connect(self.spinBox,
                 QtCore.SIGNAL('editingFinished()'),
                 lambda:self.editingFinished(self.spinBox.value()))

    self.releaseKeyboard()

    layout = QtGui.QHBoxLayout()
    layout.setMargin(0)
    layout.setSpacing(0)
    layout.addSpacing(3.5)
    layout.addWidget(self.arrow)
    layout.addWidget(self.spinBox)
    if editable:
      layout.addWidget(calculatorButton)
    self.setFocusProxy(self.spinBox)
    self.setLayout(layout)

  def set_value(self, value):
    value = CustomEditor.set_value(self, value) or 0.0
    self.spinBox.setValue(value)
    if value >= 0:
      if value == 0:
        self.arrow.setPixmap(Icon('tango/16x16/actions/zero.png').getQPixmap())
      else:
        self.arrow.setPixmap(Icon('tango/16x16/actions/go-up.png').getQPixmap())
    else:
      self.arrow.setPixmap(Icon('tango/16x16/actions/go-down-red.png').getQPixmap())

  def get_value(self):
    self.spinBox.interpretText()
    value = self.spinBox.value()
    return CustomEditor.get_value(self) or value

  def popupCalculator(self, value):
    from camelot.view.controls.calculator import Calculator
    calculator = Calculator(self)
    calculator.setValue(value)
    self.connect(calculator,
                 QtCore.SIGNAL('calculationFinished'),
                 self.calculationFinished)
    calculator.exec_()

  def calculationFinished(self, value):
    self.spinBox.setValue(float(value))
    self.emit(QtCore.SIGNAL('editingFinished()'), value)

  def editingFinished(self, value):
    self.emit(QtCore.SIGNAL('editingFinished()'), value)