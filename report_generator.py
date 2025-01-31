import logging
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import matplotlib.pyplot as plt
import io
from datetime import datetime

class ReportGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=20,
            spaceAfter=20
        )
        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=10
        )
        self.normal_style = self.styles['Normal']

    def create_cell_count_chart(self, test_results):
        """Generates a bar chart for cell count distribution."""
        cell_counts = test_results.get("cell_counts", {})

        if not cell_counts:
            logging.warning("⚠ No cell counts available for chart generation.")
            return None

        plt.figure(figsize=(6, 3))
        cell_types = list(cell_counts.keys())
        counts = list(cell_counts.values())

        plt.bar(cell_types, counts, color='skyblue')
        plt.xticks(rotation=45)
        plt.ylabel("Percentage (%)")
        plt.title("Cell Type Distribution")

        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format="png", bbox_inches="tight")
        plt.close()
        return img_buffer

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
            story.append(Paragraph(f"👤 Patient Name: {patient_info.get('name', 'Unknown')}", self.heading_style))
            story.append(Paragraph(f"🆔 Patient ID: {patient_info.get('id', 'Unknown')}", self.heading_style))
            story.append(Spacer(1, 12))

        # Test Results
        story.append(Paragraph("🩺 Test Results", self.heading_style))

        for test in test_data:
            date = test.get("details", {}).get("analysis_date", "Unknown")
            risk_assessment = test.get("risk_assessment", "Unknown")
            confidence_score = test.get("details", {}).get("confidence_score", 0)

            story.append(Paragraph(f"📅 Test Date: {date}", self.normal_style))
            story.append(Paragraph(f"📌 Risk Assessment: {risk_assessment}", self.normal_style))
            story.append(Paragraph(f"🎯 Confidence Score: {confidence_score:.1f}%", self.normal_style))
            story.append(Spacer(1, 10))

            # Blood Cell Counts
            cell_counts = test.get("cell_counts", {})
            if cell_counts:
                table_data = [["Cell Type", "Percentage (%)"]] + [[cell, f"{value:.2f}%"] for cell, value in cell_counts.items()]
                table = Table(table_data, colWidths=[200, 100])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ]))
                story.append(Paragraph("📊 Blood Cell Count Distribution", self.heading_style))
                story.append(table)
                story.append(Spacer(1, 12))

                # Generate Chart
                img_buffer = self.create_cell_count_chart(test)
                if img_buffer:
                    img_buffer.seek(0)
                    chart = Image(img_buffer, width=5 * inch, height=3 * inch)
                    story.append(chart)
                    story.append(Spacer(1, 12))

            # Recommendations
            recommendations = test.get("recommendations", [])
            story.append(Paragraph("📝 Recommendations", self.heading_style))
            story.extend(self.format_recommendations(recommendations))
            story.append(Spacer(1, 12))

        # Build PDF
        doc.build(story)
        pdf_content = buffer.getvalue()
        buffer.close()

        return pdf_content
