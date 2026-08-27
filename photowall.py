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
    QSpinBox,
    QComboBox,
)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt, QTimer, QPoint


class ZonePhoto(QWidget):
    def __init__(self, numero, parent=None):
        super().__init__(parent)

        self.numero = numero
        self.photos = []
        self.index = 0
        self.mode_affichage_actif = False

        self.orientation_actuelle = "Paysage"

        self.largeur_photo = 360
        self.hauteur_photo = 240

        self.deplacement = False
        self.redimensionnement = False

        self.depart_souris = QPoint()
        self.depart_position = QPoint()
        self.largeur_depart = 0

        # ---------- BARRE DE DÉPLACEMENT ----------

        self.barre = QLabel(f"Zone {numero} — déplacer ici")
        self.barre.setAlignment(Qt.AlignCenter)
        self.barre.setFixedHeight(25)
        self.barre.setStyleSheet(
            "background-color: #444;"
            "color: white;"
            "font-weight: bold;"
        )

        # ---------- IMAGE ----------

        self.image = QLabel(
            f"Zone {numero}\nAucun dossier sélectionné"
        )

        self.image.setAlignment(Qt.AlignCenter)
        self.image.setStyleSheet(
            "background-color: black;"
            "color: white;"
            "border: 2px solid #777;"
        )

        # ---------- COMMANDES ----------

        self.bouton_dossier = QPushButton("Choisir un dossier")
        self.bouton_dossier.clicked.connect(self.choisir_dossier)

        self.vitesse = QSpinBox()
        self.vitesse.setRange(1, 60)
        self.vitesse.setValue(5)
        self.vitesse.setSuffix(" s")
        self.vitesse.valueChanged.connect(self.changer_vitesse)

        self.orientation = QComboBox()
        self.orientation.addItems(["Paysage", "Portrait"])
        self.orientation.currentTextChanged.connect(
            self.changer_orientation
        )

        commandes_layout = QHBoxLayout()
        commandes_layout.setContentsMargins(0, 0, 0, 0)

        commandes_layout.addWidget(self.bouton_dossier)
        commandes_layout.addWidget(self.vitesse)
        commandes_layout.addWidget(self.orientation)

        self.commandes = QWidget()
        self.commandes.setLayout(commandes_layout)
        self.commandes.setFixedHeight(32)

        # ---------- POIGNÉE ----------

        self.poignee = QLabel("↘", self)
        self.poignee.setAlignment(Qt.AlignCenter)
        self.poignee.setFixedSize(26, 26)

        self.poignee.setStyleSheet(
            "background-color: #eeeeee;"
            "border: 1px solid #555;"
            "font-size: 18px;"
        )

        self.poignee.setCursor(Qt.SizeFDiagCursor)

        # ---------- LAYOUT ----------

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        layout.addWidget(self.barre)
        layout.addWidget(self.image)
        layout.addWidget(self.commandes)

        self.setLayout(layout)

        # ---------- TIMER ----------

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.photo_suivante)
        self.timer.start(5000)

        # Déplacement avec la barre
        self.barre.installEventFilter(self)

        # Redimensionnement avec la poignée
        self.poignee.installEventFilter(self)

        self.appliquer_dimensions()

    # ======================================================
    # DOSSIER / PHOTOS
    # ======================================================

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
            self.image.setText("Aucune photo trouvée")

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

    # ======================================================
    # ORIENTATION
    # ======================================================

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

    # ======================================================
    # DIMENSIONS
    # ======================================================

    def appliquer_dimensions(self):
        self.image.setFixedSize(
            self.largeur_photo,
            self.hauteur_photo
        )

        if self.mode_affichage_actif:
            hauteur_totale = self.hauteur_photo
        else:
            hauteur_totale = (
                25 +
                self.hauteur_photo +
                32 +
                4
            )

        self.setFixedSize(
            self.largeur_photo,
            hauteur_totale
        )

        self.positionner_poignee()

    def positionner_poignee(self):
        self.poignee.move(
            self.width() - self.poignee.width(),
            self.height() - self.poignee.height(),
        )

        self.poignee.raise_()

    # ======================================================
    # SOURIS : DÉPLACEMENT + REDIMENSIONNEMENT
    # ======================================================

    def eventFilter(self, objet, event):

        # ---------- DÉPLACEMENT ----------

        if objet == self.barre:

            if event.type() == event.Type.MouseButtonPress:
                if event.button() == Qt.LeftButton:
                    self.deplacement = True
                    self.depart_souris = (
                        event.globalPosition().toPoint()
                    )
                    self.depart_position = self.pos()
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
                                parent.width() - self.width(),
                            ),
                        )

                        y = max(
                            0,
                            min(
                                nouvelle_position.y(),
                                parent.height() - self.height(),
                            ),
                        )

                        self.move(x, y)

                    return True

            if event.type() == event.Type.MouseButtonRelease:
                self.deplacement = False
                return True

        # ---------- REDIMENSIONNEMENT ----------

        if objet == self.poignee:

            if event.type() == event.Type.MouseButtonPress:
                if event.button() == Qt.LeftButton:
                    self.redimensionnement = True

                    self.depart_souris = (
                        event.globalPosition().toPoint()
                    )

                    self.largeur_depart = (
                        self.largeur_photo
                    )

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

                    # Empêche le cadre de dépasser à droite
                    parent = self.parentWidget()

                    if parent:
                        largeur_max = (
                            parent.width() - self.x()
                        )

                        nouvelle_largeur = min(
                            nouvelle_largeur,
                            largeur_max,
                        )

                    self.largeur_photo = (
                        nouvelle_largeur
                    )

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

    # ======================================================
    # MODE AFFICHAGE
    # ======================================================

    def mode_affichage(self, actif):
        self.mode_affichage_actif = actif

        self.barre.setVisible(not actif)
        self.commandes.setVisible(not actif)
        self.poignee.setVisible(not actif)

        self.appliquer_dimensions()
        self.afficher_photo()


class PhotoWall(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PhotoWall")
        self.resize(1400, 850)

        self.zones = []
        self.mode_diaporama = False

        # ==================================================
        # HAUT DE FENÊTRE
        # ==================================================

        self.titre = QLabel("PhotoWall")
        self.titre.setAlignment(Qt.AlignCenter)

        self.titre.setStyleSheet(
            "font-size: 28px;"
            "font-weight: bold;"
        )

        texte_nombre = QLabel("Nombre de zones :")

        self.nombre_zones = QSpinBox()
        self.nombre_zones.setRange(1, 12)
        self.nombre_zones.setValue(2)

        self.bouton_appliquer = QPushButton("Appliquer")
        self.bouton_appliquer.clicked.connect(
            self.creer_zones
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
        barre_layout.addStretch()
        barre_layout.addWidget(self.bouton_affichage)

        self.barre_commandes = QWidget()
        self.barre_commandes.setLayout(barre_layout)

        # ==================================================
        # SURFACE LIBRE
        # ==================================================

        self.surface = QWidget()

        self.surface.setStyleSheet(
            "background-color: #dddddd;"
        )

        # ==================================================
        # LAYOUT PRINCIPAL
        # ==================================================

        layout = QVBoxLayout()

        layout.addWidget(self.titre)
        layout.addWidget(self.barre_commandes)
        layout.addWidget(self.surface, 1)

        self.setLayout(layout)

        self.creer_zones()

    # ======================================================
    # CRÉATION DES ZONES
    # ======================================================

    def creer_zones(self):

        for zone in self.zones:
            zone.deleteLater()

        self.zones.clear()

        nombre = self.nombre_zones.value()

        largeur_surface = max(
            self.surface.width(),
            1200
        )

        espace_x = 390
        espace_y = 340

        for i in range(nombre):

            zone = ZonePhoto(
                i + 1,
                self.surface
            )

            colonne = i % 3
            ligne = i // 3

            x = 20 + colonne * espace_x
            y = 20 + ligne * espace_y

            # Si écran trop petit, on garde dans la zone
            if x + zone.width() > largeur_surface:
                x = 20

            zone.move(x, y)
            zone.show()

            self.zones.append(zone)

    # ======================================================
    # CONFIGURATION / AFFICHAGE
    # ======================================================

    def basculer_mode(self):

        self.mode_diaporama = not self.mode_diaporama

        if self.mode_diaporama:

            for zone in self.zones:
                zone.mode_affichage(True)

            self.titre.hide()
            self.barre_commandes.hide()

            self.surface.setStyleSheet(
                "background-color: black;"
            )

            self.showFullScreen()

        else:

            for zone in self.zones:
                zone.mode_affichage(False)

            self.titre.show()
            self.barre_commandes.show()

            self.surface.setStyleSheet(
                "background-color: #dddddd;"
            )

            self.showNormal()

    # ======================================================
    # TOUCHE ÉCHAP
    # ======================================================

    def keyPressEvent(self, event):

        if (
            event.key() == Qt.Key_Escape
            and self.mode_diaporama
        ):

            self.mode_diaporama = False

            for zone in self.zones:
                zone.mode_affichage(False)

            self.titre.show()
            self.barre_commandes.show()

            self.surface.setStyleSheet(
                "background-color: #dddddd;"
            )

            self.showNormal()
            return

        super().keyPressEvent(event)


app = QApplication(sys.argv)

fenetre = PhotoWall()
fenetre.show()

sys.exit(app.exec())
