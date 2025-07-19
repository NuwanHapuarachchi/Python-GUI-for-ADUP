import sys
import os
from pathlib import Path


project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """Main application entry point"""
    try:
        
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import QCoreApplication
        from PyQt6.QtGui import QIcon
        
        
        QCoreApplication.setApplicationName("ADUP")
        QCoreApplication.setApplicationVersion("1.3")
        QCoreApplication.setOrganizationName("Notwork")
        
        app = QApplication(sys.argv)
        app.setApplicationDisplayName("ADUP - Advanced Diffusing Update Protocol By Notwork")
        
        
        app.setStyle('Fusion')
        
        
        from gui.main_window import ADUPMainWindow
        
        
        main_window = ADUPMainWindow()
        main_window.show()
        
        
        screen = app.primaryScreen().geometry()
        window_rect = main_window.geometry()
        x = (screen.width() - window_rect.width()) // 2
        y = (screen.height() - window_rect.height()) // 2
        main_window.move(x, y)
                
        sys.exit(app.exec())
        
    except ImportError as e:
        print(f"Import Error: {e}")
        print("Please ensure PyQt6 is installed:")
        print("pip install PyQt6 PyQt6-tools pyqtgraph matplotlib")
        sys.exit(1)
        
    except Exception as e:
        print(f"Application Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
