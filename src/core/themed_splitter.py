from PyQt5.QtWidgets import QSplitter, QSplitterHandle
from PyQt5.QtCore import Qt


class ThemedSplitterHandle(QSplitterHandle):
    def __init__(self, orientation, parent):
        super().__init__(orientation, parent)
        self.cursor_type = None
        self.main_app = None
        if hasattr(parent, 'main_app'):
            self.main_app = parent.main_app
    
    def enterEvent(self, event):
        if self.cursor_type and self.main_app and hasattr(self.main_app, 'themed_cursors'):
            themed_cursor = self.main_app.themed_cursors.get(self.cursor_type)
            if themed_cursor:
                self.setCursor(themed_cursor)
                return
        self.setCursor(Qt.SplitVCursor if self.orientation() == Qt.Vertical else Qt.SplitHCursor)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        self.unsetCursor()
        super().leaveEvent(event)


class ThemedSplitter(QSplitter):
    def __init__(self, orientation, parent=None, main_app=None):
        super().__init__(orientation, parent)
        self.main_app = main_app
    
    def createHandle(self):
        return ThemedSplitterHandle(self.orientation(), self)
    
    def update_cursor_type(self, cursor_type):
        self.cursor_type = cursor_type
        for i in range(self.count() - 1):
            handle = self.handle(i + 1)
            if isinstance(handle, ThemedSplitterHandle):
                handle.cursor_type = cursor_type 