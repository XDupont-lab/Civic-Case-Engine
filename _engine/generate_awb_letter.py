# -*- coding: utf-8 -*-
"""
generate_awb_letter.py
CivicHelper / CIVIC HELPER Tool
Genereert strakke, formele 1-pagina A4 PDF-brieven voor het bestuursrecht (Awb / AVG).
Geschikt voor vensterenveloppen en directe upload naar online postdiensten (briefverzenden.nl, postbode.nu).
Borging: dwingt exact 1 pagina A4 af via pypdf verificatie.
"""

import sys
import hashlib
from pathlib import Path
from typing import List, Tuple, Optional
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
import pypdf

def _load_default_sender_and_footer():
    dossier_profile = Path(__file__).resolve().parent.parent / "Dossier" / "profile.json"
    if dossier_profile.exists():
        try:
            p = json.loads(dossier_profile.read_text(encoding="utf-8"))
            name = p.get("name", "Burger")
            address = p.get("address", "")
            pc = p.get("postal_code", "")
            res = p.get("residence", "")
            mail = p.get("email", "")
            parts = [x for x in [name, address, f"{pc} {res}".strip(), mail] if x]
            sender = " &bull; ".join(f"<b>{parts[0]}</b>" if i == 0 else parts[i] for i in range(len(parts)))
            footer = (
                f"Hoogachtend,<br/><br/>"
                f"<b>{name}</b><br/>"
                f"{address}, {pc} {res}<br/>"
                "<i>(Communicatie-invariant conform VN-verdrag Handicap: uitsluitend schriftelijk)</i>"
            )
            return sender, footer
        except Exception:
            pass
    return (
        "<b>[Naam Burger]</b> &bull; [Straat + Huisnummer] &bull; [Postcode Woonplaats] &bull; [e-mail]",
        "Hoogachtend,<br/><br/><b>[Naam Burger]</b><br/>[Straat + Huisnummer], [Postcode Woonplaats]<br/><i>(Communicatie-invariant conform VN-verdrag Handicap: uitsluitend schriftelijk)</i>"
    )

DEFAULT_SENDER, DEFAULT_FOOTER = _load_default_sender_and_footer()

def create_awb_letter(
    out_path: Path,
    recipient_html: str,
    meta_pairs: List[Tuple[str, str]],
    subject: str,
    opening_text: str,
    bullets: List[str],
    closing_text: str,
    sender_html: str = DEFAULT_SENDER,
    signature_html: str = DEFAULT_FOOTER
) -> Path:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(out_path),
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm
    )

    styles = getSampleStyleSheet()

    style_sender = ParagraphStyle(
        'SenderSmall',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#555555')
    )
    style_recipient = ParagraphStyle(
        'RecipientBlock',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13,
        textColor=colors.black
    )
    style_meta = ParagraphStyle(
        'MetaText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor('#222222')
    )
    style_title = ParagraphStyle(
        'SubjectTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13.5,
        textColor=colors.black
    )
    style_body = ParagraphStyle(
        'BodyCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11.5,
        textColor=colors.black
    )
    style_bullet = ParagraphStyle(
        'BulletCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10.8,
        leftIndent=10,
        textColor=colors.HexColor('#111111')
    )
    style_sign = ParagraphStyle(
        'SignCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11.5,
        textColor=colors.black
    )

    story = []

    # 1. Afzenderstrook
    story.append(Paragraph(sender_html, style_sender))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#CCCCCC'), spaceBefore=2*mm, spaceAfter=5*mm))

    # 2. Geadresseerde
    story.append(Paragraph(recipient_html, style_recipient))
    story.append(Spacer(1, 4 * mm))

    # 3. Kenmerken
    table_rows = []
    for i in range(0, len(meta_pairs), 2):
        col1 = Paragraph(f"<b>{meta_pairs[i][0]}:</b> {meta_pairs[i][1]}", style_meta)
        if i + 1 < len(meta_pairs):
            col2 = Paragraph(f"<b>{meta_pairs[i+1][0]}:</b> {meta_pairs[i+1][1]}", style_meta)
        else:
            col2 = Paragraph("", style_meta)
        table_rows.append([col1, col2])

    if table_rows:
        meta_table = Table(table_rows, colWidths=[85*mm, 85*mm])
        meta_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 1),
            ('TOPPADDING', (0,0), (-1,-1), 0),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 3 * mm))

    # 4. Onderwerp
    story.append(Paragraph(f"<b>Betreft: {subject}</b>", style_title))
    story.append(Spacer(1, 2.5 * mm))

    # 5. Opening
    story.append(Paragraph(opening_text, style_body))
    story.append(Spacer(1, 1.5 * mm))

    # 6. Kernpunten / Bullets
    for b in bullets:
        story.append(Paragraph(b, style_bullet))
        story.append(Spacer(1, 1 * mm))

    # 7. Slotpassage
    if closing_text:
        story.append(Spacer(1, 1 * mm))
        story.append(Paragraph(closing_text, style_body))

    # 8. Ondertekening
    story.append(Spacer(1, 2.5 * mm))
    story.append(Paragraph(signature_html, style_sign))

    # Bouw PDF
    doc.build(story)

    # Verifieer exacte paginalengte (1 pagina)
    reader = pypdf.PdfReader(str(out_path))
    num_pages = len(reader.pages)
    if num_pages != 1:
        raise ValueError(f"Constraint geschonden: PDF telt {num_pages} pagina's in plaats van 1! Verkort de tekst.")

    sha256 = hashlib.sha256(out_path.read_bytes()).hexdigest()
    print(f"[OK] A4 Brief gegenereerd: {out_path} (Exact 1 pagina, SHA-256: {sha256[:12]}...)")
    return out_path

if __name__ == "__main__":
    print("generate_awb_letter.py: Modulaire PDF briefgenerator voor CivicHelper geladen.")
