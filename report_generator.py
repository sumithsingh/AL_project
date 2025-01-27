# report_generator.py
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
        plt.figure(figsize=(8, 4))
        cell_types = list(test_results['cell_counts'].keys())
        counts = list(test_results['cell_counts'].values())
        
        plt.bar(cell_types, counts)
        plt.xticks(rotation=45)
        plt.ylabel('Percentage (%)')
        plt.title('Cell Type Distribution')
        
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', bbox_inches='tight')
        plt.close()
        
        return img_buffer.getvalue()

    def format_recommendations(self, recommendations):
        if isinstance(recommendations, list):
            return [Paragraph(f"• {rec}", self.normal_style) for rec in recommendations]
        return [Paragraph(f"• {recommendations}", self.normal_style)]

    def generate(self, test_data, patient_info=None):
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )

        # Story will contain all elements of the report
        story = []

        # Title
        story.append(Paragraph("Blood Cancer Analysis Report", self.title_style))
        story.append(Spacer(1, 12))

        # Patient Information
        if patient_info:
            story.append(Paragraph("Patient Information", self.heading_style))
            patient_data = [
                ["Name:", patient_info.get("name", "")],
                ["ID:", patient_info.get("id", "")],
                ["Age:", patient_info.get("age", "")],
                ["Date:", datetime.now().strftime("%Y-%m-%d")]
            ]
            patient_table = Table(patient_data, colWidths=[1.5*inch, 4*inch])
            patient_table.setStyle(TableStyle([
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('PADDING', (0, 0), (-1, -1), 6),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ]))
            story.append(patient_table)
            story.append(Spacer(1, 20))

        # Test Results
        story.append(Paragraph("Test Results", self.heading_style))

        for i, test in enumerate(test_data):
            # Test date
            story.append(Paragraph(
                f"Test Date: {test.date.strftime('%Y-%m-%d')}", 
                self.normal_style
            ))
            story.append(Spacer(1, 12))

            # Cell counts table
            cell_data = [["Cell Type", "Percentage"]]
            for cell_type, count in test.results['cell_counts'].items():
                cell_data.append([
                    cell_type.replace('_', ' ').title(),
                    f"{count:.1f}%"
                ])

            cell_table = Table(cell_data, colWidths=[3*inch, 2*inch])
            cell_table.setStyle(TableStyle([
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BACKGROUND', (0, 0), (0, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 12),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('PADDING', (0, 0), (-1, -1), 6)
            ]))
            story.append(cell_table)
            story.append(Spacer(1, 12))

            # Add cell distribution chart
            chart_data = self.create_cell_count_chart(test.results)
            img = Image(io.BytesIO(chart_data))
            img.drawHeight = 3*inch
            img.drawWidth = 6*inch
            story.append(img)
            story.append(Spacer(1, 12))

            # Risk Assessment
            story.append(Paragraph("Risk Assessment", self.heading_style))
            story.append(Paragraph(test.results['risk_assessment'], self.normal_style))
            story.append(Spacer(1, 12))

            # Recommendations
            story.append(Paragraph("Recommendations", self.heading_style))
            recommendations = self.format_recommendations(test.results['recommendations'])
            for rec in recommendations:
                story.append(rec)
                story.append(Spacer(1, 6))

            # Add page break between tests if not the last test
            if i < len(test_data) - 1:
                story.append(Spacer(1, 20))

        # Build PDF
        doc.build(story)
        pdf_content = buffer.getvalue()
        buffer.close()
        
        return pdf_content

    def generate_summary_report(self, test_data, patient_info=None):
        """Generate a summary report with trends"""
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
        story.append(Paragraph("Blood Cancer Analysis Summary Report", self.title_style))
        
        if test_data:
            # Create trend analysis
            dates = [test.date for test in test_data]
            cell_types = list(test_data[0].results['cell_counts'].keys())
            
            # Create trend chart
            plt.figure(figsize=(10, 6))
            for cell_type in cell_types:
                values = [test.results['cell_counts'][cell_type] for test in test_data]
                plt.plot(dates, values, marker='o', label=cell_type.title())
            
            plt.title('Cell Count Trends Over Time')
            plt.xlabel('Date')
            plt.ylabel('Percentage (%)')
            plt.legend()
            plt.xticks(rotation=45)
            
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', bbox_inches='tight')
            plt.close()
            
            img = Image(io.BytesIO(img_buffer.getvalue()))
            img.drawHeight = 4*inch
            img.drawWidth = 7*inch
            story.append(img)

        doc.build(story)
        pdf_content = buffer.getvalue()
        buffer.close()
        
        return pdf_content