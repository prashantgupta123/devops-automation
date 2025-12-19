import json
import xlsxwriter


def load_cost_data():
    """Load cost data from JSON file"""
    with open('cost_breakdown_by_region.json', 'r') as f:
        return json.load(f)


def create_excel_report():
    """Create Excel report with multiple sheets"""
    data = load_cost_data()
    
    # Create workbook
    workbook = xlsxwriter.Workbook('aws_cost_report.xlsx')
    
    # Define formats
    header_format = workbook.add_format({
        'bold': True,
        'text_wrap': True,
        'valign': 'top',
        'fg_color': '#D7E4BC',
        'border': 1
    })
    
    currency_format = workbook.add_format({'num_format': '$#,##0.00', 'border': 1})
    total_format = workbook.add_format({'bold': True, 'num_format': '$#,##0.00', 'fg_color': '#FFE6CC', 'border': 1})
    data_format = workbook.add_format({'border': 1})
    
    # Create summary sheet
    create_summary_sheet(workbook, data, header_format, currency_format, total_format, data_format)
    
    # Create regions sheet
    create_regions_sheet(workbook, data, header_format, currency_format, total_format, data_format)
    
    # Create services sheet
    create_services_sheet(workbook, data, header_format, currency_format, total_format, data_format)
    
    # Create individual account sheets
    create_account_sheets(workbook, data, header_format, currency_format, total_format, data_format)
    
    workbook.close()
    print("Excel report saved as aws_cost_report.xlsx")


def create_summary_sheet(workbook, data, header_format, currency_format, total_format, data_format):
    """Create summary sheet with account totals"""
    worksheet = workbook.add_worksheet('Summary')
    
    # Headers
    worksheet.write(0, 0, 'Total Accounts', header_format)
    worksheet.write(0, 1, len(data), data_format)
    
    total_cost = sum(account.get('total', 0) for account in data)
    worksheet.write(1, 0, 'Total Cost', header_format)
    worksheet.write(1, 1, total_cost, total_format)
    
    # Account details sorted by cost
    worksheet.write(3, 0, 'Account ID', header_format)
    worksheet.write(3, 1, 'Account Name', header_format)
    worksheet.write(3, 2, 'Total Cost', header_format)
    
    sorted_accounts = sorted(data, key=lambda x: x.get('total', 0), reverse=True)
    
    for i, account in enumerate(sorted_accounts, 4):
        worksheet.write_string(i, 0, str(account['accountId']), data_format)
        worksheet.write(i, 1, account['accountName'], data_format)
        worksheet.write(i, 2, account.get('total', 0), currency_format)
    
    worksheet.set_column(0, 0, 20)
    worksheet.set_column(1, 1, 30)
    worksheet.set_column(2, 2, 20)


def create_regions_sheet(workbook, data, header_format, currency_format, total_format, data_format):
    """Create regions sheet with cost by region for each account"""
    worksheet = workbook.add_worksheet('Regions')
    
    # Get all unique regions and calculate totals
    region_totals = {}
    for account in data:
        for region, cost in account.get('regions', {}).items():
            region_totals[region] = region_totals.get(region, 0) + cost
    
    # Sort regions by total cost descending
    all_regions = sorted(region_totals.keys(), key=lambda x: region_totals[x], reverse=True)
    
    # Headers
    worksheet.write(0, 0, 'Account ID', header_format)
    worksheet.write(0, 1, 'Account Name', header_format)
    for i, region in enumerate(all_regions, 2):
        worksheet.write(0, i, region, header_format)
    
    # Data rows
    for row, account in enumerate(data, 1):
        worksheet.write_string(row, 0, str(account['accountId']), data_format)
        worksheet.write(row, 1, account['accountName'], data_format)
        for col, region in enumerate(all_regions, 2):
            cost = account.get('regions', {}).get(region, 0)
            worksheet.write(row, col, cost, currency_format if cost > 0 else data_format)
    
    # Total row
    total_row = len(data) + 1
    worksheet.write(total_row, 0, 'TOTAL', total_format)
    worksheet.write(total_row, 1, '', total_format)
    
    for col, region in enumerate(all_regions, 2):
        total = sum(account.get('regions', {}).get(region, 0) for account in data)
        worksheet.write(total_row, col, total, total_format)
    
    worksheet.set_column(0, 0, 20)
    worksheet.set_column(1, 1, 30)
    worksheet.set_column(2, 2 + len(all_regions), 20)


def create_services_sheet(workbook, data, header_format, currency_format, total_format, data_format):
    """Create services sheet with cost by service for each account"""
    worksheet = workbook.add_worksheet('Services')
    
    # Get all unique services and calculate totals
    service_totals = {}
    for account in data:
        for service, cost in account.get('services', {}).items():
            service_totals[service] = service_totals.get(service, 0) + cost
    
    # Sort services by total cost descending
    all_services = sorted(service_totals.keys(), key=lambda x: service_totals[x], reverse=True)
    
    # Headers
    worksheet.write(0, 0, 'Account ID', header_format)
    worksheet.write(0, 1, 'Account Name', header_format)
    for i, service in enumerate(all_services, 2):
        worksheet.write(0, i, service, header_format)
    
    # Data rows
    for row, account in enumerate(data, 1):
        worksheet.write_string(row, 0, str(account['accountId']), data_format)
        worksheet.write(row, 1, account['accountName'], data_format)
        for col, service in enumerate(all_services, 2):
            cost = account.get('services', {}).get(service, 0)
            worksheet.write(row, col, cost, currency_format if cost > 0 else data_format)
    
    # Total row
    total_row = len(data) + 1
    worksheet.write(total_row, 0, 'TOTAL', total_format)
    worksheet.write(total_row, 1, '', total_format)
    
    for col, service in enumerate(all_services, 2):
        total = sum(account.get('services', {}).get(service, 0) for account in data)
        worksheet.write(total_row, col, total, total_format)
    
    worksheet.set_column(0, 0, 20)
    worksheet.set_column(1, 1, 30)
    worksheet.set_column(2, 2 + len(all_services), 20)


def create_account_sheets(workbook, data, header_format, currency_format, total_format, data_format):
    """Create individual sheets for each account"""
    for account in data:
        sheet_name = f"{account['accountId']}"
        worksheet = workbook.add_worksheet(sheet_name)
        
        # Account info
        worksheet.write(0, 0, 'Account ID', header_format)
        worksheet.write_string(0, 1, str(account['accountId']), data_format)
        worksheet.write(1, 0, 'Account Name', header_format)
        worksheet.write(1, 1, account['accountName'], data_format)
        worksheet.write(2, 0, 'Total Cost', header_format)
        worksheet.write(2, 1, account.get('total', 0), total_format)
        
        # Regions section
        worksheet.write(4, 0, 'REGIONS', header_format)
        worksheet.write(5, 0, 'Region', header_format)
        worksheet.write(5, 1, 'Cost', header_format)
        
        row = 6
        for region, cost in account.get('regions', {}).items():
            worksheet.write(row, 0, region, data_format)
            worksheet.write(row, 1, cost, currency_format)
            row += 1
        
        # Services section
        row += 2
        worksheet.write(row, 0, 'SERVICES', header_format)
        worksheet.write(row + 1, 0, 'Service', header_format)
        worksheet.write(row + 1, 1, 'Cost', header_format)
        
        row += 2
        for service, cost in account.get('services', {}).items():
            worksheet.write(row, 0, service, data_format)
            worksheet.write(row, 1, cost, currency_format)
            row += 1
        
        # Region Services section
        row += 2
        worksheet.write(row, 0, 'REGION SERVICES', header_format)
        worksheet.write(row + 1, 0, 'Region', header_format)
        worksheet.write(row + 1, 1, 'Service', header_format)
        worksheet.write(row + 1, 2, 'Cost', header_format)
        
        row += 2
        for region, services in account.get('regionServices', {}).items():
            for service, cost in services.items():
                worksheet.write(row, 0, region, data_format)
                worksheet.write(row, 1, service, data_format)
                worksheet.write(row, 2, cost, currency_format)
                row += 1
        
        worksheet.set_column(0, 0, 40)
        worksheet.set_column(1, 1, 40)
        worksheet.set_column(2, 2, 20)


if __name__ == "__main__":
    create_excel_report()
