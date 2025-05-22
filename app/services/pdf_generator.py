from datetime import datetime
from io import BytesIO
from typing import List, Optional
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus.tableofcontents import SimpleIndex
from reportlab.platypus.frames import Frame
from PIL import Image as PILImage
import os
import base64

from app.models.models import Emargement, Evenement
from app.config import settings, STATIC_DIR

class SignaturePDFGenerator:
    # Définition des couleurs
    PRIMARY_COLOR = colors.HexColor('#000000')  # Noir
    SECONDARY_COLOR = colors.HexColor('#EDD213')  # Jaune MCA
    ACCENT_COLOR = colors.HexColor('#E74C3C')  # Rouge pour les accents
    HEADER_BG_COLOR = colors.HexColor('#F8F9FA')  # Gris très clair
    TABLE_HEADER_COLOR = colors.HexColor('#2C3E50')  # Bleu foncé
    TABLE_HEADER_TEXT_COLOR = colors.white
    TABLE_ROW_COLOR = colors.white
    TABLE_ALT_ROW_COLOR = colors.HexColor('#F8F9FA')  # Gris très clair
    BORDER_COLOR = colors.HexColor('#DEE2E6')  # Gris clair pour les bordures

    def __init__(self):
        # Définir la police par défaut
        self.font_name = 'Helvetica'  # Police par défaut de ReportLab
        
        # Essayer de charger Arial si disponible
        font_path = os.path.join(STATIC_DIR, "fonts", "Arial.ttf")
        if os.path.exists(font_path):
            try:
                pdfmetrics.registerFont(TTFont('Arial', font_path))
                self.font_name = 'Arial'
                print("✅ Police Arial chargée avec succès")
            except Exception as e:
                print(f"⚠️ Impossible de charger la police Arial: {str(e)}")
                print("ℹ️ Utilisation de la police par défaut Helvetica")
        
        # Chemin vers le logo (directement dans le dossier static)
        self.logo_path = os.path.join(STATIC_DIR, "logo.png")
        
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        self.page_count = 0  # Ajouter un compteur de pages
    
    def _setup_custom_styles(self):
        """Configure les styles personnalisés pour le PDF"""
        # Style pour le titre principal
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontName=self.font_name,
            fontSize=20,
            textColor=self.PRIMARY_COLOR,
            spaceAfter=10,
            alignment=TA_CENTER,
            leading=24
        ))
        
        # Style pour le sous-titre
        self.styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=self.styles['Heading2'],
            fontName=self.font_name,
            fontSize=14,
            textColor=self.SECONDARY_COLOR,
            spaceAfter=10,
            alignment=TA_CENTER,
            leading=18
        ))
        
        # Style pour le texte normal
        self.styles.add(ParagraphStyle(
            name='CustomText',
            parent=self.styles['Normal'],
            fontName=self.font_name,
            fontSize=10,
            textColor=self.PRIMARY_COLOR,
            spaceAfter=12,
            leading=14
        ))
        
        # Style pour les informations de l'événement
        self.styles.add(ParagraphStyle(
            name='EventInfo',
            parent=self.styles['Normal'],
            fontName=self.font_name,
            fontSize=11,
            textColor=self.PRIMARY_COLOR,
            spaceAfter=8,
            leading=14,
            alignment=TA_CENTER,
            backColor=self.HEADER_BG_COLOR,
            borderPadding=10,
            borderRadius=5
        ))

    def _base64_to_image(self, base64_string: str, max_width: float = 3*cm, max_height: float = 2*cm) -> Optional[BytesIO]:
        """Convertit une chaîne base64 en image redimensionnée"""
        if not base64_string:
            return None
            
        try:
            # Supprimer le préfixe de l'URL de données si présent
            if ',' in base64_string:
                base64_string = base64_string.split(',')[1]
            
            # Décoder l'image base64
            image_data = base64.b64decode(base64_string)
            img = PILImage.open(BytesIO(image_data))
            
            # Redimensionner l'image
            img.thumbnail((max_width, max_height), PILImage.Resampling.LANCZOS)
            
            # Convertir en PNG
            output = BytesIO()
            img.save(output, format='PNG')
            output.seek(0)
            return output
        except Exception as e:
            print(f"⚠️ Erreur lors du traitement de l'image base64: {str(e)}")
            return None

    def _create_header(self, evenement: Evenement) -> List:
        """Crée l'en-tête du document avec les informations de l'événement"""
        elements = []
        
        # Ajouter le logo si disponible
        if os.path.exists(self.logo_path):
            try:
                # Redimensionner le logo pour qu'il ne soit pas trop grand
                img = PILImage.open(self.logo_path)
                # Calculer les dimensions pour une hauteur de 2.5cm
                target_height = 2.5 * cm
                ratio = target_height / img.height
                target_width = img.width * ratio
                
                # Créer l'image pour le PDF
                logo = Image(self.logo_path, width=target_width, height=target_height)
                elements.append(logo)
                elements.append(Spacer(1, 0.5*cm))
            except Exception as e:
                print(f"⚠️ Impossible de charger le logo: {str(e)}")
        
        # Titre principal et sous-titre sans espace supplémentaire entre eux
        elements.append(Paragraph("LISTE DES PARTICIPANTS", self.styles['CustomTitle']))
        elements.append(Paragraph(evenement.titre, self.styles['CustomSubtitle']))
        elements.append(Spacer(1, 0.5*cm))
        
        # Informations de l'événement dans un bloc stylisé
        event_info = []
        event_info.append(f"Date: {evenement.date_debut.strftime('%d/%m/%Y')}")
        if evenement.date_fin:
            event_info.append(f"au {evenement.date_fin.strftime('%d/%m/%Y')}")
        if evenement.lieu:
            event_info.append(f"Lieu: {evenement.lieu}")
        if evenement.description:
            event_info.append(f"Description: {evenement.description}")
        
        # Créer un bloc d'information stylisé
        info_text = "<br/>".join(event_info)
        elements.append(Paragraph(info_text, self.styles['EventInfo']))
        
        elements.append(Spacer(1, 1*cm))  # Réduit l'espace final de 2cm à 1cm
        
        return elements

    def _create_signature_table(self, emargements: List[Emargement]) -> Table:
        """Crée le tableau des signatures avec un style amélioré"""
        # En-têtes du tableau
        headers = ['Nom', 'Prénom', 'Email', 'Type de signature', 'Date de signature', 'Signature', 'Photo (si disponible)']
        data = [headers]
        
        # Données des participants
        for emargement in emargements:
            row = [
                emargement.nom if hasattr(emargement, 'nom') else "N/A",
                emargement.prenom if hasattr(emargement, 'prenom') else "N/A",
                emargement.email,
                "Présentiel" if emargement.mode_signature == "presentiel" else "À distance",
                emargement.date_signature.strftime('%d/%m/%Y %H:%M') if emargement.date_signature else "Non signé",
            ]
            
            # Gestion de la signature (en base64)
            signature_img = None
            if emargement.signature_image:
                signature_img = self._base64_to_image(emargement.signature_image)
            
            # Gestion de la photo (en base64, uniquement pour signature à distance)
            photo_img = None
            if emargement.mode_signature != "presentiel" and emargement.photo_profil:
                photo_img = self._base64_to_image(emargement.photo_profil)
            
            # Ajout des images au tableau
            row.append(Image(signature_img) if signature_img else "Non disponible")
            row.append(Image(photo_img) if photo_img else "Non disponible")
            
            data.append(row)
        
        # Création du tableau avec des largeurs de colonnes ajustées
        table = Table(data, colWidths=[
            3*cm,      # Nom
            3*cm,      # Prénom
            5*cm,      # Email
            3.5*cm,    # Type de signature
            3.5*cm,    # Date de signature
            3.5*cm,    # Signature
            3.5*cm     # Photo
        ])
        
        # Style du tableau amélioré
        table.setStyle(TableStyle([
            # Style des en-têtes
            ('BACKGROUND', (0, 0), (-1, 0), self.TABLE_HEADER_COLOR),
            ('TEXTCOLOR', (0, 0), (-1, 0), self.TABLE_HEADER_TEXT_COLOR),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), self.font_name),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 12),
            ('WORDWRAP', (0, 0), (-1, 0), True),
            
            # Bordures des en-têtes
            ('LINEBELOW', (0, 0), (-1, 0), 2, self.SECONDARY_COLOR),
            ('LINEABOVE', (0, 0), (-1, 0), 2, self.SECONDARY_COLOR),
            
            # Style du contenu
            ('BACKGROUND', (0, 1), (-1, -1), self.TABLE_ROW_COLOR),
            ('TEXTCOLOR', (0, 1), (-1, -1), self.PRIMARY_COLOR),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, self.BORDER_COLOR),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            
            # Alternance des couleurs de fond des lignes
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [self.TABLE_ROW_COLOR, self.TABLE_ALT_ROW_COLOR]),
            
            # Ajustements spécifiques
            ('FONTSIZE', (2, 1), (2, -1), 8),  # Email en plus petit
            ('WORDWRAP', (2, 1), (2, -1), True),  # Retour à la ligne pour l'email
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            
            # Bordures extérieures plus épaisses
            ('LINEABOVE', (0, 0), (-1, 0), 2, self.SECONDARY_COLOR),
            ('LINEBELOW', (0, -1), (-1, -1), 2, self.SECONDARY_COLOR),
            ('LINELEFT', (0, 0), (0, -1), 2, self.SECONDARY_COLOR),
            ('LINERIGHT', (-1, 0), (-1, -1), 2, self.SECONDARY_COLOR),
        ]))
        
        return table

    def _create_page_number(self, canvas, doc):
        """Crée le numéro de page et la date en bas de chaque page"""
        canvas.saveState()
        
        # Style pour le pied de page
        footer_style = ParagraphStyle(
            'Footer',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=self.PRIMARY_COLOR,
            alignment=TA_CENTER,
            spaceBefore=0,
            spaceAfter=0
        )
        
        # Créer le texte du pied de page avec uniquement le numéro de page actuel
        footer_text = f"Page {doc.page} | Document généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}"
        footer = Paragraph(footer_text, footer_style)
        
        # Calculer la position (en bas de la page)
        footer_width = footer.wrap(doc.width, doc.bottomMargin)[0]
        footer_height = footer.wrap(doc.width, doc.bottomMargin)[1]
        
        # Positionner le pied de page
        footer.drawOn(canvas, doc.leftMargin, footer_height + 0.5*cm)
        
        canvas.restoreState()

    def _on_page(self, canvas, doc):
        """Fonction appelée à chaque page pour créer le pied de page"""
        self._create_page_number(canvas, doc)

    def generate_signature_pdf(self, evenement: Evenement, emargements: List[Emargement]) -> BytesIO:
        """Génère le PDF final avec toutes les signatures"""
        buffer = BytesIO()
        
        # Créer le document avec la fonction de pied de page personnalisée
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(A4),
            rightMargin=1.5*cm,
            leftMargin=1.5*cm,
            topMargin=1.5*cm,
            bottomMargin=2*cm  # Augmenté pour accommoder le pied de page
        )
        
        # Création des éléments du document
        elements = []
        
        # Ajout de l'en-tête
        elements.extend(self._create_header(evenement))
        
        # Ajout du tableau des signatures
        elements.append(self._create_signature_table(emargements))
        
        # Génération du PDF avec la numérotation des pages
        doc.build(elements, onFirstPage=self._on_page, onLaterPages=self._on_page)
        buffer.seek(0)
        return buffer 