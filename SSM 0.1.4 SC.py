import sys
import subprocess
import ctypes
import time
import os
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QTextEdit, QFileDialog, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QCoreApplication

def run_as_admin():
    """Relance le script en mode administrateur si nécessaire."""
    if ctypes.windll.shell32.IsUserAnAdmin():
        return

    params = " ".join(f'"{arg}"' for arg in sys.argv)
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
    sys.exit()

run_as_admin()

class CommandWorker(QThread):
    finished = pyqtSignal(str)

    def __init__(self, command):
        super().__init__()
        self.command = command

    def run(self):
        try:
            result = subprocess.run(self.command, shell=True, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            output = result.stdout if result.stdout else "Commande exécutée."
            if result.stderr:
                output += f"\nErreur: {result.stderr}"
        except Exception as e:
            output = f"Erreur lors de l'exécution de la commande : {str(e)}"

        self.finished.emit(output)

class FirewallApp(QWidget):
    def __init__(self):
        super().__init__()

        self.file_path = self.load_steam_path()
        self.initUI()
        self.initTrayIcon()

        self.threads = []  

    def initUI(self):
        self.setWindowTitle("Steam Share Master - SSM")
        self.setFixedSize(370, 350)
        self.setWindowIcon(QIcon(r"SSM-logo-png.ico"))
        self.setStyleSheet("background-color: #1E1E1E;")

        layout = QVBoxLayout()

        # Block / Unblock buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.btn_bloquer = QPushButton("Block Steam", self)
        self.btn_bloquer.setStyleSheet("background-color: red; color: white;")
        self.btn_bloquer.clicked.connect(self.bloquer)
        self.btn_bloquer.setFixedSize(150, 50)
        button_layout.addWidget(self.btn_bloquer)

        self.btn_debloquer = QPushButton("Unblock Steam", self)
        self.btn_debloquer.setStyleSheet("background-color: green; color: white;")
        self.btn_debloquer.clicked.connect(self.debloquer)
        self.btn_debloquer.setFixedSize(150, 50)
        button_layout.addWidget(self.btn_debloquer)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        # Steam path selection button
        center_layout = QHBoxLayout()
        center_layout.addStretch()

        self.btn_choisir = QPushButton("Locate Steam.exe (optional)", self)
        self.btn_choisir.setStyleSheet("background-color: #3C3C3C; color: white; padding: 12px; border-radius: 4px;")
        self.btn_choisir.clicked.connect(self.choisir_steam)
        self.btn_choisir.setFixedSize(300, 50)
        center_layout.addWidget(self.btn_choisir)

        center_layout.addStretch()
        layout.addLayout(center_layout)
        
        
        # Steam path label
        self.label_fichier = QLabel(f"Actual path : {self.file_path}", self)
        self.label_fichier.setStyleSheet("color: white; padding: 4px; border: 1px solid #3F3F3F; border-radius: 7px; margin-top: 10px")
        layout.addWidget(self.label_fichier)

        
        # Log area
        self.log_display = QTextEdit(self)
        self.log_display.setReadOnly(True)
        self.log_display.setStyleSheet("background-color: black; color: lime; font-family: Courier; font-size: 12px; border: 1px solid #3F3F3F; border-radius: 8px")
        layout.addWidget(self.log_display)
        
        # License and affiliation labels
        self.label_copyright1 = QLabel("© 2025 P.Tisseyre. Licensed under GPL-3.0. Steam Share Master (SSM) v0.1.4", self)
        self.label_copyright1.setStyleSheet("color: darkgray; font-size: 10px; text-align: center; margin-top: 5px;")
        layout.addWidget(self.label_copyright1, alignment=Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter)
        
        self.label_affiliation = QLabel("SSM have NO affiliation with Steam. Steam is a trademark of Valve Corporation.", self)
        self.label_affiliation.setStyleSheet("color: darkgray; font-size: 9.35px; text-align: center; margin-top: 0px;")
        layout.addWidget(self.label_affiliation, alignment=Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter)

        self.setLayout(layout)

    def initTrayIcon(self):
        tray_icon = QSystemTrayIcon(QIcon(r"SSM-logo-png.ico"), parent=self)
        tray_icon.setToolTip("Steam Share Master")
       
        # Context menu
        menu = QMenu()
        
        # Taskbar menu actions
        quit_action = QAction("Quitter")
        quit_action.triggered.connect(QCoreApplication.quit)
        menu.addAction(quit_action)

        tray_icon.setContextMenu(menu)
        tray_icon.show()


    # choose the Steam.exe file
    def choisir_steam(self):
        chemin, _ = QFileDialog.getOpenFileName(self, "Sélectionner Steam.exe", "C:\\", "Fichiers EXE (*.exe)")
        if chemin:
            self.file_path = chemin
            self.label_fichier.setText(f"Chemin actuel : {self.file_path}")
            self.save_steam_path()

    def save_steam_path(self):
        with open("steam_path.txt", "w") as f:
            f.write(self.file_path)

    def load_steam_path(self):
        if os.path.exists("steam_path.txt"):
            with open("steam_path.txt", "r") as f:
                return f.read().strip()
        return "C:\\Program Files (x86)\\Steam\\Steam.exe"

    def run_cmd(self, cmd):
        worker = CommandWorker(cmd)
        worker.finished.connect(self.update_log)
        worker.finished.connect(lambda: self.threads.remove(worker))
        self.threads.append(worker)
        worker.start()

    def update_log(self, message):
        
        # Unwanted log messages
        unwanted_messages = [

        "Op‚ration r‚ussieÿ: le processus \"steam.exe\" de PID",
        "Op‚ration r‚ussieÿ: le processus \"steamwebhelper.exe\" de PID",
        "Op‚ration r‚ussieÿ: le processus \"steamservice.exe\" de PID",
        "Ok.",
        "Commande exécutée."

            

        ]

        # If the message contains one of the unwanted strings, don't display it

        if any(unwanted_message in message for unwanted_message in unwanted_messages):
            return
        
        
        current_text = self.log_display.toPlainText()
        new_text = current_text + message + "\n"

        # Split current text into lines
        lines = new_text.split("\n")

        # Keep only the last three lines
        if len(lines) > 4:
            lines = lines[-2:]

        # Reassemble the lines into a single string
        truncated_text = "\n".join(lines)

        # Update text area with truncated text
        self.log_display.setPlainText(truncated_text)

    # block Steam
    def bloquer(self):
        self.update_log("Blocking Steam...")
        self.run_cmd('taskkill /F /IM "steam.exe" /IM "steamwebhelper.exe" /IM "steamservice.exe"')
        time.sleep(2)
        self.run_cmd(f'netsh advfirewall firewall add rule name="BlockSteam" dir=out action=block program="{self.file_path}" enable=yes')
        self.update_log("Steam blocked.")
        self.relaunch_steam()

    # unblock Steam
    def debloquer(self):
        self.update_log("Unblocking Steam...")
        self.run_cmd('netsh advfirewall firewall set rule name="BlockSteam" new enable=no')
        time.sleep(1)  
        self.update_log("Steam unblocked.")
        self.relaunch_steam()

    # restart Steam after blocking or unblocking
    def relaunch_steam(self):
        """Ferme et relance Steam après le blocage ou le déblocage."""
        self.update_log("Closing and restarting Steam...")
        self.run_cmd('taskkill /F /IM "steam.exe" /IM "steamwebhelper.exe" /IM "steamservice.exe"')
        time.sleep(3)  
        self.run_cmd(f'start "" "{self.file_path}"')

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FirewallApp()
    window.show()
    sys.exit(app.exec())
