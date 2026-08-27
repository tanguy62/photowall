import sys
import os
import math

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
    QComboBox,
)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt, QTimer, QSize


class PhotoLabel(QLabel):
    def __init__(self):
        super().__init__()

        self.orientation = "Paysage"

        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet(
            "background-color: black;"
            "color: white;"
            "border: 2px solid gray;"
        )

    def set_orientation(self, orientation):
        self.orientation = orientation
        self.updateGeometry()

    def sizeHint(self):
        if self.orientation == "Portrait":
            return QSize(300, 450)

        return QSize(450, 300)

    def heightForWidth(self, largeur):
        if self.orientation == "Portrait":
            return int(largeur * 1.5)

        return int(largeur * 2 / 3)


class ZonePhoto(QWidget):
    def __init__(self, numero):
        super().__init__()

        self.numero = numero
        self.photos = []
        self.index = 0

        self.image = PhotoLabel()
        self.image.setText(
            f"Zone {numero}\nAucun dossier sélectionné"
        )

        self.bouton_dossier = QPushButton("Choisir un dossier")
        self.bouton_dossier.clicked.connect(self.choisir_dossier)

        self.vitesse = QSpinBox()
        self.vitesse.setRange(1, 60)
        self.vitesse.setValue(5)
        self.vitesse.setSuffix(" secondes")
        self.vitesse.valueChanged.connect(self.changer_vitesse)

        self.orientation = QComboBox()
        self.orientation.addItems(["Paysage", "Portrait"])
        self.orientation.currentTextChanged.connect(
            self.changer_orientation
        )

        commandes = QHBoxLayout()
        commandes.addWidget(self.bouton_dossier)
        commandes.addWidget(self.vitesse)
        commandes.addWidget(self.orientation)

        self.commandes_widget = QWidget()
        self.commandes_widget.setLayout(commandes)

        layout = QVBoxLayout()
        layout.addWidget(self.image)
        layout.addWidget(self.commandes_widget)

        self.setLayout(layout)

        self.timer = QTimer()
        self.timer.timeout.connect(self.photo_suivante)
        self.timer.start(5000)

        self.changer_orientation("Paysage")

    def choisir_dossier(self):
        dossier = QFileDialog.getExistingDirectory(
            self,
            f"Choisir le dossier de la zone {self.numero}"
        )

        if not dossier:
            return

        extensions = (
            ".jpg",
            ".jpeg",
            ".png",
            ".bmp",
            ".webp",
        )

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
            self.image.clear()
            self.image.setText(
                "Aucune photo trouvée dans ce dossier"
            )

    def afficher_photo(self):
        if not self.photos:
            return

        pixmap = QPixmap(self.photos[self.index])

        if pixmap.isNull():
            return

        pixmap = pixmap.scaled(
            self.image.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )

        self.image.setPixmap(pixmap)

    def photo_suivante(self):
        if not self.photos:
            return

        self.index = (self.index + 1) % len(self.photos)
        self.afficher_photo()

    def changer_vitesse(self):
        self.timer.setInterval(
            self.vitesse.value() * 1000
        )

    def changer_orientation(self, orientation):
        self.image.set_orientation(orientation)

        if orientation == "Portrait":
            largeur = 240
            hauteur = 360
        else:
            largeur = 360
            hauteur = 240

        self.image.setMinimumSize(largeur, hauteur)
        self.image.setMaximumSize(largeur, hauteur)

        self.adjustSize()
        self.afficher_photo()

    def mode_affichage(self, actif):
        self.commandes_widget.setVisible(not actif)

    def resizeEvent(self, event):
        self.afficher_photo()
        super().resizeEvent(event)


class PhotoWall(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PhotoWall")
        self.resize(1200, 800)

        self.zones = []
        self.mode_diaporama = False

        self.titre = QLabel("PhotoWall")
        self.titre.setAlignment(Qt.AlignCenter)
        self.titre.setStyleSheet(
            "font-size: 28px;"
            "font-weight: bold;"
        )

        texte_nombre = QLabel("Nombre de zones :")

        self.nombre_zones = QSpinBox()
        self.nombre_zones.setRange(1, 9)
        self.nombre_zones.setValue(2)

        self.bouton_appliquer = QPushButton("Appliquer")
        self.bouton_appliquer.clicked.connect(
            self.creer_zones
        )

        self.bouton_mode = QPushButton(
            "Passer en mode Affichage"
        )
        self.bouton_mode.clicked.connect(
            self.basculer_mode
        )

        commandes_generales = QHBoxLayout()
        commandes_generales.addWidget(texte_nombre)
        commandes_generales.addWidget(self.nombre_zones)
        commandes_generales.addWidget(self.bouton_appliquer)
        commandes_generales.addStretch()
        commandes_generales.addWidget(self.bouton_mode)

        self.commandes_generales_widget = QWidget()
        self.commandes_generales_widget.setLayout(
            commandes_generales
        )

        self.grille = QGridLayout()

        self.bouton_plein_ecran = QPushButton(
            "Plein écran"
        )
        self.bouton_plein_ecran.clicked.connect(
            self.plein_ecran
        )

        layout = QVBoxLayout()
        layout.addWidget(self.titre)
        layout.addWidget(
            self.commandes_generales_widget
        )
        layout.addLayout(self.grille)
        layout.addWidget(self.bouton_plein_ecran)

        self.setLayout(layout)

        self.creer_zones()

    def vider_grille(self):
        while self.grille.count():
            item = self.grille.takeAt(0)
            widget = item.widget()

            if widget is not None:
                widget.deleteLater()

        self.zones.clear()

    def creer_zones(self):
        self.vider_grille()

        nombre = self.nombre_zones.value()
        colonnes = math.ceil(math.sqrt(nombre))

        for i in range(nombre):
            zone = ZonePhoto(i + 1)
            self.zones.append(zone)

            ligne = i // colonnes
            colonne = i % colonnes

            self.grille.addWidget(
                zone,
                ligne,
                colonne,
                alignment=Qt.AlignCenter,
            )

    def basculer_mode(self):
        self.mode_diaporama = not self.mode_diaporama

        for zone in self.zones:
            zone.mode_affichage(self.mode_diaporama)

        if self.mode_diaporama:
            self.titre.hide()
            self.commandes_generales_widget.hide()
            self.bouton_plein_ecran.hide()

            self.setStyleSheet(
                "background-color: black;"
            )

            self.showFullScreen()

        else:
            self.titre.show()
            self.commandes_generales_widget.show()
            self.bouton_plein_ecran.show()

            self.setStyleSheet("")

            self.showNormal()

    def plein_ecran(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            if self.mode_diaporama:
                self.mode_diaporama = False

                for zone in self.zones:
                    zone.mode_affichage(False)

                self.titre.show()
                self.commandes_generales_widget.show()
                self.bouton_plein_ecran.show()

                self.setStyleSheet("")
                self.showNormal()

                return

            if self.isFullScreen():
                self.showNormal()
                return

        super().keyPressEvent(event)


app = QApplication(sys.argv)

fenetre = PhotoWall()
fenetre.show()

sys.exit(app.exec())
