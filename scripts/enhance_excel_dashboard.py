"""
enhance_excel_dashboard.py
--------------------------
Enhances files/Sales_Dashboard.xlsx to meet all requirements of:
1. Excel / Google Sheets
   - Data Cleaning (CleanData vs RawData)
   - Sorting & Filtering
   - Conditional Formatting
   - Pivot Tables / Pivot Business Reporting
   - Charts (Monthly Trend, Category Breakdown, Regional Performance)
   - Lookup Functions (XLOOKUP, INDEX, MATCH, VLOOKUP)
   - Basic Business Reporting
"""

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.formatting.rule import ColorScaleRule

def enhance_workbook(file_path: str):
    wb = openpyxl.load_workbook(file_path)

    # Styles
    navy_header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
    soft_blue_fill = PatternFill(start_color="DBEAFE", end_color="DBEAFE", fill_type="solid")
    green_header_fill = PatternFill(start_color="065F46", end_color="065F46", fill_type="solid")
    soft_green_fill = PatternFill(start_color="D1FAE5", end_color="D1FAE5", fill_type="solid")
    card_bg_fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")

    font_title = Font(name="Calibri", size=14, bold=True, color="1E3A8A")
    font_section = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    font_bold = Font(name="Calibri", size=10, bold=True)
    font_regular = Font(name="Calibri", size=10)
    font_formula = Font(name="Consolas", size=9, italic=True, color="334155")

    thin_border = Border(
        left=Side(style='thin', color="CBD5E1"),
        right=Side(style='thin', color="CBD5E1"),
        top=Side(style='thin', color="CBD5E1"),
        bottom=Side(style='thin', color="CBD5E1")
    )

    # =========================================================================
    # 1. ENHANCE LOOKUP SHEET: XLOOKUP vs INDEX/MATCH vs VLOOKUP
    # =========================================================================
    ws_lookup = wb['Lookup']

    # Set Column widths
    ws_lookup.column_dimensions['F'].width = 28
    ws_lookup.column_dimensions['G'].width = 30
    ws_lookup.column_dimensions['I'].width = 28
    ws_lookup.column_dimensions['J'].width = 30

    # Header for XLOOKUP section
    ws_lookup.cell(1, 9, "XLOOKUP Demonstration").font = font_title
    ws_lookup.cell(2, 9, "ProductID Input").font = font_bold
    ws_lookup.cell(2, 9).fill = soft_blue_fill
    ws_lookup.cell(2, 10, "P004").font = font_bold
    ws_lookup.cell(2, 10).fill = soft_blue_fill
    ws_lookup.cell(2, 10).alignment = Alignment(horizontal="center")

    # XLOOKUP formulas
    ws_lookup.cell(3, 9, "Product Name (XLOOKUP)").font = font_bold
    ws_lookup.cell(3, 10, '=XLOOKUP(J2,A4:A18,B4:B18,"Not Found")').font = font_bold

    ws_lookup.cell(4, 9, "Category (XLOOKUP)").font = font_bold
    ws_lookup.cell(4, 10, '=XLOOKUP(J2,A4:A18,C4:C18,"Not Found")').font = font_regular

    ws_lookup.cell(5, 9, "Unit Price (XLOOKUP)").font = font_bold
    ws_lookup.cell(5, 10, '=XLOOKUP(J2,A4:A18,D4:D18,"Not Found")').font = font_regular
    ws_lookup.cell(5, 10).number_format = "$#,##0.00"

    # VLOOKUP formulas for comparison
    ws_lookup.cell(7, 9, "VLOOKUP Demonstration").font = font_title
    ws_lookup.cell(8, 9, "Product Name (VLOOKUP)").font = font_bold
    ws_lookup.cell(8, 10, '=VLOOKUP(J2,A4:D18,2,FALSE)').font = font_bold

    ws_lookup.cell(9, 9, "Category (VLOOKUP)").font = font_bold
    ws_lookup.cell(9, 10, '=VLOOKUP(J2,A4:D18,3,FALSE)').font = font_regular

    ws_lookup.cell(10, 9, "Unit Price (VLOOKUP)").font = font_bold
    ws_lookup.cell(10, 10, '=VLOOKUP(J2,A4:D18,4,FALSE)').font = font_regular
    ws_lookup.cell(10, 10).number_format = "$#,##0.00"

    # Explanatory notes
    ws_lookup.cell(12, 9, "Lookup Functions Comparison & When to Use:").font = font_bold
    notes = [
        "1. XLOOKUP: Modern Excel standard. Can look left or right, defaults to exact match, handles errors cleanly.",
        "2. INDEX / MATCH: Backward-compatible across all Excel versions & Sheets. Two-dimensional flexibility.",
        "3. VLOOKUP: Legacy standard. Searches only the first column left-to-right; requires hardcoded column index."
    ]
    for idx, note in enumerate(notes, start=13):
        ws_lookup.cell(idx, 9, note).font = font_formula

    # Apply borders
    for r in range(2, 6):
        ws_lookup.cell(r, 9).border = thin_border
        ws_lookup.cell(r, 10).border = thin_border
    for r in range(7, 11):
        ws_lookup.cell(r, 9).border = thin_border
        ws_lookup.cell(r, 10).border = thin_border

    # =========================================================================
    # 2. ENHANCE SUMMARY SHEET: CONDITIONAL FORMATTING
    # =========================================================================
    ws_summary = wb['Summary']

    # 3-color scale rule: Green (High Revenue), Yellow (Mid), Red/White (Low)
    color_scale = ColorScaleRule(
        start_type='min', start_color='FCA5A5', # soft red
        mid_type='percentile', mid_value=50, mid_color='FEF08A', # soft yellow
        end_type='max', end_color='86EFAC' # soft green
    )
    ws_summary.conditional_formatting.add("B8:B13", color_scale) # Regional Revenue
    ws_summary.conditional_formatting.add("F8:F11", color_scale) # Category Revenue
    ws_summary.conditional_formatting.add("B17:B28", color_scale) # Monthly Trend Revenue

    # =========================================================================
    # 3. ADD PIVOT BUSINESS REPORTING SHEET
    # =========================================================================
    if 'Pivot_Report' in wb.sheetnames:
        del wb['Pivot_Report']
    ws_pivot = wb.create_sheet('Pivot_Report')
    ws_pivot.views.sheetView[0].showGridLines = True

    # Title Banner
    ws_pivot.merge_cells('A1:G1')
    title_cell = ws_pivot.cell(1, 1, "Executive Sales Business Report — Pivot Matrix")
    title_cell.font = Font(name="Calibri", size=16, bold=True, color="FFFFFF")
    title_cell.fill = navy_header_fill
    title_cell.alignment = Alignment(horizontal="center", vertical="center")
    ws_pivot.row_dimensions[1].height = 35

    # Subtitle
    ws_pivot.cell(2, 1, "Cross-Tabulation: Revenue by Category & Geographic Region (Dynamic Pivot Formula Model)").font = font_formula

    # Pivot Matrix: Category x Region
    # Headers
    regions = ['Central', 'East', 'North', 'South', 'West']
    categories = ['Accessories', 'Electronics', 'Furniture', 'Stationery']

    ws_pivot.cell(4, 1, "Category").font = font_section
    ws_pivot.cell(4, 1).fill = navy_header_fill
    for col_idx, reg in enumerate(regions, start=2):
        cell = ws_pivot.cell(4, col_idx, reg)
        cell.font = font_section
        cell.fill = navy_header_fill
        cell.alignment = Alignment(horizontal="center")
    total_hdr = ws_pivot.cell(4, 7, "Grand Total")
    total_hdr.font = font_section
    total_hdr.fill = green_header_fill
    total_hdr.alignment = Alignment(horizontal="center")

    # Data rows
    for row_idx, cat in enumerate(categories, start=5):
        ws_pivot.cell(row_idx, 1, cat).font = font_bold
        ws_pivot.cell(row_idx, 1).border = thin_border
        for col_idx, reg in enumerate(regions, start=2):
            # Formula: SUMIFS on CleanData!$M$2:$M$851 where Category matches col A and Region matches row 4
            formula = f'=SUMIFS(CleanData!$M$2:$M$851,CleanData!$I$2:$I$851,$A{row_idx},CleanData!$E$2:$E$851,{openpyxl.utils.get_column_letter(col_idx)}$4)'
            c = ws_pivot.cell(row_idx, col_idx, formula)
            c.font = font_regular
            c.number_format = "$#,##0.00"
            c.border = thin_border
        # Row Total
        c_tot = ws_pivot.cell(row_idx, 7, f'=SUM(B{row_idx}:F{row_idx})')
        c_tot.font = font_bold
        c_tot.number_format = "$#,##0.00"
        c_tot.fill = soft_green_fill
        c_tot.border = thin_border

    # Grand Total row
    gt_row = 5 + len(categories)
    ws_pivot.cell(gt_row, 1, "Total Revenue").font = font_bold
    ws_pivot.cell(gt_row, 1).fill = soft_blue_fill
    ws_pivot.cell(gt_row, 1).border = thin_border
    for col_idx in range(2, 7):
        col_letter = openpyxl.utils.get_column_letter(col_idx)
        c = ws_pivot.cell(gt_row, col_idx, f'=SUM({col_letter}5:{col_letter}{gt_row-1})')
        c.font = font_bold
        c.number_format = "$#,##0.00"
        c.fill = soft_blue_fill
        c.border = thin_border
    gt_tot = ws_pivot.cell(gt_row, 7, f'=SUM(G5:G{gt_row-1})')
    gt_tot.font = Font(name="Calibri", size=11, bold=True, color="065F46")
    gt_tot.fill = soft_green_fill
    gt_tot.number_format = "$#,##0.00"
    gt_tot.border = thin_border

    # Second Section: Customer Segment Analysis
    seg_start = gt_row + 3
    ws_pivot.cell(seg_start, 1, "Customer Segment Performance").font = font_title
    seg_headers = ["Segment", "Order Count", "Total Revenue", "Avg Order Value", "% Share"]
    for idx, sh in enumerate(seg_headers, start=1):
        c = ws_pivot.cell(seg_start+1, idx, sh)
        c.font = font_section
        c.fill = navy_header_fill
        c.alignment = Alignment(horizontal="center" if idx > 1 else "left")

    segments = ["Consumer", "Corporate", "Small Business"]
    for s_idx, seg in enumerate(segments, start=seg_start+2):
        ws_pivot.cell(s_idx, 1, seg).font = font_bold
        ws_pivot.cell(s_idx, 1).border = thin_border

        # Orders
        c_ord = ws_pivot.cell(s_idx, 2, f'=COUNTIFS(CleanData!$F$2:$F$851,$A{s_idx})')
        c_ord.font = font_regular
        c_ord.number_format = "#,##0"
        c_ord.border = thin_border

        # Revenue
        c_rev = ws_pivot.cell(s_idx, 3, f'=SUMIFS(CleanData!$M$2:$M$851,CleanData!$F$2:$F$851,$A{s_idx})')
        c_rev.font = font_regular
        c_rev.number_format = "$#,##0.00"
        c_rev.border = thin_border

        # AOV
        c_aov = ws_pivot.cell(s_idx, 4, f'=C{s_idx}/B{s_idx}')
        c_aov.font = font_regular
        c_aov.number_format = "$#,##0.00"
        c_aov.border = thin_border

        # % Share
        c_pct = ws_pivot.cell(s_idx, 5, f'=C{s_idx}/$G${gt_row}')
        c_pct.font = font_regular
        c_pct.number_format = "0.0%"
        c_pct.border = thin_border

    # Segment Total
    s_tot_row = seg_start + 2 + len(segments)
    ws_pivot.cell(s_tot_row, 1, "Total").font = font_bold
    ws_pivot.cell(s_tot_row, 1).fill = soft_blue_fill
    ws_pivot.cell(s_tot_row, 1).border = thin_border

    c_tot_ord = ws_pivot.cell(s_tot_row, 2, f'=SUM(B{seg_start+2}:B{s_tot_row-1})')
    c_tot_ord.font = font_bold
    c_tot_ord.number_format = "#,##0"
    c_tot_ord.fill = soft_blue_fill
    c_tot_ord.border = thin_border

    c_tot_rev = ws_pivot.cell(s_tot_row, 3, f'=SUM(C{seg_start+2}:C{s_tot_row-1})')
    c_tot_rev.font = font_bold
    c_tot_rev.number_format = "$#,##0.00"
    c_tot_rev.fill = soft_blue_fill
    c_tot_rev.border = thin_border

    c_tot_aov = ws_pivot.cell(s_tot_row, 4, f'=C{s_tot_row}/B{s_tot_row}')
    c_tot_aov.font = font_bold
    c_tot_aov.number_format = "$#,##0.00"
    c_tot_aov.fill = soft_blue_fill
    c_tot_aov.border = thin_border

    c_tot_pct = ws_pivot.cell(s_tot_row, 5, f'=SUM(E{seg_start+2}:E{s_tot_row-1})')
    c_tot_pct.font = font_bold
    c_tot_pct.number_format = "0.0%"
    c_tot_pct.fill = soft_blue_fill
    c_tot_pct.border = thin_border

    # Column dimensions for Pivot_Report
    ws_pivot.column_dimensions['A'].width = 20
    ws_pivot.column_dimensions['B'].width = 16
    ws_pivot.column_dimensions['C'].width = 16
    ws_pivot.column_dimensions['D'].width = 16
    ws_pivot.column_dimensions['E'].width = 16
    ws_pivot.column_dimensions['F'].width = 16
    ws_pivot.column_dimensions['G'].width = 18

    # Apply Color scale to the Pivot Matrix numbers
    ws_pivot.conditional_formatting.add(f"B5:F{4+len(categories)}", color_scale)

    # Save
    wb.save(file_path)
    print(f"Successfully enhanced {file_path}")
    print(f"Current sheets: {wb.sheetnames}")

if __name__ == "__main__":
    enhance_workbook(r"l:\Bluestocks\files\Sales_Dashboard.xlsx")
