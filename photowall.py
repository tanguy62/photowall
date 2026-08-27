import sys
import os
import json

from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QFileDialog,
    QVBoxLayout, QHBoxLayout, QSpinBox, QComboBox, QMessageBox
)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt, QTimer, QPoint, QRect


CONFIG_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "photowall_config.json"
)


class ZonePhoto(QWidget):
    def __init__(self, numero, parent=None):
        super().__init__(parent)

        self.numero = numero
        self.photos = []
        self.dossier = ""
        self.index = 0

        self.mode_affichage_actif = False
        self.orientation_actuelle = "Paysage"
        self.mode_image = "Photo entière"

        self.largeur_photo = 360
        self.hauteur_photo = 240

        self.deplacement = False
        self.redimensionnement = False

        self.depart_souris = QPoint()
        self.depart_position = QPoint()
        self.largeur_depart = 0

        # Barre de déplacement
        self.barre = QLabel(f"Zone {numero} — déplacer ici")
        self.barre.setAlignment(Qt.AlignCenter)
        self.barre.setFixedHeight(25)
        self.barre.setStyleSheet(
            "background-color:#444;"
            "color:white;"
            "font-weight:bold;"
        )

        # Image
        self.image = QLabel(
            f"Zone {numero}\nAucun dossier sélectionné"
        )
        self.image.setAlignment(Qt.AlignCenter)
        self.image.setStyleSheet(
            "background-color:black;"
            "color:white;"
            "border:2px solid #777;"
        )

        # Choix dossier
        self.bouton_dossier = QPushButton("Choisir dossier")
        self.bouton_dossier.clicked.connect(self.choisir_dossier)

        # Vitesse
        self.vitesse = QSpinBox()
        self.vitesse.setRange(1, 60)
        self.vitesse.setValue(5)
        self.vitesse.setSuffix(" s")
        self.vitesse.valueChanged.connect(self.changer_vitesse)

        # Orientation
        self.orientation = QComboBox()
        self.orientation.addItems(["Paysage", "Portrait"])
        self.orientation.currentTextChanged.connect(
            self.changer_orientation
        )

        # Mode d'affichage de la photo
        self.mode_combo = QComboBox()
        self.mode_combo.addItems([
            "Photo entière",
            "Remplir"
        ])
        self.mode_combo.currentTextChanged.connect(
            self.changer_mode_image
        )

        commandes_layout = QHBoxLayout()
        commandes_layout.setContentsMargins(0, 0, 0, 0)

        commandes_layout.addWidget(self.bouton_dossier)
        commandes_layout.addWidget(self.vitesse)
        commandes_layout.addWidget(self.orientation)
        commandes_layout.addWidget(self.mode_combo)

        self.commandes = QWidget()
        self.commandes.setLayout(commandes_layout)
        self.commandes.setFixedHeight(32)

        # Poignée
        self.poignee = QLabel("↘", self)
        self.poignee.setAlignment(Qt.AlignCenter)
        self.poignee.setFixedSize(26, 26)
        self.poignee.setStyleSheet(
            "background-color:#eeeeee;"
            "border:1px solid #555;"
            "font-size:18px;"
        )
        self.poignee.setCursor(Qt.SizeFDiagCursor)

        # Layout
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        layout.addWidget(self.barre)
        layout.addWidget(self.image)
        layout.addWidget(self.commandes)

        self.setLayout(layout)

        # Diaporama
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.photo_suivante)
        self.timer.start(5000)

        self.barre.installEventFilter(self)
        self.poignee.installEventFilter(self)

        self.appliquer_dimensions()

    # --------------------------------------------------
    # PHOTOS
    # --------------------------------------------------

    def charger_dossier(self, dossier):
        self.dossier = dossier

        if not dossier or not os.path.isdir(dossier):
            self.photos = []
            self.image.clear()
            self.image.setText(
                f"Zone {self.numero}\nDossier introuvable"
            )
            return

        extensions = (
            ".jpg", ".jpeg", ".png",
            ".bmp", ".webp"
        )

        try:
            self.photos = [
                os.path.join(dossier, fichier)
                for fichier in os.listdir(dossier)
                if fichier.lower().endswith(extensions)
            ]
        except OSError:
            self.photos = []

        self.photos.sort()
        self.index = 0

        if self.photos:
            self.afficher_photo()
        else:
            self.image.clear()
            self.image.setText(
                "Aucune photo trouvée"
            )

    def choisir_dossier(self):
        dossier = QFileDialog.getExistingDirectory(
            self,
            f"Choisir le dossier de la zone {self.numero}"
        )

        if dossier:
            self.charger_dossier(dossier)

    def afficher_photo(self):
        if not self.photos:
            return

        pixmap = QPixmap(self.photos[self.index])

        if pixmap.isNull():
            return

        if self.mode_image == "Remplir":
            pixmap = pixmap.scaled(
                self.image.size(),
                Qt.KeepAspectRatioByExpanding,
                Qt.SmoothTransformation
            )

            x = max(
                0,
                (pixmap.width() - self.image.width()) // 2
            )
            y = max(
                0,
                (pixmap.height() - self.image.height()) // 2
            )

            pixmap = pixmap.copy(
                QRect(
                    x,
                    y,
                    self.image.width(),
                    self.image.height()
                )
            )

        else:
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
        self.timer.setInterval(
            self.vitesse.value() * 1000
        )

    def changer_mode_image(self, mode):
        self.mode_image = mode
        self.afficher_photo()

    # --------------------------------------------------
    # ORIENTATION / DIMENSIONS
    # --------------------------------------------------

    def changer_orientation(self, orientation):
        self.orientation_actuelle = orientation

        if orientation == "Paysage":
            self.hauteur_photo = int(
                self.largeur_photo * 2 / 3
            )
        else:
            self.hauteur_photo = int(
                self.largeur_photo * 3 / 2
            )

        self.appliquer_dimensions()
        self.afficher_photo()

    def appliquer_dimensions(self):
        self.image.setFixedSize(
            self.largeur_photo,
            self.hauteur_photo
        )

        if self.mode_affichage_actif:
            hauteur_totale = self.hauteur_photo
        else:
            hauteur_totale = (
                25 + self.hauteur_photo + 32 + 4
            )

        self.setFixedSize(
            self.largeur_photo,
            hauteur_totale
        )

        self.positionner_poignee()

    def positionner_poignee(self):
        self.poignee.move(
            self.width() - self.poignee.width(),
            self.height() - self.poignee.height()
        )
        self.poignee.raise_()

    # --------------------------------------------------
    # SOURIS
    # --------------------------------------------------

    def eventFilter(self, objet, event):

        # Déplacement
        if objet == self.barre:

            if event.type() == event.Type.MouseButtonPress:
                if event.button() == Qt.LeftButton:
                    self.deplacement = True
                    self.depart_souris = (
                        event.globalPosition().toPoint()
                    )
                    self.depart_position = self.pos()
                    self.raise_()
                    return True

            if event.type() == event.Type.MouseMove:
                if self.deplacement:
                    delta = (
                        event.globalPosition().toPoint()
                        - self.depart_souris
                    )

                    nouvelle_position = (
                        self.depart_position + delta
                    )

                    parent = self.parentWidget()

                    if parent:
                        x = max(
                            0,
                            min(
                                nouvelle_position.x(),
                                parent.width() - self.width()
                            )
                        )

                        y = max(
                            0,
                            min(
                                nouvelle_position.y(),
                                parent.height() - self.height()
                            )
                        )

                        self.move(x, y)

                    return True

            if event.type() == event.Type.MouseButtonRelease:
                self.deplacement = False
                return True

        # Redimensionnement
        if objet == self.poignee:

            if event.type() == event.Type.MouseButtonPress:
                if event.button() == Qt.LeftButton:
                    self.redimensionnement = True
                    self.depart_souris = (
                        event.globalPosition().toPoint()
                    )
                    self.largeur_depart = self.largeur_photo
                    self.raise_()
                    return True

            if event.type() == event.Type.MouseMove:
                if self.redimensionnement:

                    delta = (
                        event.globalPosition().toPoint().x()
                        - self.depart_souris.x()
                    )

                    nouvelle_largeur = (
                        self.largeur_depart + delta
                    )

                    nouvelle_largeur = max(
                        150,
                        nouvelle_largeur
                    )

                    parent = self.parentWidget()

                    if parent:
                        largeur_max = (
                            parent.width() - self.x()
                        )

                        nouvelle_largeur = min(
                            nouvelle_largeur,
                            largeur_max
                        )

                    self.largeur_photo = nouvelle_largeur

                    if self.orientation_actuelle == "Paysage":
                        self.hauteur_photo = int(
                            self.largeur_photo * 2 / 3
                        )
                    else:
                        self.hauteur_photo = int(
                            self.largeur_photo * 3 / 2
                        )

                    self.appliquer_dimensions()
                    self.afficher_photo()

                    return True

            if event.type() == event.Type.MouseButtonRelease:
                self.redimensionnement = False
                return True

        return super().eventFilter(objet, event)

    # --------------------------------------------------
    # MODE AFFICHAGE
    # --------------------------------------------------

    def mode_affichage(self, actif):
        self.mode_affichage_actif = actif

        self.barre.setVisible(not actif)
        self.commandes.setVisible(not actif)
        self.poignee.setVisible(not actif)

        self.appliquer_dimensions()
        self.afficher_photo()

    # --------------------------------------------------
    # SAUVEGARDE DE LA ZONE
    # --------------------------------------------------

    def obtenir_configuration(self):
        return {
            "x": self.x(),
            "y": self.y(),
            "largeur": self.largeur_photo,
            "orientation": self.orientation_actuelle,
            "vitesse": self.vitesse.value(),
            "dossier": self.dossier,
            "mode_image": self.mode_image
        }

    def appliquer_configuration(self, config):
        self.largeur_photo = int(
            config.get("largeur", 360)
        )

        orientation = config.get(
            "orientation",
            "Paysage"
        )

        self.orientation.setCurrentText(orientation)
        self.orientation_actuelle = orientation

        if orientation == "Paysage":
            self.hauteur_photo = int(
                self.largeur_photo * 2 / 3
            )
        else:
            self.hauteur_photo = int(
                self.largeur_photo * 3 / 2
            )

        self.vitesse.setValue(
            int(config.get("vitesse", 5))
        )

        mode = config.get(
            "mode_image",
            "Photo entière"
        )

        self.mode_combo.setCurrentText(mode)
        self.mode_image = mode

        self.appliquer_dimensions()

        self.move(
            int(config.get("x", 20)),
            int(config.get("y", 20))
        )

        dossier = config.get("dossier", "")

        if dossier:
            self.charger_dossier(dossier)


class PhotoWall(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PhotoWall")
        self.resize(1400, 850)

        self.zones = []
        self.mode_diaporama = False

        # Titre
        self.titre = QLabel("PhotoWall")
        self.titre.setAlignment(Qt.AlignCenter)
        self.titre.setStyleSheet(
            "font-size:28px;"
            "font-weight:bold;"
        )

        texte_nombre = QLabel("Nombre de zones :")

        self.nombre_zones = QSpinBox()
        self.nombre_zones.setRange(1, 12)
        self.nombre_zones.setValue(2)

        self.bouton_appliquer = QPushButton("Appliquer")
        self.bouton_appliquer.clicked.connect(
            self.creer_zones
        )

        self.bouton_sauver = QPushButton(
            "Enregistrer la configuration"
        )
        self.bouton_sauver.clicked.connect(
            self.sauvegarder_configuration
        )

        self.bouton_charger = QPushButton(
            "Charger la configuration"
        )
        self.bouton_charger.clicked.connect(
            self.charger_configuration
        )

        self.bouton_affichage = QPushButton(
            "Passer en mode Affichage"
        )
        self.bouton_affichage.clicked.connect(
            self.basculer_mode
        )

        barre_layout = QHBoxLayout()

        barre_layout.addWidget(texte_nombre)
        barre_layout.addWidget(self.nombre_zones)
        barre_layout.addWidget(self.bouton_appliquer)
        barre_layout.addWidget(self.bouton_sauver)
        barre_layout.addWidget(self.bouton_charger)
        barre_layout.addStretch()
        barre_layout.addWidget(self.bouton_affichage)

        self.barre_commandes = QWidget()
        self.barre_commandes.setLayout(barre_layout)

        # Surface
        self.surface = QWidget()
        self.surface.setStyleSheet(
            "background-color:#dddddd;"
        )

        # Layout principal
        layout = QVBoxLayout()
        layout.addWidget(self.titre)
        layout.addWidget(self.barre_commandes)
        layout.addWidget(self.surface, 1)

        self.setLayout(layout)

        self.creer_zones()

    # --------------------------------------------------
    # ZONES
    # --------------------------------------------------

    def supprimer_zones(self):
        for zone in self.zones:
            zone.deleteLater()

        self.zones.clear()

    def creer_zones(self):
        self.supprimer_zones()

        nombre = self.nombre_zones.value()

        for i in range(nombre):
            zone = ZonePhoto(
                i + 1,
                self.surface
            )

            colonne = i % 3
            ligne = i // 3

            zone.move(
                20 + colonne * 390,
                20 + ligne * 340
            )

            zone.show()
            self.zones.append(zone)

    # --------------------------------------------------
    # SAUVEGARDE
    # --------------------------------------------------

    def sauvegarder_configuration(self):
        config = {
            "nombre_zones": len(self.zones),
            "zones": [
                zone.obtenir_configuration()
                for zone in self.zones
            ]
        }

        try:
            with open(
                CONFIG_FILE,
                "w",
                encoding="utf-8"
            ) as fichier:
                json.dump(
                    config,
                    fichier,
                    ensure_ascii=False,
                    indent=4
                )

            QMessageBox.information(
                self,
                "PhotoWall",
                "Configuration enregistrée."
            )

        except OSError as erreur:
            QMessageBox.warning(
                self,
                "PhotoWall",
                f"Impossible d'enregistrer :\n{erreur}"
            )

    def charger_configuration(self):
        if not os.path.exists(CONFIG_FILE):
            QMessageBox.information(
                self,
                "PhotoWall",
                "Aucune configuration enregistrée."
            )
            return

        try:
            with open(
                CONFIG_FILE,
                "r",
                encoding="utf-8"
            ) as fichier:
                config = json.load(fichier)

        except (OSError, json.JSONDecodeError) as erreur:
            QMessageBox.warning(
                self,
                "PhotoWall",
                f"Impossible de charger :\n{erreur}"
            )
            return

        nombre = int(
            config.get("nombre_zones", 2)
        )

        nombre = max(1, min(12, nombre))

        self.nombre_zones.setValue(nombre)
        self.supprimer_zones()

        configurations = config.get(
            "zones",
            []
        )

        for i in range(nombre):
            zone = ZonePhoto(
                i + 1,
                self.surface
            )

            if i < len(configurations):
                zone.appliquer_configuration(
                    configurations[i]
                )
            else:
                zone.move(
                    20 + (i % 3) * 390,
                    20 + (i // 3) * 340
                )

            zone.show()
            self.zones.append(zone)

    # --------------------------------------------------
    # MODE AFFICHAGE
    # --------------------------------------------------

    def basculer_mode(self):
        self.mode_diaporama = not self.mode_diaporama

        if self.mode_diaporama:

            for zone in self.zones:
                zone.mode_affichage(True)

            self.titre.hide()
            self.barre_commandes.hide()

            self.surface.setStyleSheet(
                "background-color:black;"
            )

            self.showFullScreen()

        else:
            self.retour_configuration()

    def retour_configuration(self):
        self.mode_diaporama = False

        for zone in self.zones:
            zone.mode_affichage(False)

        self.titre.show()
        self.barre_commandes.show()

        self.surface.setStyleSheet(
            "background-color:#dddddd;"
        )

        self.showNormal()

    def keyPressEvent(self, event):
        if (
            event.key() == Qt.Key_Escape
            and self.mode_diaporama
        ):
            self.retour_configuration()
            return

        super().keyPressEvent(event)


app = QApplication(sys.argv)

fenetre = PhotoWall()

if os.path.exists(CONFIG_FILE):
    fenetre.charger_configuration()

fenetre.show()

sys.exit(app.exec())
