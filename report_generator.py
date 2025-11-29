#!/usr/bin/env python3
"""
Automated Reporting System for Credential Discovery
Generates comprehensive reports from all discovery tools
"""

import json
import os
import time
from datetime import datetime
import base64
import hashlib
from urllib.parse import urlparse
import re

class ReportGenerator:
    def __init__(self):
        self.reports_dir = "reports"
        if not os.path.exists(self.reports_dir):
            os.makedirs(self.reports_dir)
    
    def load_json_data(self, filepath):
        """Load JSON data from file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading {filepath}: {e}")
            return None
    
    def analyze_credentials(self, results):
        """Analyze credential findings for risk assessment"""
        risks = {
            'high': [],
            'medium': [],
            'low': [],
            'info': []
        }
        
        for result in results:
            title = result.get('title', '').lower()
            snippet = result.get('snippet', '').lower()
            link = result.get('link', '')
            
            combined_text = f"{title} {snippet}"
            
            # High risk patterns
            high_risk_patterns = [
                'password', 'secret_key', 'private_key', 'access_token',
                'aws_access', 'stripe_key', 'github_token', 'database_password'
            ]
            
            # Medium risk patterns
            medium_risk_patterns = [
                'config', 'api_key', 'admin', 'root', 'auth_token',
                'oauth', 'jwt', 'session'
            ]
            
            if any(pattern in combined_text for pattern in high_risk_patterns):
                risks['high'].append(result)
            elif any(pattern in combined_text for pattern in medium_risk_patterns):
                risks['medium'].append(result)
            else:
                risks['info'].append(result)
        
        return risks
    
    def categorize_results(self, data):
        """Categorize results by type"""
        categories = {
            'env_files': [],
            'config_files': [],
            'api_keys': [],
            'credentials': [],
            'api_endpoints': [],
            'sensitive_data': [],
            'other': []
        }
        
        if isinstance(data, dict):
            for category, results in data.items():
                if category == 'env_files':
                    categories['env_files'] = results
                elif category == 'config_files':
                    categories['config_files'] = results
                elif category == 'credentials':
                    categories['credentials'] = results
                elif category == 'api_endpoints':
                    categories['api_endpoints'] = results
                else:
                    categories['other'].extend(results)
        elif isinstance(data, list):
            for result in data:
                title = result.get('title', '').lower()
                if '.env' in title:
                    categories['env_files'].append(result)
                elif 'config' in title:
                    categories['config_files'].append(result)
                elif 'api' in title:
                    categories['api_endpoints'].append(result)
                elif any(word in title for word in ['password', 'key', 'secret', 'token']):
                    categories['credentials'].append(result)
                else:
                    categories['other'].append(result)
        
        return categories
    
    def generate_html_report(self, data, title, timestamp):
        """Generate HTML report"""
        
        html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; border-bottom: 2px solid #333; padding-bottom: 20px; margin-bottom: 30px; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .summary-card {{ background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #007bff; }}
        .risk-high {{ border-left-color: #dc3545; }}
        .risk-medium {{ border-left-color: #ffc107; }}
        .risk-low {{ border-left-color: #28a745; }}
        .risk-info {{ border-left-color: #17a2b8; }}
        .section {{ margin-bottom: 30px; }}
        .section h3 {{ color: #333; border-bottom: 1px solid #ddd; padding-bottom: 10px; }}
        .result-item {{ background: #f8f9fa; margin: 10px 0; padding: 15px; border-radius: 5px; border-left: 3px solid #007bff; }}
        .result-title {{ font-weight: bold; color: #333; margin-bottom: 8px; }}
        .result-link {{ color: #007bff; text-decoration: none; word-break: break-all; }}
        .result-link:hover {{ text-decoration: underline; }}
        .result-snippet {{ color: #666; margin: 5px 0; }}
        .risk-badge {{ display: inline-block; padding: 3px 8px; border-radius: 12px; font-size: 12px; font-weight: bold; color: white; }}
        .badge-high {{ background-color: #dc3545; }}
        .badge-medium {{ background-color: #ffc107; color: #333; }}
        .badge-low {{ background-color: #28a745; }}
        .badge-info {{ background-color: #17a2b8; }}
        .metadata {{ color: #666; font-size: 12px; margin-top: 10px; }}
        .chart {{ margin: 20px 0; padding: 15px; background: #f8f9fa; border-radius: 5px; }}
        .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; text-align: center; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 Security Assessment Report</h1>
            <h2>{title}</h2>
            <p>Generated on: {timestamp}</p>
        </div>
        
        {self._generate_summary_section(data)}
        {self._generate_detailed_sections(data)}
        
        <div class="footer">
            <p>This report was generated automatically by the Credential Finder Tool</p>
            <p>⚠️ Use this information responsibly and only on systems you own or have permission to test</p>
        </div>
    </div>
</body>
</html>
        """
        
        return html_template
    
    def _generate_summary_section(self, data):
        """Generate summary section HTML"""
        total_results = 0
        risks = {'high': 0, 'medium': 0, 'low': 0, 'info': 0}
        
        # Count results
        if isinstance(data, dict):
            for category, results in data.items():
                if isinstance(results, list):
                    total_results += len(results)
                    # Analyze risks
                    categorized = self.analyze_credentials(results)
                    for risk_level, risk_results in categorized.items():
                        risks[risk_level] += len(risk_results)
        elif isinstance(data, list):
            total_results = len(data)
            categorized = self.analyze_credentials(data)
            for risk_level, risk_results in categorized.items():
                risks[risk_level] += len(risk_results)
        
        return f"""
        <div class="summary">
            <div class="summary-card">
                <h3>📊 Total Findings</h3>
                <h2>{total_results}</h2>
                <p>Potential security issues discovered</p>
            </div>
            <div class="summary-card risk-high">
                <h3>🚨 High Risk</h3>
                <h2>{risks['high']}</h2>
                <p>Critical security vulnerabilities</p>
            </div>
            <div class="summary-card risk-medium">
                <h3>⚠️ Medium Risk</h3>
                <h2>{risks['medium']}</h2>
                <p>Moderate security concerns</p>
            </div>
            <div class="summary-card risk-low">
                <h3>✅ Low Risk</h3>
                <h2>{risks['low']}</h2>
                <p>Minor security issues</p>
            </div>
        </div>
        """
    
    def _generate_detailed_sections(self, data):
        """Generate detailed sections HTML"""
        sections_html = ""
        
        if isinstance(data, dict):
            for category, results in data.items():
                if results:
                    categorized = self.analyze_credentials(results)
                    sections_html += f"""
                    <div class="section">
                        <h3>🔍 {category.replace('_', ' ').title()}</h3>
                        {self._generate_risk_sections(categorized)}
                    </div>
                    """
        elif isinstance(data, list):
            categorized = self.analyze_credentials(data)
            sections_html = f"""
            <div class="section">
                <h3>🔍 All Results</h3>
                {self._generate_risk_sections(categorized)}
            </div>
            """
        
        return sections_html
    
    def _generate_risk_sections(self, categorized_results):
        """Generate risk-based result sections"""
        html = ""
        
        for risk_level, results in categorized_results.items():
            if results:
                html += f"""
                <div class="risk-section">
                    <h4>Risk Level: {risk_level.title()}</h4>
                """
                for result in results:
                    html += f"""
                    <div class="result-item">
                        <div class="result-title">
                            {result.get('title', 'N/A')}
                            <span class="risk-badge badge-{risk_level}">{risk_level.upper()}</span>
                        </div>
                        <a href="{result.get('link', '#')}" class="result-link" target="_blank">
                            {result.get('link', 'N/A')}
                        </a>
                        <div class="result-snippet">{result.get('snippet', 'N/A')}</div>
                        <div class="metadata">
                            URL: {result.get('link', 'N/A')}
                        </div>
                    </div>
                    """
                html += "</div>"
        
        return html
    
    def generate_text_report(self, data, title, timestamp):
        """Generate text-based report"""
        report = f"""
CREDENTIAL FINDER SECURITY REPORT
=================================
Title: {title}
Generated: {timestamp}
{'='*50}

"""
        
        if isinstance(data, dict):
            for category, results in data.items():
                if results:
                    report += f"\n🔍 {category.replace('_', ' ').title()} ({len(results)} found)\n"
                    report += "-" * 40 + "\n"
                    
                    categorized = self.analyze_credentials(results)
                    for risk_level, risk_results in categorized.items():
                        if risk_results:
                            report += f"\n  Risk Level: {risk_level.upper()}\n"
                            for result in risk_results:
                                report += f"""
    Title: {result.get('title', 'N/A')}
    URL: {result.get('link', 'N/A')}
    Snippet: {result.get('snippet', 'N/A')[:100]}...
    
"""
        elif isinstance(data, list):
            categorized = self.analyze_credentials(data)
            report += f"\n🔍 All Results ({len(data)} found)\n"
            report += "-" * 40 + "\n"
            
            for risk_level, results in categorized.items():
                if results:
                    report += f"\n  Risk Level: {risk_level.upper()}\n"
                    for result in results:
                        report += f"""
    Title: {result.get('title', 'N/A')}
    URL: {result.get('link', 'N/A')}
    Snippet: {result.get('snippet', 'N/A')[:100]}...

"""
        
        report += "\n" + "="*50 + "\n"
        report += "END OF REPORT\n"
        report += "⚠️ Use this information responsibly!\n"
        
        return report
    
    def create_json_report(self, data, title, timestamp):
        """Create structured JSON report"""
        report = {
            'title': title,
            'timestamp': timestamp,
            'summary': {
                'total_findings': 0,
                'high_risk': 0,
                'medium_risk': 0,
                'low_risk': 0,
                'info': 0
            },
            'findings': {},
            'metadata': {
                'report_version': '1.0',
                'generated_by': 'Credential Finder Tool',
                'scan_duration': 'N/A'
            }
        }
        
        if isinstance(data, dict):
            for category, results in data.items():
                categorized = self.analyze_credentials(results)
                report['findings'][category] = categorized
                
                # Update summary
                report['summary']['total_findings'] += sum(len(r) for r in categorized.values())
                for risk_level, risk_results in categorized.items():
                    report['summary'][f'{risk_level}_risk'] += len(risk_results)
        
        elif isinstance(data, list):
            categorized = self.analyze_credentials(data)
            report['findings']['all_results'] = categorized
            
            # Update summary
            report['summary']['total_findings'] = sum(len(r) for r in categorized.values())
            for risk_level, risk_results in categorized.items():
                report['summary'][f'{risk_level}_risk'] += len(risk_results)
        
        return report
    
    def process_directory(self, directory_path):
        """Process all JSON files in a directory"""
        results = {}
        json_files = [f for f in os.listdir(directory_path) if f.endswith('.json')]
        
        for json_file in json_files:
            filepath = os.path.join(directory_path, json_file)
            data = self.load_json_data(filepath)
            if data:
                category = json_file.replace('.json', '')
                results[category] = data
        
        return results
    
    def generate_comprehensive_report(self, input_data=None, title=None):
        """Generate comprehensive report from input data"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if not title:
            title = f"Credential Discovery Report - {timestamp}"
        
        # Determine data source
        if input_data is None:
            # Process all JSON files in current directory
            input_data = self.process_directory('.')
            title = "Comprehensive Security Assessment Report"
        
        # Generate reports in different formats
        filename_base = f"security_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # HTML Report
        html_content = self.generate_html_report(input_data, title, timestamp)
        html_file = os.path.join(self.reports_dir, f"{filename_base}.html")
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Text Report
        text_content = self.generate_text_report(input_data, title, timestamp)
        text_file = os.path.join(self.reports_dir, f"{filename_base}.txt")
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write(text_content)
        
        # JSON Report
        json_report = self.create_json_report(input_data, title, timestamp)
        json_file = os.path.join(self.reports_dir, f"{filename_base}.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(json_report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📊 Report Generated Successfully!")
        print(f"📁 Files created:")
        print(f"  HTML Report: {html_file}")
        print(f"  Text Report: {text_file}")
        print(f"  JSON Report: {json_file}")
        
        return {
            'html': html_file,
            'text': text_file,
            'json': json_file
        }

def main():
    generator = ReportGenerator()
    
    print("📊 Automated Reporting System")
    print("=" * 50)
    print("\nChoose an option:")
    print("1. Generate report from directory of JSON files")
    print("2. Generate report from specific JSON file")
    print("3. Generate custom report from data")
    print("4. Generate comprehensive report from all JSON files in current directory")
    
    choice = input("\nEnter your choice (1-4): ").strip()
    
    if choice == '1':
        directory = input("Enter directory path containing JSON files: ").strip()
        if os.path.exists(directory):
            data = generator.process_directory(directory)
            generator.generate_comprehensive_report(data)
        else:
            print("❌ Directory not found")
    
    elif choice == '2':
        filepath = input("Enter path to JSON file: ").strip()
        if os.path.exists(filepath):
            data = generator.load_json_data(filepath)
            if data:
                title = input("Enter report title (optional): ").strip()
                generator.generate_comprehensive_report(data, title)
        else:
            print("❌ File not found")
    
    elif choice == '3':
        print("This option requires programmatic data input.")
        print("Use the generator programmatically with:")
        print("generator.generate_comprehensive_report(your_data, 'Custom Title')")
    
    elif choice == '4':
        print("Generating comprehensive report from all JSON files...")
        generator.generate_comprehensive_report()
    
    else:
        print("❌ Invalid choice")

if __name__ == "__main__":
    main()