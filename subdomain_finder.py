#!/usr/bin/env python3
"""
Subdomain Discovery and Enumeration Tool
Discovers subdomains using various techniques including DNS, search engines, and certificate transparency
"""

import requests
import socket
import dns.resolver
import ssl
import json
import time
import os
from urllib.parse import urlparse
import concurrent.futures
from dotenv import load_dotenv

load_dotenv()

class SubdomainFinder:
    def __init__(self):
        self.api_key = os.getenv('API_KEY_GOOGLE')
        self.engine_id = os.getenv('SEARCH_ENGINE_ID')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def dns_bruteforce(self, domain, wordlist=None):
        """DNS bruteforce for subdomain discovery"""
        if not wordlist:
            wordlist = [
                'www', 'mail', 'ftp', 'localhost', 'webmail', 'smtp', 'pop', 'ns1', 'webdisk', 
                'ns2', 'cpanel', 'whm', 'autodiscover', 'autoconfig', 'ns', 'm', 'imap', 'test',
                'ns3', 'mail2', 'new', 'mysql', 'old', 'blog', 'pop3', 'dev', 'www2', 'admin',
                'forum', 'news', 'vpn', 'ns4', 'ns5', 'ns6', 'ns7', 'www1', 'email', 'web',
                'demo', 'home', 'sql', 'ns8', 'staging', 'api', 'secure', 'docs', 'beta',
                'www3', 'images', 'img', 'www4', 'shop', 'prod', 'prod1', 'prod2', 'backup',
                'mx', 'mobile', 'wap', 'eshop', 'ecommerce', 'test1', 'test2', 'app', 'apps',
                'login', 'admin1', 'admin2', 'user', 'users', 'support', 'help', 'docs1',
                'staging1', 'staging2', 'dev1', 'dev2', 'internal', 'private', 'intranet'
            ]
        
        found_subdomains = []
        
        def check_subdomain(subdomain):
            try:
                full_domain = f"{subdomain}.{domain}"
                socket.gethostbyname(full_domain)
                return full_domain
            except (socket.gaierror, socket.herror):
                return None
        
        print(f"🔍 DNS Bruteforcing {domain}...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(check_subdomain, sub) for sub in wordlist]
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if result:
                    found_subdomains.append(result)
                    print(f"  ✅ Found: {result}")
        
        return list(set(found_subdomains))
    
    def google_subdomains(self, domain):
        """Find subdomains using Google search"""
        queries = [
            f'site:*.{domain} -www.{domain}',
            f'site:{domain} -inurl:www.{domain}',
            f'inurl:*.{domain}',
            f'intext:*.{domain}',
            f'"{domain}" "subdomain"'
        ]
        
        subdomains = set()
        
        for query in queries:
            print(f"  Query: {query}")
            try:
                url = f'https://www.googleapis.com/customsearch/v1?key={self.api_key}&cx={self.engine_id}&q={query}&num=10'
                response = self.session.get(url)
                response.raise_for_status()
                data = response.json()
                
                for item in data.get('items', []):
                    link = item.get('link', '')
                    parsed = urlparse(link)
                    if parsed.netloc:
                        if domain in parsed.netloc:
                            subdomains.add(parsed.netloc)
                
                time.sleep(1)  # Rate limiting
            except Exception as e:
                print(f"Error in Google search: {e}")
        
        return list(subdomains)
    
    def certificate_transparency(self, domain):
        """Search certificate transparency logs for subdomains"""
        ct_domains = set()
        
        # crt.sh API
        try:
            url = f"https://crt.sh/?q=%.{domain}&output=json"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                certs = response.json()
                for cert in certs:
                    name_value = cert.get('name_value', '')
                    if name_value:
                        # Handle multiple domains in one certificate
                        for name in name_value.split('\n'):
                            name = name.strip()
                            if name.endswith(f'.{domain}'):
                                ct_domains.add(name)
            
            print(f"  🔒 Certificate Transparency found {len(ct_domains)} subdomains")
        except Exception as e:
            print(f"Error in certificate transparency search: {e}")
        
        return list(ct_domains)
    
    def dns_records(self, domain):
        """Get various DNS records for the domain"""
        record_types = ['A', 'AAAA', 'MX', 'NS', 'TXT', 'CNAME', 'SRV']
        records = {}
        
        for record_type in record_types:
            try:
                answers = dns.resolver.resolve(domain, record_type)
                records[record_type] = [str(answer) for answer in answers]
                print(f"  📋 {record_type} records: {len(records[record_type])} found")
            except Exception as e:
                records[record_type] = []
        
        return records
    
    def port_scan_subdomains(self, subdomains, ports=[22, 23, 53, 80, 135, 139, 443, 993, 995]):
        """Scan subdomains for open ports"""
        open_ports = {}
        
        def scan_port(subdomain, port):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex((subdomain, port))
            sock.close()
            return port if result == 0 else None
        
        print(f"🔍 Port scanning {len(subdomains)} subdomains...")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
            futures = []
            for subdomain in subdomains:
                for port in ports:
                    futures.append(executor.submit(scan_port, subdomain, port))
            
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if result:
                    print(f"  ✅ {result} is open")
        
        return open_ports
    
    def save_results(self, results, filename):
        """Save results to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"💾 Results saved to {filename}")
    
    def discover_subdomains(self, domain):
        """Main subdomain discovery function"""
        print(f"🚀 Starting subdomain discovery for {domain}")
        print("=" * 50)
        
        all_subdomains = set()
        
        # DNS bruteforce
        dns_subs = self.dns_bruteforce(domain)
        all_subdomains.update(dns_subs)
        
        # Google search
        google_subs = self.google_subdomains(domain)
        all_subdomains.update(google_subs)
        
        # Certificate transparency
        ct_subs = self.certificate_transparency(domain)
        all_subdomains.update(ct_subs)
        
        # DNS records
        dns_records = self.dns_records(domain)
        
        # Final results
        final_subdomains = list(all_subdomains)
        
        print(f"\n📊 Discovery Results for {domain}:")
        print(f"  Total subdomains found: {len(final_subdomains)}")
        print(f"  DNS Bruteforce: {len(dns_subs)}")
        print(f"  Google Search: {len(google_subs)}")
        print(f"  Certificate Transparency: {len(ct_subs)}")
        
        if final_subdomains:
            print(f"\n🔍 Found Subdomains:")
            for i, subdomain in enumerate(sorted(final_subdomains), 1):
                print(f"  {i:2d}. {subdomain}")
        
        return {
            'domain': domain,
            'subdomains': final_subdomains,
            'dns_subs': dns_subs,
            'google_subs': google_subs,
            'ct_subs': ct_subs,
            'dns_records': dns_records,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }

def main():
    finder = SubdomainFinder()
    
    print("🌐 Subdomain Discovery Tool")
    print("=" * 50)
    
    domain = input("Enter domain to discover subdomains for: ").strip()
    
    if not domain:
        print("❌ Domain cannot be empty")
        return
    
    results = finder.discover_subdomains(domain)
    
    # Ask to save results
    save = input("\nSave results to JSON file? (y/n): ").lower()
    if save == 'y':
        filename = f"{domain.replace('.', '_')}_subdomains.json"
        finder.save_results(results, filename)
    
    # Ask to port scan
    scan = input("\nPort scan discovered subdomains? (y/n): ").lower()
    if scan == 'y':
        port_results = finder.port_scan_subdomains(results['subdomains'])
        finder.save_results(port_results, f"{domain.replace('.', '_')}_port_scan.json")

if __name__ == "__main__":
    main()