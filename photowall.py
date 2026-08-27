import sys
import os
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QPushButton,
    QFileDialog,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QSpinBox,
)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt, QTimer


class ZonePhoto(QWidget):
    def __init__(self, numero):
        super().__init__()

        self.numero = numero
        self.photos = []
        self.index = 0

        self.image = QLabel(f"Zone {numero}\nAucun dossier sélectionné")
        self.image.setAlignment(Qt.AlignCenter)
        self.image.setMinimumSize(300, 200)
        self.image.setStyleSheet(
            "background-color: black; color: white; border: 2px solid gray;"
        )

        self.bouton_dossier = QPushButton("Choisir un dossier")
        self.bouton_dossier.clicked.connect(self.choisir_dossier)

        self.vitesse = QSpinBox()
        self.vitesse.setRange(1, 60)
        self.vitesse.setValue(5)
        self.vitesse.setSuffix(" secondes")
        self.vitesse.valueChanged.connect(self.changer_vitesse)

        commandes = QHBoxLayout()
        commandes.addWidget(self.bouton_dossier)
        commandes.addWidget(self.vitesse)

        layout = QVBoxLayout()
        layout.addWidget(self.image)
        layout.addLayout(commandes)

        self.setLayout(layout)

        self.timer = QTimer()
        self.timer.timeout.connect(self.photo_suivante)
        self.timer.start(5000)

    def choisir_dossier(self):
        dossier = QFileDialog.getExistingDirectory(
            self,
            f"Choisir le dossier de la zone {self.numero}"
        )

        if not dossier:
            return

        extensions = (".jpg", ".jpeg", ".png", ".bmp", ".webp")

        self.photos = [
            os.path.join(dossier, fichier)
            for fichier in os.listdir(dossier)
            if fichier.lower().endswith(extensions)
        ]

        self.photos.sort()
        self.index = 0

        if self.photos:
            self.afficher_photo()
        else:
            self.image.setText("Aucune photo trouvée dans ce dossier")

    def afficher_photo(self):
        if not self.photos:
            return

        pixmap = QPixmap(self.photos[self.index])

        pixmap = pixmap.scaled(
            self.image.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )

        self.image.setPixmap(pixmap)

    def photo_suivante(self):
        if not self.photos:
            return

        self.index = (self.index + 1) % len(self.photos)
        self.afficher_photo()

    def changer_vitesse(self):
        self.timer.setInterval(self.vitesse.value() * 1000)

    def resizeEvent(self, event):
        self.afficher_photo()
        super().resizeEvent(event)


class PhotoWall(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PhotoWall")
        self.resize(1200, 750)

        titre = QLabel("PhotoWall")
        titre.setAlignment(Qt.AlignCenter)
        titre.setStyleSheet(
            "font-size: 28px; font-weight: bold;"
        )

        self.grille = QGridLayout()

        self.zone1 = ZonePhoto(1)
        self.zone2 = ZonePhoto(2)

        self.grille.addWidget(self.zone1, 0, 0)
        self.grille.addWidget(self.zone2, 0, 1)

        bouton_plein_ecran = QPushButton("Plein écran")
        bouton_plein_ecran.clicked.connect(self.plein_ecran)

        layout = QVBoxLayout()
        layout.addWidget(titre)
        layout.addLayout(self.grille)
        layout.addWidget(bouton_plein_ecran)

        self.setLayout(layout)

    def plein_ecran(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()


app = QApplication(sys.argv)

fenetre = PhotoWall()
fenetre.show()

sys.exit(app.exec())
