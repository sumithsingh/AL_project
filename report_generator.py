import logging
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import matplotlib.pyplot as plt
import io
from datetime import datetime
import numpy as np

class ReportGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30
        )
        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceAfter=12
        )
        self.normal_style = self.styles['Normal']

    def create_cell_count_chart(self, test_results):
        """Generates a bar chart for cell count distribution."""
        cell_counts = test_results.get("cell_counts", {})

        if not cell_counts:
            logging.warning("No cell counts available for chart generation.")
            return None

        plt.figure(figsize=(8, 4))
        cell_types = list(cell_counts.keys())
        counts = list(cell_counts.values())

        plt.bar(cell_types, counts, color='skyblue')
        plt.xticks(rotation=45)
        plt.ylabel("Percentage (%)")
        plt.title("Cell Type Distribution")

        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format="png", bbox_inches="tight")
        plt.close()

        return img_buffer.getvalue()

    def format_recommendations(self, recommendations):
        """Formats recommendations as bullet points."""
        if not recommendations:
            recommendations = ["No specific recommendations."]
        if isinstance(recommendations, list):
            return [Paragraph(f"• {rec}", self.normal_style) for rec in recommendations]
        return [Paragraph(f"• {recommendations}", self.normal_style)]

    def generate(self, test_data, patient_info=None):
        """Generates a detailed PDF report for test results."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )

        story = []

        # Title
        story.append(Paragraph("Blood Cancer Analysis Report", self.title_style))
        story.append(Spacer(1, 12))

        # Patient Information
        if patient_info:
            story.append(Paragraph(f"Patient Name: {patient_info.get('name', 'Unknown')}", self.heading_style))
            story.append(Paragraph(f"Patient ID: {patient_info.get('id', 'Unknown')}", self.heading_style))
            story.append(Spacer(1, 12))

        # Test Results
        story.append(Paragraph("Test Results", self.heading_style))

        for test in test_data:
            date = test.get("details", {}).get("analysis_date", "Unknown")
            risk_assessment = test.get("risk_assessment", "Unknown")
            confidence_score = test.get("details", {}).get("confidence_score", 0)

            story.append(Paragraph(f"Test Date: {date}", self.normal_style))
            story.append(Paragraph(f"Risk Assessment: {risk_assessment}", self.normal_style))
            story.append(Paragraph(f"Confidence Score: {confidence_score:.1f}%", self.normal_style))
            story.append(Spacer(1, 12))

        # Build PDF
        doc.build(story)
        pdf_content = buffer.getvalue()
        buffer.close()

        return pdf_content
