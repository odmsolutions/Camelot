
from customdelegate import *
from camelot.core.constants import *
from camelot.core.utils import *

class IntegerDelegate(CustomDelegate):
  """Custom delegate for integer values"""

  __metaclass__ = DocumentationMetaclass
  
  editor = editors.IntegerEditor

  def __init__(self,
               minimum=camelot_minint,
               maximum=camelot_maxint,
               editable=True,
               parent=None,
               unicode_format = None,
               **kwargs):

    CustomDelegate.__init__(self, parent=parent, editable=editable, minimum=minimum, maximum=maximum, **kwargs)
    self.minimum = minimum
    self.maximum = maximum
    self.editable = editable
    self.unicode_format = unicode_format
    
  def paint(self, painter, option, index):
    painter.save()
    self.drawBackground(painter, option, index)
    value = variant_to_pyobject(index.model().data(index, Qt.EditRole))
    editor = editors.IntegerEditor( None, 
                                    self.minimum,
                                    self.maximum,
                                    self.editable )
    
    
    
    rect = option.rect
    rect = QtCore.QRect(rect.left()+3, rect.top()+6, 16, 16)
    #fontColor = QtGui.QColor()
    
    if( option.state & QtGui.QStyle.State_Selected ):
        painter.fillRect(option.rect, option.palette.highlight())
        fontColor = QtGui.QColor()
        if self.editable:
          Color = option.palette.highlightedText().color()
          fontColor.setRgb(Color.red(), Color.green(), Color.blue())
        else:
          fontColor.setRgb(130,130,130)
    else:
        if self.editable:
          fontColor = QtGui.QColor()
          fontColor.setRgb(0,0,0)
        else:
          painter.fillRect(option.rect, option.palette.window())
          fontColor = QtGui.QColor()
          fontColor.setRgb(130,130,130)
    

    value_str = str(value or '')
    if self.unicode_format != None:
        value_str = self.unicode_format(value)

    #fontColor = fontColor.darker()
    


    painter.setPen(fontColor.toRgb())
    rect = QtCore.QRect(option.rect.left()+23,
                        option.rect.top(),
                        option.rect.width()-23,
                        option.rect.height())
    painter.drawText(rect.x()+2,
                     rect.y(),
                     rect.width()-4,
                     rect.height(),
                     Qt.AlignVCenter | Qt.AlignRight,
                     value_str)
    painter.restore()

  def setEditorData(self, editor, index):
    value = index.model().data(index, Qt.EditRole).toInt()[0]
    editor.set_value(value)