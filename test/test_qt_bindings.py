"""Test the behaviour of the qt bindings in various circumstances.
"""

import unittest

from PyQt4 import QtGui, QtCore

class ReferenceHoldingBox(QtGui.QGroupBox):
    """A group box holding references to the table
    view and the table model"""

    def __init__(self, model, table):
        QtGui.QGroupBox.__init__(self)
        self.model = model
        self.table = table
                 
class TableView( QtGui.QWidget  ):
    """A widget containg both a table and a groupbox that
    holds a reference to both the table and the model of the
    table"""

    def __init__( self, table_model ):
        super(TableView, self).__init__()
        widget_layout = QtGui.QVBoxLayout()
        table = QtGui.QTableView( self )
        table.setModel( table_model )
        widget_layout.addWidget( table )
        widget_layout.addWidget( ReferenceHoldingBox( table_model, self ) )
        self.setLayout( widget_layout )

class ModelViewRegister(QtCore.QObject):
    
    def __init__(self):
        super(ModelViewRegister, self).__init__()
        self.max_key = 0
        self.model_by_view = dict()
        
    def register_model_view(self, model, view):
        self.max_key += 1
        view.destroyed.connect( self._registered_object_destroyed )
        self.model_by_view[self.max_key] = model
        view.setProperty( 'registered_key', self.max_key )
        
    @QtCore.pyqtSlot(QtCore.QObject)
    def _registered_object_destroyed(self, qobject):
        key, _success = qobject.property('registered_key').toLongLong()
        del self.model_by_view[key]

class TableViewCases(unittest.TestCase):
    """Tests related to table views"""

    def setUp(self):
        from camelot.test import get_application
        self.app = get_application()

    def test_table_view_garbage_collection(self):
        """Create a table view and force its garbage collection, while
        a common reference exists to both the table view and its model.
        
        when doing so without registering the model and the view to the
        ModelViewRegister, this will segfault.
        """            
        register = ModelViewRegister()
        
        import gc
        for _i in range(100):
            
            class TableModelSubclass(QtGui.QStringListModel):
                pass
    
            model = TableModelSubclass()
            widget = TableView( model )
            register.register_model_view(model, widget)
            gc.collect()

class SignalEmitter(QtCore.QObject):
    
    my_signal = QtCore.pyqtSignal(object)
    
    def start_emitting(self):
        for _i in range(1000):
            o = object()
            self.my_signal.emit(o)

class SignalReceiver(QtCore.QObject):
    
    @QtCore.pyqtSlot(object)
    def my_slot(self, obj):
        print obj

class GarbageCollectionCase( unittest.TestCase ):
    
    def setUp(self):
        self.application = QtGui.QApplication.instance()
        if not self.application:
            import sys
            self.application = QtGui.QApplication(sys.argv)
        
    def test_cyclic_dependency( self ):
        """Create 2 widgets with a cyclic dependency, so that they can
        only be removed by the garbage collector, and then invoke the
        garbage collector in a different thread.
        """
        import gc
        
        class CyclicChildWidget(QtGui.QWidget):
            
            def __init__( self, parent ):
                super( CyclicChildWidget, self ).__init__( parent )
                self._parent = parent
                
        class CyclicWidget(QtGui.QWidget):
            
            def __init__( self ):
                super( CyclicWidget, self ).__init__()
                CyclicChildWidget( self )
                    
        # turn off automatic garbage collection, to be able to trigger it
        # at the 'right' time
        gc.disable()
        alive = lambda :sum( isinstance(o,CyclicWidget) for o in gc.get_objects() )
        #
        # first proof that the wizard is only destructed by the garbage
        # collector
        #
        cycle = CyclicWidget()
        self.assertTrue( alive() )
        del cycle
        self.assertTrue( alive() )
        gc.collect()
        self.assertFalse( alive() )
        #
        # now run the garbage collector in a different thread
        #
        cycle = CyclicWidget()
        del cycle
        self.assertTrue( alive() )

        class GarbageCollectingThread(QtCore.QThread):
            
            def run(thread):
                self.assertTrue( alive() )
                # assertian failure here, and core dump
                gc.collect()
                self.assertFalse( alive() )
                    
        thread = GarbageCollectingThread()
        thread.start()
        thread.wait()
        
class SignalSlotCase( unittest.TestCase ):
    
    def setUp(self):
        from camelot.test import get_application
        self.app = get_application()

    def test_multiple_threads(self):
        """Emit a signal containing a python object and at the
        same time connect to it.
        
        this used to deadlock in pyqt.
        """
            
        emitter = SignalEmitter()
        
        class ReceivingThread(QtCore.QThread):
            
            def run(self):
                receivers = []
                for _i in range(100):
                    receiver = SignalReceiver()
                    emitter.my_signal.connect( receiver.my_slot )
                    receivers.append(receiver)
                    
        thread = ReceivingThread()
        thread.start()
        emitter.start_emitting()
        thread.wait()
        
    def test_received_signals(self):
        """See what happens when an object that has
        been deleted receives signals"""

        class SignalReceiver(QtGui.QWidget):
    
            def __init__(self, parent):
                super(SignalReceiver, self).__init__(parent)
                receiver_child = QtGui.QWidget(self)
                receiver_child.setObjectName('child')
                
            @QtCore.pyqtSlot(object)
            def my_slot(self, obj):
                child = self.findChild(QtCore.QObject, 'child')
                print child.objectName()
        
        class ReceiverParent(QtGui.QTabWidget):
            
            def __init__(self):
                super(ReceiverParent, self).__init__()
                receiver = SignalReceiver(parent=self)
                receiver.setObjectName('receiver')
                self.addTab(receiver, 'receiver')
                
            def get_receiver(self):
                return self.findChild(QtCore.QObject, 'receiver')
        
        receiver_parent = ReceiverParent()
                
        class EmittingThread(QtCore.QThread):
            
            my_signal = QtCore.pyqtSignal(object)
            started = False
            move_on = False
            
            def run(self):
                for i in range(10):
                    self.my_signal.emit( i )
                    self.started = True
                    while not self.move_on:
                        pass
                                    
        thread = EmittingThread()
        thread.my_signal.connect( receiver_parent.get_receiver().my_slot, QtCore.Qt.QueuedConnection )
        #del receiver_parent
        thread.start()
        while thread.started == False:
            thread.wait(1)
            self.app.processEvents()
        receiver_parent.widget(0).deleteLater()
        receiver_parent.removeTab(0)
        import gc
        gc.collect()
        thread.move_on = True
        thread.wait()
        self.app.processEvents()
