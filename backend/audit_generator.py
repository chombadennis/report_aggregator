from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
import os
from datetime import datetime

class AuditReportGenerator:
    def __init__(self):
        pass

    def generate_report(self, output_path, data, insights, financials=None):
        doc = Document()
        
        # --- COVER PAGE ---
        self._add_cover_page(doc, data)
        
        # --- EXECUTIVE SUMMARY ---
        doc.add_page_break()
        self._add_heading(doc, "1.0 EXECUTIVE SUMMARY", level=1)
        doc.add_paragraph(insights.get("executive_summary", "No summary available."))
        
        # --- RECALIBRATION EXECUTIVE AUDIT (VERBATIM REQUIREMENT) ---
        self._add_heading(doc, "1.1 RECALIBRATION EXECUTIVE AUDIT", level=2)
        
        # Extract months with fallback to last two records
        m_list = financials.get("monthly_financials", []) if financials else []
        completed_month = None
        ongoing_month = None
        
        if len(m_list) >= 2:
            # Usually the last one is ongoing, the one before is completed
            ongoing_month = m_list[-1]
            completed_month = m_list[-2]
        elif len(m_list) == 1:
            ongoing_month = m_list[0]
            
        latest_week = financials.get("weekly_financials", [{}])[-1] if financials else {}
        variance = abs(latest_week.get("variance", 0))
        
        p = doc.add_paragraph()
        if completed_month and ongoing_month:
            p.add_run(f"Analysis shows that in {completed_month.get('month', 'April 2026')}, the project achieved {completed_month.get('actual_production', 0):.2f}% production against an envisaged {completed_month.get('envisaged_production', 0):.2f}%. ").bold = False
            p.add_run(f"The cumulative variance is now {variance:.2f}% behind the project baseline. ").bold = True
            p.add_run(f"To hit 100% completion by Nov 24, 2027, the contractor must maintain a velocity of {ongoing_month.get('required_weekly', 0):.2f}% per week for the remainder of {ongoing_month.get('month', 'May 2026')}.")
        else:
            p.add_run("Recalibration data is still initializing for the current period. Baseline linear tracking remains at 0.96% per week.")

        # P.S. Section
        doc.add_paragraph("")
        ps_p = doc.add_paragraph()
        run = ps_p.add_run("P.S. Mathematical Logic:")
        run.bold = True
        run.underline = True
        
        pct_time = latest_week.get("pct_time", 0)
        pct_work = latest_week.get("pct_work", 0)
        req_weekly = ongoing_month.get('required_weekly', 0) if ongoing_month else 0.96
        m_name = ongoing_month.get('month', 'May 2026') if ongoing_month else 'Current Month'
        
        doc.add_paragraph(
            f"The {variance:.2f}% variance is the cumulative \"Slippage Gap.\" "
            f"By {m_name}, {pct_time:.2f}% of the project time has elapsed, "
            f"but only {pct_work:.2f}% of work is done. This {variance:.2f}% backlog is the total deficit "
            f"that has shifted the required weekly production rate from the original 0.96% to the current "
            f"{req_weekly:.2f}%."
        )
        
        # --- MONTHLY PRODUCTION CALIBRATION ---
        if financials and financials.get("monthly_financials"):
            doc.add_page_break()
            self._add_heading(doc, "2.0 MONTHLY PRODUCTION CALIBRATION", level=1)
            
            # Monthly Table
            m_table = doc.add_table(rows=1, cols=6)
            m_table.style = 'Table Grid'
            hdr = m_table.rows[0].cells
            for idx, text in enumerate(["Month", "Start %", "End %", "Actual (x)", "Envisaged (y)", "Variance (k)"]):
                hdr[idx].text = text
                hdr[idx].paragraphs[0].runs[0].bold = True
            
            for m in financials["monthly_financials"]:
                # ONLY show completed months in the historical comparison table
                if m.get("is_ongoing"):
                    continue
                    
                row = m_table.add_row().cells
                row[0].text = m["month"]
                row[1].text = f"{m['start_pct']:.2f}%"
                row[2].text = f"{m['end_pct']:.2f}%"
                row[3].text = f"{m['actual_production']:.2f}%"
                row[4].text = f"{m['envisaged_production']:.2f}%"
                row[5].text = f"{m['variance']:+.2f}%"

            # Add ongoing target note
            ongoing = financials["monthly_financials"][-1]
            if ongoing.get("is_ongoing"):
                p = doc.add_paragraph()
                run = p.add_run(f"\nONGOING CALIBRATION ({ongoing['month']}):")
                run.bold = True
                doc.add_paragraph(f"The project is currently tracking at {ongoing['end_pct']:.2f}% progress. To hit the required milestone by {ongoing['month']} 31st, the target is {ongoing.get('target_this_month_end', 0):.2f}% progress, requiring a recalibrated velocity of {ongoing['required_weekly']:.2f}% per week.")

        # --- RECALIBRATION CHAIN ---
        if financials and financials.get("weekly_financials"):
            self._add_heading(doc, "3.0 PRODUCTION RECALIBRATION CHAIN (WEEKLY AUDIT)", level=1)
            doc.add_paragraph("Tactical weekly performance variance (k) based on dynamic recalibration.")
            
            w_table = doc.add_table(rows=1, cols=5)
            w_table.style = 'Table Grid'
            hdr = w_table.rows[0].cells
            for idx, text in enumerate(["Reporting Week", "Actual (x)", "Envisaged (y)", "Variance (k)", "Next Target"]):
                hdr[idx].text = text
                hdr[idx].paragraphs[0].runs[0].bold = True
                
            for w in financials["weekly_financials"]:
                row = w_table.add_row().cells
                row[0].text = w["label"]
                row[1].text = f"{w['weekly_actual']:.2f}%"
                row[2].text = f"{w['weekly_envisaged']:.2f}%"
                row[3].text = f"{w['weekly_variance']:+.2f}%"
                row[4].text = f"{w['required_future_rate']:.2f}%"

        # --- SWOT ANALYSIS ---
        doc.add_page_break()
        self._add_heading(doc, "4.0 SWOT & PERFORMANCE INTELLIGENCE", level=1)
        
        swot = insights.get("swot", {})
        sections = [
            ("STRENGTHS", swot.get("strengths", []), "008000"), # Green
            ("WEAKNESSES", swot.get("weaknesses", []), "FF0000"), # Red
            ("OPPORTUNITIES", swot.get("opportunities", []), "FFA500"), # Orange
            ("THREATS", swot.get("threats", []), "0000FF") # Blue
        ]
        
        for title, items, color in sections:
            p = doc.add_paragraph()
            run = p.add_run(title)
            run.bold = True
            run.font.color.rgb = RGBColor.from_string(color)
            
            if not items:
                doc.add_paragraph("No items identified.")
            else:
                for item in items:
                    doc.add_paragraph(item, style='List Bullet')
            doc.add_paragraph("")

        # --- STRATEGIC RECOMMENDATIONS ---
        doc.add_page_break()
        self._add_heading(doc, "5.0 STRATEGIC RECOMMENDATIONS", level=1)
        
        recs = insights.get("recommendations", {})
        
        self._add_heading(doc, "5.1 TO THE CLIENT (PM)", level=2)
        for item in recs.get("to_client", ["No recommendations available."]):
            doc.add_paragraph(item, style='List Bullet')
            
        self._add_heading(doc, "5.2 TO THE CONTRACTOR", level=2)
        for item in recs.get("to_contractor", ["No recommendations available."]):
            doc.add_paragraph(item, style='List Bullet')

        # --- CLOSING ---
        doc.add_paragraph("\n\nReport generated by Construction Aggregator.")
        doc.add_paragraph(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        doc.save(output_path)
        return output_path

    def _add_cover_page(self, doc, data):
        # Center alignment for cover
        for i in range(10): doc.add_paragraph() # Spacer
        
        title = doc.add_paragraph("PROJECT AUDIT & RISK INTELLIGENCE REPORT")
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = title.runs[0]
        run.bold = True
        run.font.size = Pt(24)
        run.font.color.rgb = RGBColor(47, 84, 150) # Dark Blue
        
        subtitle = doc.add_paragraph("Tactical Site Performance Analysis")
        subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
        subtitle.runs[0].font.size = Pt(14)
        
        for i in range(5): doc.add_paragraph() # Spacer
        
        info = doc.add_paragraph(f"Generated for: Makindu Affordable Housing Project")
        info.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        date_para = doc.add_paragraph(f"Report Date: {datetime.now().strftime('%B %d, %Y')}")
        date_para.alignment = WD_ALIGN_PARAGRAPH.CENTER

    def _add_heading(self, doc, text, level=1):
        h = doc.add_heading(text, level=level)
        # Custom styling could be added here

    def _calculate_slippage(self, trend):
        try:
            time = float(trend.get('time_progress', 0))
            work = float(trend.get('financial_progress', 0))
            return round(time - work, 2)
        except:
            return 0
