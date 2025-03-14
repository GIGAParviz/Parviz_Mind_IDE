"""
Parviz Mind IDE - A Python IDE with integrated AI assistance
Main entry point for the application
"""

import sys
import os
import traceback
import argparse
import logging
from pathlib import Path
from datetime import datetime

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def setup_logging(log_level="INFO"):
    """Set up logging configuration"""
    logs_dir = os.path.join(project_root, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    
    log_file = os.path.join(logs_dir, f"parviz_ide_{datetime.now().strftime('%Y%m%d')}.log")
    
    log_levels = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }
    
    level = log_levels.get(log_level.upper(), logging.INFO)
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger("ParvizIDE")

def global_exception_handler(exc_type, exc_value, exc_traceback):
    """Global exception handler for uncaught exceptions"""
    from PyQt6.QtWidgets import QMessageBox, QApplication
    
    traceback.print_exception(exc_type, exc_value, exc_traceback)
    logger.error("Unhandled exception", exc_info=(exc_type, exc_value, exc_traceback))
    
    if QApplication.instance() is None:
        app = QApplication(sys.argv)
    
    error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    error_dialog = QMessageBox()
    error_dialog.setWindowTitle("Critical Error")
    error_dialog.setText("An unexpected error has occurred:")
    error_dialog.setInformativeText(str(exc_value))
    error_dialog.setDetailedText(error_msg)
    error_dialog.setIcon(QMessageBox.Icon.Critical)
    error_dialog.exec()

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Parviz Mind IDE - Python IDE with AI assistance')
    parser.add_argument('--file', '-f', help='File to open on startup')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        default='INFO', help='Set logging level')
    parser.add_argument('--version', '-v', action='store_true', help='Show version information')
    return parser.parse_args()

def main():
    """Main entry point for the application"""
    args = parse_arguments()
    
    global logger
    logger = setup_logging(args.log_level)
    
    sys.excepthook = global_exception_handler
    
    if args.version:
        try:
            from src.version import __version__, __author__, __description__
            print(f"{__description__} v{__version__}")
            print(f"Author: {__author__}")
            return 0
        except ImportError:
            print("Parviz Mind IDE")
            print("Version information not available")
            return 0
    
    try:
        from PyQt6.QtWidgets import QApplication
        from src.ui.ide_window import SimpleIDE
        
        app = QApplication(sys.argv)
        app.setApplicationName("Parviz Mind IDE")
         
        try:
            from src.version import __version__
            app.setApplicationVersion(__version__)
        except ImportError:
            app.setApplicationVersion("dev")
        
        logger.info("Starting Parviz Mind IDE")
        ide = SimpleIDE()
        
        if args.file:
            file_path = os.path.abspath(args.file)
            if os.path.isfile(file_path):
                logger.info(f"Opening file: {file_path}")
                ide.open_file(file_path)
            else:
                logger.warning(f"File not found: {file_path}")
        
        ide.show()
        return app.exec()
        
    except Exception as e:
        logger.critical(f"Fatal error: {str(e)}", exc_info=True)
        raise

if __name__ == '__main__':
    logger = None
    
    sys.exit(main()) 
    
    
    
