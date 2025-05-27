from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, Flowable
from PIL import Image as PILImage
import base64
import os
from app.schemas.schema_fiche_synthese import FicheSyntheseInput
from app.config import STATIC_DIR
from reportlab.pdfgen import canvas
from app.utils.formatting import format_milliers, diff_date_humaine

class BandeauLogos(Flowable):
    """Flowable personnalisé pour afficher plusieurs logos sur une ligne."""
    def __init__(self, logos, height=1.2*cm, padding=0.3*cm):
        super().__init__()
        self.logos = logos
        self.height = height
        self.padding = padding

    def draw(self):
        x = 0
        for logo_path in self.logos:
            if os.path.exists(logo_path):
                try:
                    img = PILImage.open(logo_path)
                    ratio = self.height / img.height
                    width = img.width * ratio
                    self.canv.drawImage(logo_path, x, 0, width=width, height=self.height, mask='auto')
                    x += width + self.padding
                except Exception as e:
                    pass

class FicheSynthesePDFGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.PRIMARY_COLOR = colors.HexColor('#000000')
        self.HEADER_COLOR = colors.HexColor('#f0f0f0')
        self.FIELD_BG = colors.HexColor('#e9ecef')
        self.BORDER_COLOR = colors.HexColor('#d1b000')
        self.logo_paths = [
            os.path.join(STATIC_DIR, f"logo{i}.png") for i in range(1, 7)
        ]
        self.logo_entreprise_path = os.path.join(STATIC_DIR, "logo.png")
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        self.styles.add(ParagraphStyle(
            name='TitreSynthese', fontSize=16, alignment=1, spaceAfter=8, leading=20, fontName='Helvetica-Bold', spaceBefore=0
        ))
        self.styles.add(ParagraphStyle(
            name='ChampNormal', fontSize=10, alignment=0, textColor=self.PRIMARY_COLOR, fontName='Helvetica'
        ))
        self.styles.add(ParagraphStyle(
            name='ChampLabel', fontSize=12, alignment=0, textColor=self.PRIMARY_COLOR, fontName='Helvetica-Bold'
        ))
        self.styles.add(ParagraphStyle(
            name='ChampValue', fontSize=10, alignment=0, textColor=self.PRIMARY_COLOR, fontName='Helvetica'
        ))
        self.styles.add(ParagraphStyle(
            name='SectionTitle', fontSize=11, alignment=0, spaceBefore=8, spaceAfter=4, fontName='Helvetica-Bold'
        ))
        self.styles.add(ParagraphStyle(
            name='ChampSaisie', fontSize=14, alignment=0, textColor=self.PRIMARY_COLOR, fontName='Helvetica'
        ))

    def _champ(self, label, value, width=5*cm):
        return [
            Paragraph(f"<b>{label}</b>", self.styles['ChampLabel']),
            Paragraph(value or "", self.styles['ChampValue'])
        ]

    def _champ_gris(self, value, width=16*cm, min_height=None, style_name='ChampValue'):
        t = Table(
            [[Paragraph(value or "", self.styles[style_name])]],
            colWidths=[width],
            rowHeights=[min_height] if min_height else None
        )
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#d9d9d9')),
            ('BOX', (0,0), (-1,-1), 1, colors.grey),
            ('LEFTPADDING', (0,0), (-1,-1), 4),
            ('RIGHTPADDING', (0,0), (-1,-1), 4),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        return t

    def _photo(self, photo_base64):
        try:
            image_data = base64.b64decode(photo_base64)
            image = PILImage.open(BytesIO(image_data))
            max_size = 3.5 * cm
            ratio = min(max_size/image.width, max_size/image.height)
            new_width = image.width * ratio
            new_height = image.height * ratio
            return Image(BytesIO(image_data), width=new_width, height=new_height)
        except Exception:
            return Paragraph("Photo non disponible", self.styles['ChampValue'])

    def _draw_footer(self, canv: canvas.Canvas, doc):
        page_num = f"Page {doc.page}/1"
        canv.setFont("Helvetica", 8)
        canv.setFillColor(colors.grey)
        canv.drawCentredString(A4[0]/2, 1.1*cm, page_num)

    def generate_pdf(self, data: FicheSyntheseInput) -> BytesIO:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=1.5*cm, leftMargin=1.5*cm, topMargin=1*cm, bottomMargin=1*cm)
        elements = []

        # Logo entreprise en haut à gauche
        if os.path.exists(self.logo_entreprise_path):
            try:
                img = PILImage.open(self.logo_entreprise_path)
                target_height = 1.5 * cm
                ratio = target_height / img.height
                target_width = img.width * ratio
                logo = Image(self.logo_entreprise_path, width=target_width, height=target_height)
                elements.append(logo)
            except Exception:
                pass
        else:
            elements.append(Spacer(1, 1*cm))

        # Bandeau logos (centré)
        elements.append(BandeauLogos(self.logo_paths, height=1.2*cm, padding=0.3*cm))
        elements.append(Spacer(1, 0.05*cm))
        # Titre très proche du haut
        elements.append(Paragraph(f"PROGRAMME {data.nom_programme}", self.styles['TitreSynthese']))
        elements.append(Paragraph("FICHE SYNTHETIQUE", self.styles['TitreSynthese']))
        elements.append(Table([['']], colWidths=[17*cm], rowHeights=[0.08*cm], style=[('LINEBELOW', (0,0), (-1,-1), 1, self.BORDER_COLOR)]))
        elements.append(Spacer(1, 0.08*cm))

        # Bloc principal : 2 colonnes (infos texte à gauche, photo à droite)
        # Sous-tableau horizontal à 2 colonnes pour les infos texte
        col1 = [
            Paragraph(f"<b>Nom : {data.nom} {data.prenom}</b>", self.styles['ChampNormal']),
            Spacer(1, 0.08*cm),
            Paragraph(f"<b>Contacts : {data.contact}</b>", self.styles['ChampNormal']),
            Spacer(1, 0.08*cm),
            Paragraph(f"<b>QPV : {data.qpv}</b>", self.styles['ChampNormal']),
            Spacer(1, 0.08*cm),
            Paragraph(f"<b>Siret : {data.siret}</b>", self.styles['ChampNormal']),
            Spacer(1, 0.08*cm),
            Paragraph(f"<b>Secteur : {data.secteur}</b>", self.styles['ChampNormal']),
            Spacer(1, 0.08*cm),
            Paragraph(f"<b>CA : {data.ca}</b>", self.styles['ChampNormal']),
            Spacer(1, 0.08*cm),
            Paragraph(f"<b>Entreprise : {data.entreprise}</b>", self.styles['ChampNormal']),
            Spacer(1, 0.08*cm),
            Paragraph(f"<b>Date de création : {data.date_creation} soit {diff_date_humaine(data.date_creation, unite='annees')}</b>", self.styles['ChampNormal']),
        ]
        
        infos_table = Table(
            [[col1]],
            colWidths=[15*cm],
            hAlign='LEFT',
            style=[
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('LEFTPADDING', (0,0), (-1,-1), 2),
                ('RIGHTPADDING', (0,0), (-1,-1), 2),
                ('TOPPADDING', (0,0), (-1,-1), 2),
                ('BOTTOMPADDING', (0,0), (-1,-1), 2),
            ]
        )
        col3 = [
            Spacer(1, 0.5*cm),
            self._photo(data.photo_base64),
            Spacer(1, 0.5*cm)
        ]
        bloc_table = Table(
            [[infos_table, col3]],
            colWidths=[13*cm, 7*cm],
            hAlign='LEFT',
            style=[
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('ALIGN', (1,0), (1,0), 'CENTER'),
                ('LEFTPADDING', (0,0), (-1,-1), 2),
                ('RIGHTPADDING', (0,0), (-1,-1), 2),
                ('TOPPADDING', (0,0), (-1,-1), 2),
                ('BOTTOMPADDING', (0,0), (-1,-1), 2),
            ]
        )
        elements.append(bloc_table)
        elements.append(Spacer(1, 0.15*cm))

        #Permet d'ajouter une ligne de séparation
        elements.append(Table(
            [['']],
            colWidths=[17*cm],  # Largeur totale souhaitée
            rowHeights=[0.08*cm],  # Hauteur très faible
            style=[('LINEBELOW', (0,0), (-1,-1), 1, self.BORDER_COLOR)]
        ))
        elements.append(Spacer(1, 0.4*cm))

        # Champs principaux (sans effet zone de texte)
        elements.append(Paragraph("1. Description Activité / Business Modèle Commerciale :", self.styles['ChampLabel']))
        elements.append(Spacer(1, 0.4*cm))
        elements.append(
            Table(
                [[Paragraph(f"{data.description_activite}", self.styles['ChampNormal'])]],
                colWidths=[18*cm],
                hAlign='LEFT',
                rowHeights=[3*cm],
                style=[
                    ('BACKGROUND', (0,0), (-1,-1), "#f0f0f0"),
                    ('BOX', (0,0), (-1,-1), 0.2, colors.black),  # ou retire cette ligne pour aucune bordure
                    ('LEFTPADDING', (0,0), (-1,-1), 4),
                    ('RIGHTPADDING', (0,0), (-1,-1), 4),
                    ('TOPPADDING', (0,0), (-1,-1), 6),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 6),
                    ('VALIGN', (0,0), (-1,-1), 'TOP'),   # Alignement vertical en haut
                    ('ALIGN', (0,0), (-1,-1), 'LEFT'),   # Alignement horizontal à gauche
                    ]
            )
        )
        
        elements.append(Spacer(1, 0.8*cm))
        elements.append(Paragraph(f"2. Prix de vente unitaire : {format_milliers(data.prix_vente_unitaire)} €", self.styles['ChampLabel']))
        elements.append(Spacer(1, 0.8*cm))

        elements.append(Paragraph("3. Coûts (Fixes, variables, revient) :", self.styles['ChampLabel']))
        elements.append(Spacer(1, 0.4*cm))
        # Entêtes du tableau
        headers = [
            Paragraph("<b>Coût de revient unitaire</b>", self.styles['ChampLabel']),
            Paragraph("<b>Coûts Fixes</b>", self.styles['ChampLabel']),
            Paragraph("<b>Coûts Variables</b>", self.styles['ChampLabel'])
        ]

        # Valeurs du tableau
        values = [
            Paragraph(f"{format_milliers(data.cout_revient_unitaire)} €", self.styles['ChampNormal']),
            Paragraph(f"{format_milliers(data.couts_fixes)} €", self.styles['ChampNormal']),
            Paragraph(f"{format_milliers(data.couts_variables)} €", self.styles['ChampNormal'])
        ]

        elements.append(
            Table(
                [headers, values],
                colWidths=[6*cm, 6*cm, 6*cm],
                style=[
                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f0f0f0')),  # Fond pour l'entête
                    ('BOX', (0,0), (-1,-1), 1, colors.black),
                    ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                    ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                    ('VALIGN', (0,0), (-1,-1), 'TOP'),
                    ('TOPPADDING', (0,0), (-1,-1), 6),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 6),
                    ('LEFTPADDING', (0,0), (-1,-1), 4),
                    ('RIGHTPADDING', (0,0), (-1,-1), 4),
                ]
            )
        )

        elements.append(Spacer(1, 0.8*cm))
        elements.append(Paragraph(f"4. Nombre d'unités à vendre pour être rentable (Seuil de rentabilité) : {format_milliers(data.seuil_rentabilite)} unités", self.styles['ChampLabel']))
        elements.append(Spacer(1, 0.8*cm))
        elements.append(Paragraph(f"5. Marge par unité : {format_milliers(data.marge_par_unite)} €", self.styles['ChampLabel']))
        elements.append(Spacer(1, 0.8*cm))
        elements.append(Paragraph(f"6. Localisation Adresse : {data.adresse}", self.styles['ChampLabel']))
        elements.append(Spacer(1, 0.8*cm))
        # 6. Carte (si présente)
        if hasattr(data, 'carte_base64') and data.carte_base64:
            try:
                carte_data = base64.b64decode(data.carte_base64)
                carte_img = PILImage.open(BytesIO(carte_data))
                max_width, max_height = 12*cm, 6*cm
                ratio = min(max_width/carte_img.width, max_height/carte_img.height)
                width, height = carte_img.width * ratio, carte_img.height * ratio
                elements.append(Paragraph("7. Carte :", self.styles['ChampNormal']))
                elements.append(Image(BytesIO(carte_data), width=width, height=height))
                elements.append(Spacer(1, 0.15*cm))
            except Exception as e:
                elements.append(Paragraph("Carte non disponible", self.styles['ChampNormal']))

        doc.build(elements, onFirstPage=self._draw_footer, onLaterPages=self._draw_footer)
        buffer.seek(0)
        return buffer

async def generate_fiche_synthese(data: FicheSyntheseInput) -> bytes:
    generator = FicheSynthesePDFGenerator()
    pdf_buffer = generator.generate_pdf(data)
    return pdf_buffer.getvalue() 