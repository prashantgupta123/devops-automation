"""Generate Excel report for enabled controls from input.json."""

import json
import xlsxwriter


def main(input_file: str = "input.json"):
    """Load input.json and generate Excel report for enabled controls."""
    with open(input_file, 'r') as f:
        config = json.load(f)
    
    workbook = xlsxwriter.Workbook('aws_enabled_controls_report.xlsx')
    
    header_format = workbook.add_format({
        'bold': True,
        'text_wrap': True,
        "align": "center",
        "valign": "vcenter",
        'fg_color': '#D7E4BC',
        'border': 1
    })
    
    cell_format = workbook.add_format({
        "text_wrap": True,
        "valign": "vcenter",
        "border": 1
    })
    
    enable_controls = config["controlTower"]["enableControls"]
    
    for behavior, behavior_config in enable_controls.items():
        worksheet = workbook.add_worksheet(behavior)
        worksheet.set_row(0, 30)
        
        headers = ['ARN', 'Aliases', 'Name', 'Description', 'Behavior', 'Severity']
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
            worksheet.set_column(col, col, 20)
        
        controls = behavior_config.get("controlIdentifiers", [])
        for row, control in enumerate(controls, 1):
            worksheet.write(row, 0, control.get('Arn', ''), cell_format)
            worksheet.write(row, 1, ', '.join(control.get('Aliases', [])), cell_format)
            worksheet.write(row, 2, control.get('Name', ''), cell_format)
            worksheet.write(row, 3, control.get('Description', ''), cell_format)
            worksheet.write(row, 4, control.get('Behavior', ''), cell_format)
            worksheet.write(row, 5, control.get('Severity', ''), cell_format)
    
    workbook.close()
    print("Excel report generated: aws_enabled_controls_report.xlsx")


if __name__ == "__main__":
    main()
