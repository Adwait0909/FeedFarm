"""Public animal-health screening routes for the unified farm application."""

import html
import io
import json
import re
import threading
from datetime import datetime
from pathlib import Path

from flask import Blueprint, current_app, jsonify, render_template, request, send_file
from PIL import Image, ImageOps, UnidentifiedImageError


animal_health_bp = Blueprint(
    "animal_health",
    __name__,
    url_prefix="/animal-health",
    template_folder="../animal_health_ai/templates",
    static_folder="../animal_health_ai/static",
    static_url_path="/static",
)

MODEL_PATH = (
    Path(__file__).resolve().parent.parent
    / "animal_health_ai"
    / "models"
    / "best_model.pth"
)

_model_bundle = None
_model_lock = threading.Lock()
_EMOJI_PATTERN = re.compile(
    "["
    "\U0001F300-\U0001FAFF"
    "\U00002600-\U000027BF"
    "\U0001F1E6-\U0001F1FF"
    "\U0001F900-\U0001F9FF"
    "\U00002B00-\U00002BFF"
    "]+",
    flags=re.UNICODE,
)


def _model():
    """Load the bundled, weights-only checkpoint on the first prediction."""
    global _model_bundle
    if _model_bundle is not None:
        return _model_bundle

    with _model_lock:
        if _model_bundle is not None:
            return _model_bundle
        if not MODEL_PATH.is_file():
            raise FileNotFoundError("Animal-health model is missing.")

        import torch
        import torch.nn as nn
        from torchvision import models, transforms

        checkpoint = torch.load(
            MODEL_PATH,
            map_location="cpu",
            weights_only=True,
        )
        classes = checkpoint.get("classes")
        if not isinstance(classes, (list, tuple)) or len(classes) < 2:
            raise ValueError("The model checkpoint has no valid class list.")

        model = models.resnet18(weights=None)
        model.fc = nn.Linear(model.fc.in_features, len(classes))
        model.load_state_dict(checkpoint["model_state_dict"])
        model.eval()

        image_size = int(checkpoint.get("image_size", 224))
        mean = checkpoint.get("normalization_mean")
        std = checkpoint.get("normalization_std")
        if mean is not None and std is not None:
            transform = transforms.Compose([
                transforms.Resize(256),
                transforms.CenterCrop(image_size),
                transforms.ToTensor(),
                transforms.Normalize(mean=mean, std=std),
            ])
        else:
            # The bundled checkpoint carries no normalisation metadata.  Its BatchNorm statistics show it was
            # trained on plain 0..1 pixels (no ImageNet mean/std); see
            # scripts/verify_animal_health_preprocessing.py.  Do not add Normalize() here unless the
            # checkpoint is replaced by one that records normalization_mean / normalization_std.
            transform = transforms.Compose([
                transforms.Resize((image_size, image_size)),
                transforms.ToTensor(),
            ])

        _model_bundle = (torch, model, list(classes), transform)
        return _model_bundle


def _read_image(upload):
    try:
        image = ImageOps.exif_transpose(Image.open(upload.stream)).convert("RGB")
        if image.width * image.height > 25_000_000:
            raise ValueError("Image is too large to process.")
        return image
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError, ValueError) as exc:
        raise ValueError("Please upload a valid image under 25 megapixels.") from exc


def _safe_text(value, limit=500):
    """Strip unsupported emoji and escape markup before ReportLab parses it."""
    text = _EMOJI_PATTERN.sub("", str(value or "")).strip()[:limit]
    return html.escape(text, quote=False)


def _json_list(value, max_items=20):
    try:
        parsed = json.loads(value or "[]")
    except (TypeError, json.JSONDecodeError):
        return []
    return parsed[:max_items] if isinstance(parsed, list) else []


@animal_health_bp.get("/")
def index():
    return render_template("animal_health.html")


@animal_health_bp.post("/predict")
def predict():
    upload = request.files.get("image")
    if upload is None or not upload.filename:
        return jsonify({"error": "Choose an image to analyze."}), 400

    try:
        image = _read_image(upload)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    try:
        torch, model, classes, transform = _model()
        with torch.inference_mode():
            scores = torch.softmax(model(transform(image).unsqueeze(0)), dim=1)[0]
        confidence, index = torch.max(scores, dim=0)
        return jsonify({
            "predicted_class": classes[index.item()],
            "confidence": float(confidence.item()),
            "all_scores": {classes[i]: float(scores[i]) for i in range(len(classes))},
        })
    except Exception:
        current_app.logger.exception("Animal-health prediction failed")
        return jsonify({
            "error": "The screening model is temporarily unavailable. Please try again later."
        }), 503


@animal_health_bp.post("/generate_report")
def generate_report():
    upload = request.files.get("image")
    if upload is None or not upload.filename:
        return jsonify({"error": "Choose an image to include in the report."}), 400
    try:
        image = _read_image(upload)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import inch
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.platypus import (
            Image as ReportImage,
            Paragraph,
            SimpleDocTemplate,
            Spacer,
            Table,
            TableStyle,
        )

        regular_font = animal_health_bp.root_path
        regular_font = Path(regular_font).parent / "animal_health_ai" / "static" / "fonts"
        font_regular = regular_font / "NotoSansDevanagari-Regular.ttf"
        font_bold = regular_font / "NotoSansDevanagari-Bold.ttf"
        report_font, report_font_bold = "Helvetica", "Helvetica-Bold"
        if font_regular.is_file() and font_bold.is_file():
            if "NotoDevanagari" not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont("NotoDevanagari", str(font_regular)))
                pdfmetrics.registerFont(TTFont("NotoDevanagari-Bold", str(font_bold)))
                pdfmetrics.registerFontFamily(
                    "NotoDevanagari",
                    normal="NotoDevanagari",
                    bold="NotoDevanagari-Bold",
                    italic="NotoDevanagari",
                    boldItalic="NotoDevanagari-Bold",
                )
            report_font, report_font_bold = "NotoDevanagari", "NotoDevanagari-Bold"

        form = request.form
        title = _safe_text(form.get("report_title", "Cattle Disease Detection Report"))
        generated_label = _safe_text(form.get("generated_label", "Generated on"))
        result_heading = _safe_text(form.get("result_heading", "Result"))
        display_name = _safe_text(form.get("display_name", ""))
        confidence_text = _safe_text(form.get("confidence_text", ""))
        confidence_label = _safe_text(form.get("confidence_label", "Confidence breakdown:"))
        is_healthy = form.get("is_healthy", "false") == "true"
        severity_heading = _safe_text(form.get("severity_heading", ""))
        severity_label = _safe_text(form.get("severity_label", ""))
        severity_message = _safe_text(form.get("severity_message", ""))
        info_heading = _safe_text(form.get("info_heading", ""))
        info_summary = _safe_text(form.get("info_summary", ""))
        disclaimer = _safe_text(form.get("disclaimer", ""))

        score_rows = []
        for row in _json_list(form.get("all_scores")):
            if isinstance(row, (list, tuple)) and len(row) >= 2:
                score_rows.append([_safe_text(row[0], 100), _safe_text(row[1], 40)])
        info_points = [
            _safe_text(point, 300)
            for point in _json_list(form.get("info_points"), max_items=12)
        ]

        image_buffer = io.BytesIO()
        image.save(image_buffer, format="JPEG", quality=90)
        image_buffer.seek(0)
        pdf_buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            pdf_buffer,
            pagesize=A4,
            topMargin=42,
            bottomMargin=42,
            leftMargin=48,
            rightMargin=48,
        )
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "AnimalTitle",
            parent=styles["Title"],
            fontName=report_font_bold,
            textColor=colors.HexColor("#1b5e20"),
        )
        heading_style = ParagraphStyle(
            "AnimalHeading",
            parent=styles["Heading2"],
            fontName=report_font_bold,
            textColor=colors.HexColor("#1b5e20"),
            spaceBefore=14,
            spaceAfter=6,
        )
        normal_style = ParagraphStyle(
            "AnimalNormal",
            parent=styles["Normal"],
            fontName=report_font,
        )
        disclaimer_style = ParagraphStyle(
            "AnimalDisclaimer",
            parent=normal_style,
            fontSize=8,
            textColor=colors.grey,
            spaceBefore=16,
        )

        story = [
            Paragraph(title, title_style),
            Paragraph(
                f"{generated_label}: {datetime.now().strftime('%d %b %Y, %I:%M %p')}",
                normal_style,
            ),
            Spacer(1, 14),
        ]
        max_width = 3.2 * inch
        story.extend([
            ReportImage(
                image_buffer,
                width=max_width,
                height=max_width * image.height / image.width,
            ),
            Spacer(1, 14),
            Paragraph(result_heading, heading_style),
            Paragraph(
                f'<font color="{"#1b5e20" if is_healthy else "#b71c1c"}">'
                f"<b>{display_name}</b></font> — {confidence_text}",
                normal_style,
            ),
            Spacer(1, 8),
            Paragraph(confidence_label, normal_style),
        ])
        table_data = [["", ""]] + score_rows
        score_table = Table(table_data, colWidths=[3.2 * inch, 1.8 * inch])
        score_table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), report_font),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2e7d32")),
            ("GRID", (0, 1), (-1, -1), 0.5, colors.HexColor("#c8e6c9")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f1f8f2")]),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(score_table)
        if severity_label:
            story.extend([
                Paragraph(f"{severity_heading}: {severity_label}", heading_style),
                Paragraph(severity_message, normal_style),
            ])
        if info_summary:
            story.extend([
                Paragraph(info_heading, heading_style),
                Paragraph(info_summary, normal_style),
            ])
            story.extend(Paragraph(f"• {point}", normal_style) for point in info_points)
        if disclaimer:
            story.append(Paragraph(disclaimer, disclaimer_style))

        doc.build(story)
        pdf_buffer.seek(0)
        return send_file(
            pdf_buffer,
            mimetype="application/pdf",
            as_attachment=True,
            download_name="cattle_disease_report.pdf",
        )
    except Exception:
        current_app.logger.exception("Animal-health report generation failed")
        return jsonify({"error": "The report could not be generated. Please try again."}), 500
