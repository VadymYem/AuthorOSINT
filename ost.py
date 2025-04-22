# -*- coding: utf-8 -*-

# --- AuthorOSINT Lite (Termux Friendly) ---
# Версія 3.7.0
#Developer: AuthorChe, authorche.pp.ua
# --- НЕОБХІДНІ КРОКИ ДЛЯ ВСТАНОВЛЕННЯ(pkg for Termux, apt for Linux) ---
# 1. Оновіть пакети: pkg/apt update && pkg/apt upgrade -y
# 2. Встановіть базові: pkg/apt install python git curl wget whois openssl -y
# 3. Встановіть pip та Python пакети:
#    pip install --upgrade pip
#    pip install requests beautifulsoup4 colorama phonenumbers python-whois # python-whois опціонально
#    pip install "googlesearch-python" wikipedia-api email_validator dnspython sherlock-project
#    pip install huggingface_hub ipinfo
# 4. Sherlock (alt): git clone https://github.com/sherlock-project/sherlock.git && cd sherlock && python -m pip install -r requirements.txt && cd ..
# -----------------------------------------

import os
import sys
import subprocess
import requests
import json
from datetime import datetime
from bs4 import BeautifulSoup
from colorama import Fore, Style, init
import phonenumbers
from phonenumbers import geocoder, carrier, phonenumberutil
try:
    import whois
    PYTHON_WHOIS_AVAILABLE = True
except ImportError:
    PYTHON_WHOIS_AVAILABLE = False
try:
    from googlesearch import search
    GOOGLESEARCH_AVAILABLE = True
except ImportError:
    print(f"{Fore.RED}Помилка: Не вдалося імпортувати 'search' з 'googlesearch'. Встановіть 'googlesearch-python'.{Style.RESET_ALL}")
    GOOGLESEARCH_AVAILABLE = False
import wikipedia
from email_validator import validate_email, EmailNotValidError
import dns.resolver
import time
import logging
import shutil
import re
import random
import getpass
from huggingface_hub import HfApi, InferenceClient
from huggingface_hub.utils import HfHubHTTPError
import ipinfo

init(autoreset=True)

logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("huggingface_hub").setLevel(logging.WARNING)

AUTHOR_WATERMARK = Style.DIM + Fore.GREEN + "[AuthorChe]" + Style.RESET_ALL
HF_TOKEN_FILE = os.path.expanduser("~/.author_osint_hf_token")
HF_MODEL_ID = "HuggingFaceH4/zephyr-7b-beta"
IPINFO_TOKEN = None # Вставте свій токен ipinfo.io сюди, якщо є
DONATE_URL = "https://authorche.pp.ua/donate.html"

class AuthorOSINTLite:

    def __init__(self):
        self.version = "3.7.1-Final"
        self.author_name = "AuthorChe"
        self.banner = f"""
{Fore.GREEN}╔═══════════════════════════════════════════════════════╗
║  ▄▄▄       █    ██ ▄▄▄█████▓ ██░ ██   ▒█████   ██▀███{Style.NORMAL} ║
║ ▒████▄     ██  ▓██▒▓  ██▒ ▓▒▓██░ ██▒▒██▒  ██▒▓██ ▒ ██▒║
║ ▒██  ▀█▄  ▓██  ▒██░▒ ▓██░ ▒░▒██▀▀██░▒██░  ██▒▓██ ░▄█ ▒║
║ ░██▄▄▄▄██ ▓▓█  ░██░░ ▓██▓ ░ ░▓█ ░██ ▒██   ██░▒██▀▀█▄  ║
║  ▓█   ▓██▒▒▒█████▓   ▒██▒ ░ ░▓█▒░██▓░ ████▓▒░░██▓ ▒██▒║
║  ▒▒    ▓▒█░░▒▓▒ ▒ ▒   ▒ ░░    ▒ ░░▒░▒░ ▒░▒░▒░ ░ ▒▓ ░▒▓║
║   ▒   ▒▒ ░░░▒░ ░ ░     ░     ▒ ░▒░ ░  ░ ▒ ▒░   ░▒ ░ ▒ ║
║   ░   ▒    ░░░ ░ ░   ░       ░  ░░ ░░ ░ ░ ▒    ░░   ░ ║
║       ░  ░   ░                 ░  ░  ░    ░ ░     ░   ║
╠═══════════════════════════════════════════════════════╣
║ {Style.BRIGHT} OSINT Tool v{self.version} by {self.author_name}{Fore.YELLOW}           ║
║ {Fore.CYAN}Inst:{Fore.YELLOW} @Vadym_Yem {Fore.CYAN}TG:{Fore.YELLOW} @wsinfo {Fore.CYAN}Web:{Fore.YELLOW} authorche.pp.ua     ║
╚═══════════════════════════════════════════════════════╝{Style.RESET_ALL}
"""
        os.makedirs("logs", exist_ok=True)
        self.log_file = f"logs/osint_lite_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:109.0) Gecko/20100101 Firefox/115.0'})
        self.hf_token = None
        try:
            self.ipinfo_handler = ipinfo.getHandler(IPINFO_TOKEN)
        except Exception as e:
            self.log(f"Failed to initialize ipinfo handler: {e}")
            self.ipinfo_handler = None
            print(f"{Fore.YELLOW}Попередження: Не вдалося ініціалізувати обробник ipinfo. Геолокація IP може не працювати.{Style.RESET_ALL}")

    def log(self, message: str):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        sanitized = message.encode('utf-8', 'replace').decode('utf-8')
        try:
            with open(self.log_file, 'a', encoding='utf-8', errors='replace') as f:
                f.write(f"[{timestamp}] {sanitized}\n")
        except Exception as e: print(f"{Fore.RED}Помилка запису логу: {e}{Style.RESET_ALL}")

    def clear(self): os.system('cls' if os.name == 'nt' else 'clear')

    def print_banner(self): self.clear(); print(self.banner)

    def get_input_with_prompt(self, prompt_text: str, example: str = ""):
        prompt = f"{Fore.CYAN}{prompt_text}{Style.RESET_ALL}"
        if example: prompt += f"{Fore.YELLOW} (приклад: {example}){Style.RESET_ALL}"
        print(prompt)
        try: return input(f"{Fore.GREEN}> {Style.RESET_ALL}")
        except EOFError: print(f"{Fore.YELLOW}\nЗавершення вводу (EOF)...{Style.RESET_ALL}"); return None

    def load_hf_token(self):
        if self.hf_token: return self.hf_token
        if os.path.exists(HF_TOKEN_FILE):
            try:
                with open(HF_TOKEN_FILE, 'r') as f: token = f.read().strip()
                if token:
                    print(f"{Fore.CYAN}Перевірка збереженого токена HF...{Style.RESET_ALL}", end='\r')
                    try:
                        HfApi().whoami(token=token)
                        print(" " * 40, end='\r'); self.hf_token = token; self.log("Токен HF завантажено.")
                        return token
                    except HfHubHTTPError:
                        print(f"{Fore.YELLOW}Збережений токен HF недійсний. Видалення.{Style.RESET_ALL}")
                        os.remove(HF_TOKEN_FILE)
                    # Fallback: still return token even if validation fails offline? Maybe.
                    except Exception as e:
                        self.log(f"Помилка валідації збереженого токена HF: {e}")
                        self.hf_token = token; return token # Consider returning even if validation fails?
            except Exception as e: self.log(f"Помилка завантаження токена HF: {e}")
        return None

    def save_hf_token(self, token):
        try:
            with open(HF_TOKEN_FILE, 'w') as f: f.write(token)
            try: os.chmod(HF_TOKEN_FILE, 0o600) # Set restrictive permissions
            except OSError: pass # Ignore if chmod fails (e.g., Windows)
            self.hf_token = token; self.log(f"Токен HF збережено у {HF_TOKEN_FILE}")
            return True
        except Exception as e:
            print(f"{Fore.RED}Помилка збереження токена HF: {e}{Style.RESET_ALL}")
            self.log(f"Помилка збереження токена HF: {e}"); return False

    def get_and_validate_hf_token(self):
        print(f"\n{Fore.YELLOW}Для роботи AuthorAI потрібен токен Hugging Face API.{Style.RESET_ALL}")
        print(f"Отримати токен (з правами 'read') можна тут:")
        print(f"{Fore.CYAN}https://huggingface.co/settings/tokens{Style.RESET_ALL}")
        print(f"Токен буде збережено локально для майбутнього використання у:")
        print(f"{Fore.CYAN}{HF_TOKEN_FILE}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Попередження: Зберігання токенів у текстовому файлі не є найбезпечнішим методом.{Style.RESET_ALL}")
        while True:
            try:
                token = getpass.getpass(f"{Fore.CYAN}Введіть ваш токен Hugging Face (буде приховано): {Style.RESET_ALL}")
                if not token: return None # User cancelled
                print(f"{Fore.CYAN}Валідація токена...{Style.RESET_ALL}", end='\r')
                try:
                    user_info = HfApi().whoami(token=token)
                    print(" " * 30, end='\r') # Clear validation message
                    print(f"{Fore.GREEN}Токен успішно валідовано для користувача: {user_info.get('name', 'N/A')}{Style.RESET_ALL}")
                    if self.save_hf_token(token): return token
                    else: print(f"{Fore.RED}Не вдалося зберегти токен.{Style.RESET_ALL}"); return token # Still return if save failed
                except HfHubHTTPError:
                    print(" "*30, end='\r'); print(f"{Fore.RED}Валідація токена не вдалась: Невірний токен або проблема з мережею.{Style.RESET_ALL}")
                except Exception as e:
                    print(" "*30, end='\r'); print(f"{Fore.RED}Помилка валідації: {e}{Style.RESET_ALL}")

                retry = input(f"{Fore.YELLOW}Спробувати ще раз? (y/N): {Style.RESET_ALL}").lower()
                if retry != 'y': return None
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}Введення токена скасовано.{Style.RESET_ALL}"); return None

    def fetch_google(self, query: str, max_results: int = 5):
        results = []
        if not GOOGLESEARCH_AVAILABLE: return results
        print(f"{Fore.CYAN}Пошук Google '{query}'...{Style.RESET_ALL}", end='\r')
        try:
            search_generator = search(query, lang="uk", num_results=max_results, sleep_interval=1.5) # Added sleep
            for i, url in enumerate(search_generator):
                results.append(url)
                # No need for manual break, num_results handles it
                # time.sleep(1.0) # Let googlesearch handle sleep
            print(" " * 60, end='\r'); # Clear status
            return results
        except ImportError:
            print(" "*60, end='\r'); print(f"{Fore.RED}Бібліотека Google Search недоступна.{Style.RESET_ALL}")
            return []
        except Exception as e:
            print(" " * 60, end='\r')
            err_str = str(e)
            if "429" in err_str: print(f"{Fore.RED}Помилка Google: 429 (Забагато запитів). Спробуйте пізніше.{Style.RESET_ALL}")
            elif "timed out" in err_str.lower(): print(f"{Fore.RED}Помилка Google: Таймаут запиту.{Style.RESET_ALL}")
            else: print(f"{Fore.RED}Помилка Google Search: {e}.{Style.RESET_ALL}")
            self.log(f"Google Error: {e}")
            return []

    def fetch_wikipedia(self, query: str, lang: str = 'uk', sentences: int = 3):
        try:
            wikipedia.set_lang(lang)
            # Use search to find the best page title first
            search_results = wikipedia.search(query)
            if not search_results:
                return None
            page_title = search_results[0] # Try the top result
            try:
                summary = wikipedia.summary(page_title, sentences=sentences, auto_suggest=False)
                # Basic check to avoid irrelevant disambiguation pages
                if summary and f"may refer to:" not in summary.lower() and f"does not match any pages." not in summary.lower():
                     # Add page URL for context
                     page_obj = wikipedia.page(page_title, auto_suggest=False)
                     return f"{summary}\n{Fore.BLUE}Джерело ({lang}): {page_obj.url}{Style.RESET_ALL}"
                else: return None # Summary was likely irrelevant
            except wikipedia.exceptions.PageError:
                return None # Specific page title didn't work
            except wikipedia.exceptions.DisambiguationError as e:
                # Try suggesting the first option if disambiguation occurs
                try:
                    first_option = e.options[0]
                    summary = wikipedia.summary(first_option, sentences=sentences, auto_suggest=False)
                    page_obj = wikipedia.page(first_option, auto_suggest=False)
                    return f"{Fore.YELLOW}(Неоднозначно, обрано: {first_option}){Style.RESET_ALL} {summary}\n{Fore.BLUE}Джерело ({lang}): {page_obj.url}{Style.RESET_ALL}"
                except Exception: # If getting the first option fails
                    return f"{Fore.YELLOW}Неоднозначно ({lang}): {', '.join(e.options[:3])}...{Style.RESET_ALL}"
        except Exception as e:
             self.log(f"Wikipedia Error ({lang}) for '{query}': {e}")
             return f"{Fore.RED}Помилка Wikipedia ({lang}): {e}{Style.RESET_ALL}"


    def author_search(self, query: str = None):
        self.print_banner()
        query = query or self.get_input_with_prompt("Введіть запит", "Прізвище Ім'я")
        if query is None: return
        self.log(f"Search: '{query}'")
        print(f"\n{Fore.GREEN}--- Пошук '{query}' {AUTHOR_WATERMARK} ---{Style.RESET_ALL}")

        print(f"\n{Fore.GREEN}[ Google ]{Style.RESET_ALL}")
        ggl_res = self.fetch_google(query)
        if ggl_res: [print(f"{Fore.GREEN}• {Fore.BLUE}{u}{Style.RESET_ALL}") for u in ggl_res]
        elif isinstance(ggl_res, list): print(f"{Fore.YELLOW}Нічого не знайдено.{Style.RESET_ALL}")

        print(f"\n{Fore.GREEN}[ Wikipedia ]{Style.RESET_ALL}")
        wiki_lang = 'uk' # Default to Ukrainian
        # Optional: Ask for language if needed
        # wiki_lang = self.get_input_with_prompt("Мова Wikipedia (uk/en/ru)", "uk").lower()
        # if wiki_lang not in ['uk', 'en', 'ru']:
        #     print(f"{Fore.YELLOW}Невірна мова, використовується 'uk'.{Style.RESET_ALL}")
        #     wiki_lang = 'uk'

        wiki = self.fetch_wikipedia(query, lang=wiki_lang)
        print(wiki if wiki else f"{Fore.YELLOW}Інформація у Вікіпедії ({wiki_lang}) відсутня.{Style.RESET_ALL}")

        # Add search for other languages?
        print(f"\n{Fore.GREEN}[ Wikipedia (en) ]{Style.RESET_ALL}")
        wiki_en = self.fetch_wikipedia(query, lang='en')
        print(wiki_en if wiki_en else f"{Fore.YELLOW}Інформація у Вікіпедії (en) відсутня.{Style.RESET_ALL}")


        print(f"\n{Fore.CYAN}--- Пошук завершено ---{Style.RESET_ALL}")
        input(f"\n{Fore.CYAN}Натисніть Enter...{Style.RESET_ALL}")

    def _perform_reputation_search(self, queries: list, search_type: str):
        print(f"{Fore.CYAN}Пошук згадок в Google...{Style.RESET_ALL}")
        urls=set(); found=0; max_r=3
        for i,q in enumerate(queries):
            time.sleep(random.uniform(1.0, 2.5)) # Increased random delay
            self.log(f"Reputation ({search_type}): '{q}'")
            try:
                res_g = self.fetch_google(q, max_results=max_r)
                if res_g:
                    for u in res_g:
                        if u and u not in urls:
                            print(f"{Fore.GREEN}• [GGL] {u}{Style.RESET_ALL}")
                            urls.add(u); found+=1
            except Exception as e:
                 self.log(f"Помилка репутаційного пошуку Google для '{q}': {e}")
                 pass # Continue searching
        print("-" * 20)
        print(f"{Fore.GREEN}Знайдено {found} згадок.{Style.RESET_ALL}" if found else f"{Fore.YELLOW}Релевантних згадок не знайдено.{Style.RESET_ALL}")

    def author_username_check(self, username: str = None):
        self.print_banner()
        print(f"{Fore.GREEN}--- Перевірка юзернейму {AUTHOR_WATERMARK} ---{Style.RESET_ALL}")
        s_path=shutil.which('sherlock')
        l_path=os.path.expanduser("~/sherlock/sherlock/sherlock.py") # Standard path if cloned
        s_cmd = None

        if s_path:
             s_cmd=['sherlock']
             print(f"{Fore.CYAN}Використовується Sherlock з PATH: {s_path}{Style.RESET_ALL}")
        elif os.path.exists(l_path):
             s_cmd=[sys.executable, l_path] # Use current python interpreter
             print(f"{Fore.YELLOW}Використовується локальна версія Sherlock: {l_path}{Style.RESET_ALL}")
        else:
             print(f"{Fore.RED}Команду 'sherlock' не знайдено!{Style.RESET_ALL}")
             print(f"{Fore.YELLOW}Встановіть: {Fore.CYAN}pip install sherlock-project{Style.RESET_ALL} або клонуйте з GitHub.")
             input(f"{Fore.CYAN}Натисніть Enter...{Style.RESET_ALL}"); return

        username = username or self.get_input_with_prompt("Введіть юзернейм", "example_user")
        if username is None:
            return
        self.log(f"Sherlock: {username}")
        print(f"{Fore.CYAN}Запуск Sherlock для '{username}'... (Це може зайняти деякий час){Style.RESET_ALL}")

        try:
            # Consider adding --site option later if needed
            cmd=s_cmd + ['--print-found','--no-color','--timeout','30', '--output', f'logs/sherlock_{username}_{datetime.now().strftime("%Y%m%d%H%M")}.txt', username]
            # Using subprocess.Popen for potentially better handling of output streams if needed later
            p=subprocess.run(cmd,capture_output=True,text=True,check=False,encoding='utf-8',errors='replace')
            out=p.stdout.strip(); err=p.stderr.strip()
            links=[l.replace("[+] ","").strip() for l in out.splitlines() if l.startswith("[+] ")] if out else []
            if links:
                print(f"\n{Fore.GREEN}[ Знайдено профілі ({len(links)}) ]{Style.RESET_ALL}")
                [print(f"{Fore.GREEN}• {Fore.BLUE}{l}{Style.RESET_ALL}") for l in links]
                print(f"\n{Fore.CYAN}Результати збережено у файл логів Sherlock.{Style.RESET_ALL}")
            else:
                print(f"{Fore.YELLOW}\nПрофілів не знайдено.{Style.RESET_ALL}")

            # Show stderr only if it contains errors, not just progress messages
            if err and "ERROR" in err.upper():
                 print(f"\n{Fore.YELLOW}Повідомлення Sherlock (stderr):{Style.RESET_ALL}\n{err}")
                 self.log(f"Sherlock stderr for '{username}': {err}")

        except Exception as e:
             print(f"{Fore.RED}\nПомилка виконання Sherlock: {e}{Style.RESET_ALL}")
             self.log(f"Sherlock execution error for '{username}': {e}")
        input(f"\n{Fore.CYAN}Натисніть Enter...{Style.RESET_ALL}")

    def author_email_check(self, email: str = None):
        self.print_banner()
        print(f"{Fore.GREEN}--- Перевірка Email {AUTHOR_WATERMARK} ---{Style.RESET_ALL}")

        email = email or self.get_input_with_prompt("Введіть Email", "example@domain.com")
        if email is None:
             return
        self.log(f"Email Check: {email}")

        try:
            print(f"\n{Fore.CYAN}Перевірка формату...{Style.RESET_ALL}")
            valid=validate_email(email,check_deliverability=False) 
            domain=valid.domain
            print(f"{Fore.GREEN} [+] Формат валідний, Домен: {domain}{Style.RESET_ALL}")

            print(f"\n{Fore.CYAN}Перевірка MX записів...{Style.RESET_ALL}")
            try:
                mx=dns.resolver.resolve(domain,'MX')
                mx_l=sorted([str(r.exchange).rstrip('.') for r in mx])
                print(f"{Fore.GREEN} [+] MX: {', '.join(mx_l)}{Style.RESET_ALL}" if mx_l else f"{Fore.YELLOW} [!] MX порожній.{Style.RESET_ALL}")
            except dns.resolver.NoAnswer: print(f"{Fore.YELLOW} [!] MX не знайдено (домен може не приймати пошту).{Style.RESET_ALL}")
            except dns.resolver.NXDOMAIN: print(f"{Fore.RED} [-] Домен не існує.{Style.RESET_ALL}"); return 
            except dns.exception.Timeout: print(f"{Fore.YELLOW} [!] Таймаут перевірки MX.{Style.RESET_ALL}")
            except Exception as e: print(f"{Fore.RED} [-] Помилка MX: {e}{Style.RESET_ALL}")

            # Deliverability check (optional, can be slow/unreliable)
            # print(f"\n{Fore.CYAN}Перевірка доставності (може бути неточною)...{Style.RESET_ALL}")
            # try:
            #     validate_email(email, check_deliverability=True)
            #     print(f"{Fore.GREEN} [+] Ймовірно, адреса існує (сервер відповів).{Style.RESET_ALL}")
            # except EmailNotValidError as e:
            #     print(f"{Fore.YELLOW} [!] Перевірка доставності не вдалася: {e}{Style.RESET_ALL}")
            # except Exception as e:
            #     print(f"{Fore.RED} [-] Помилка перевірки доставності: {e}{Style.RESET_ALL}"


            print(f"\n{Fore.CYAN}Перевірка репутації (витік даних, спам)...{Style.RESET_ALL}")
            self._perform_reputation_search([f'"{email}" "витік даних"', f'"{email}" "data breach"', f'"{email}" "спам"', f'"{email}" "компрометація"'], "email")

        except EmailNotValidError as e:
             print(f"{Fore.RED}\n [-] Помилка валідації формату: {e}{Style.RESET_ALL}")
        except Exception as e:
             print(f"{Fore.RED}\n [-] Загальна помилка перевірки Email: {e}{Style.RESET_ALL}")
             self.log(f"Email check error for '{email}': {e}")
        input(f"\n{Fore.CYAN}Натисніть Enter...{Style.RESET_ALL}")

    def author_phone_check(self, phone: str = None):
        self.print_banner()
        print(f"{Fore.GREEN}--- Перевірка номера телефону {AUTHOR_WATERMARK} ---{Style.RESET_ALL}")

        phone = phone or self.get_input_with_prompt("Введіть номер (+код країни)", "+380991234567")
        if phone is None:
            return
        self.log(f"Phone Check: {phone}")

        try:
            print(f"\n{Fore.CYAN}Аналіз номера...{Style.RESET_ALL}")
            # Try parsing with a default region if '+' is missing initially
            parsed_num = None
            possible_regions = ['UA', 'PL', 'DE', 'GB', 'US', None] # Add more common regions if needed
            for region in possible_regions:
                try:
                    pn = phonenumbers.parse(phone, region)
                    if phonenumbers.is_valid_number(pn):
                         parsed_num = pn
                         break
                except phonenumberutil.NumberParseException:
                    continue # Try next region if parsing fails

            if parsed_num:
                pn = parsed_num # Use the successfully parsed number
                print(f"{Fore.GREEN} [+] Номер валідний.{Style.RESET_ALL}")
                ctry=geocoder.description_for_number(pn,'uk') or geocoder.description_for_number(pn,'en')
                carr=carrier.name_for_number(pn,'uk') or carrier.name_for_number(pn,'en')
                print(f"{Fore.GREEN} [+] Країна: {ctry}{Style.RESET_ALL}")
                print(f"{Fore.GREEN if carr else Fore.YELLOW} [+] Оператор: {carr or 'Не визначено'}{Style.RESET_ALL}")
                print(f"{Fore.GREEN} [+] Формат E.164: {phonenumbers.format_number(pn, phonenumbers.PhoneNumberFormat.E164)}{Style.RESET_ALL}")
                print(f"{Fore.GREEN} [+] Можливий тип: {phonenumberutil.number_type(pn)}{Style.RESET_ALL}") # MOBILE, FIXED_LINE etc.

                print(f"\n{Fore.CYAN}Перевірка репутації (шахрайство, відгуки)...{Style.RESET_ALL}")
                search_phone = phonenumbers.format_number(pn,phonenumbers.PhoneNumberFormat.E164)
                self._perform_reputation_search([
                    f'"{search_phone}" шахрайство',
                    f'"{search_phone}" scam',
                    f'"{phone}" відгуки',
                    f'хто дзвонив {search_phone}'
                ], "phone")
            else:
                # If parsing failed after trying regions
                print(f"{Fore.RED} [-] Номер не валідний або не вдалося розпізнати формат/регіон.{Style.RESET_ALL}")

        except phonenumberutil.NumberParseException as e:
            # This might catch cases not handled by the loop above
            print(f"{Fore.RED}\n [-] Помилка аналізу номера: {e}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}\n [-] Загальна помилка перевірки номера: {e}{Style.RESET_ALL}")
            self.log(f"Phone check error for '{phone}': {e}")
        input(f"\n{Fore.CYAN}Натисніть Enter...{Style.RESET_ALL}")

    def _format_system_whois(self, whois_text: str):
        formatted = []
        # Extended keywords for better matching
        keywords = [
            "domain name", "registrar", "registration date", "creation date", "created",
            "paid-till", "registry expiry date", "expiration date", "updated date", "last updated",
            "status", "state", "nserver", "name server", "nameserver", "dnssec",
            "registrant", "admin", "tech", "billing", "owner", "holder",
            "org", "organization", "person", "contact", "e-mail", "email", "phone", "fax"
        ]
        # Regex to capture key-value pairs, ignoring case and leading/trailing whitespace
        pattern = re.compile(r"^\s*(" + "|".join(re.escape(k) for k in keywords) + r")\s*:\s*(.*?)\s*$", re.IGNORECASE | re.MULTILINE)
        lines = whois_text.splitlines()
        used = set() # Keep track of lines already processed by regex

        # --- Pass 1: Extract known key-value pairs ---
        found_kv = False
        for match in pattern.finditer(whois_text):
            key = match.group(1).strip().capitalize()
            value = match.group(2).strip()
            if value and value.lower() != "not available" and "REDACTED" not in value.upper():
                # Try to find the original line index to mark it as used
                original_line = match.group(0)
                for i, line in enumerate(lines):
                    if original_line.strip() == line.strip():
                         used.add(i)
                         break
                formatted.append(f"{Fore.GREEN}{key}:{Style.RESET_ALL} {value}")
                found_kv = True

        if found_kv:
            formatted.append("-" * 20) # Separator if K/V pairs were found

        # --- Pass 2: Add remaining relevant lines ---
        skip_phrases = ["terms of use", ">>> last update of whois database", "NOTICE:", "REDACTED FOR PRIVACY"]
        for i, line in enumerate(lines):
            clean = line.strip()
            # Skip if empty, comment, already used, or contains skip phrases
            if not clean or clean.startswith(('%', '#', ';', '*')) or i in used or any(sp in clean.lower() for sp in skip_phrases):
                 continue

            # Avoid adding lines that look like parts of already captured multi-line values (heuristic)
            if i > 0 and i - 1 in used and clean.startswith(' '): # Check previous line was used and this one is indented
                 continue

            # Check if this line IS a key-value pair we missed somehow (unlikely with current regex but good practice)
            is_missed_kv = False
            for kw in keywords:
                if clean.lower().startswith(kw+":"):
                    is_missed_kv = True
                    break
            if not is_missed_kv:
                 formatted.append(clean) # Add the line if it seems relevant and wasn't processed

        return "\n".join(formatted)


    def author_whois(self, domain: str = None):
        self.print_banner()
        print(f"{Fore.GREEN}--- WHOIS інформація {AUTHOR_WATERMARK} ---{Style.RESET_ALL}")
        domain = domain or self.get_input_with_prompt("Введіть домен", "google.com")
        if domain is None: return
        # Basic domain cleaning/validation
        domain = domain.lower().strip().replace("http://", "").replace("https://", "").split('/')[0]
        if not domain: print(f"{Fore.RED}Невірний домен.{Style.RESET_ALL}"); return

        self.log(f"WHOIS: {domain}"); out = None; err = None; method = None

        def get_val(o, a, fb=None):
            """Helper to get attribute value, handling lists and dates."""
            v = getattr(o, a, None)
            if v is None and fb: v = getattr(o, fb, None)

            if isinstance(v, list):
                 # Filter out None or empty strings before joining
                 return ', '.join(filter(None, map(str, v)))
            elif isinstance(v, datetime):
                 return v.strftime('%Y-%m-%d %H:%M:%S') # Include time
            else:
                 return str(v) if v is not None else None

        def format_attr(label, value):
            """Formats attribute if value exists."""
            return f"{Fore.GREEN}{label}:{Style.RESET_ALL} {value}" if value else None

        # --- Attempt 1: python-whois library ---
        if PYTHON_WHOIS_AVAILABLE:
            print(f"{Fore.CYAN}Спроба 1: python-whois...{Style.RESET_ALL}", end='\r')
            try:
                w = whois.query(domain) # May take time
                if w and get_val(w, 'domain_name'): # Check if basic info was returned
                    lines = []
                    lines.append(format_attr("Домен", get_val(w,'domain_name')))
                    lines.append(format_attr("Реєстратор", get_val(w,'registrar')))
                    lines.append(format_attr("Створено", get_val(w,'creation_date')))
                    lines.append(format_attr("Закінчується", get_val(w,'expiration_date')))
                    lines.append(format_attr("Оновлено", get_val(w,'updated_date','last_updated')))
                    lines.append(format_attr("NS сервери", get_val(w,'name_servers')))
                    lines.append(format_attr("Статус", get_val(w,'status')))
                    lines.append(format_attr("Email реєстранта", get_val(w,'emails')))
                    # Add Org/Name if available
                    lines.append(format_attr("Організація", get_val(w,'org')))
                    lines.append(format_attr("Ім'я", get_val(w,'name')))

                    out = "\n".join(filter(None, lines)); method = "python-whois"
                else:
                     # python-whois might return None or an empty object
                     err = "python-whois не повернув даних" if w is None else "python-whois повернув неповні дані"
            except Exception as e:
                 err = f"Помилка python-whois: {e}"
                 self.log(f"python-whois error for {domain}: {err}")
            print(" " * 60, end='\r') # Clear status message

        # --- Attempt 2: System 'whois' command (if python-whois failed or unavailable) ---
        if not out:
             status_msg = f"{Fore.CYAN}Спроба 2: системна 'whois'...{Style.RESET_ALL}"
             if err: status_msg += f" {Fore.YELLOW}(Помилка №1: {err[:50]}...){Style.RESET_ALL}" # Show previous error briefly
             print(status_msg, end='\r')

             whois_cmd = shutil.which('whois')
             if not whois_cmd:
                 err = "Команду 'whois' не знайдено (спробуйте: pkg install whois)"
             else:
                 try:
                     # Use timeout, capture output, handle potential errors
                     p = subprocess.run([whois_cmd, domain], capture_output=True, text=True, timeout=30, check=False, encoding='utf-8', errors='replace')
                 except subprocess.TimeoutExpired:
                      err = f"Системна whois: Таймаут запиту ({domain})"
                 except Exception as e:
                      err = f"Помилка запуску системної whois: {e}"
                 else:
                     if p.returncode == 0 and p.stdout and "No match" not in p.stdout:
                          # **** THIS IS THE CORRECTED PART ****
                          formatted_whois = self._format_system_whois(p.stdout.strip())
                          if formatted_whois: # Check if formatting produced output
                               out = formatted_whois
                               method = "system 'whois'"
                          else:
                               # If formatting failed, show raw output as fallback? Or specific error?
                               err = "Системна whois: Не вдалося відформатувати вивід."
                               # Optional: assign raw output if formatting fails?
                               # out = p.stdout.strip()
                               # method = "system 'whois' (raw)"
                     elif p.stderr:
                          err = f"Системна whois помилка: {p.stderr.strip()}"
                     else:
                          err = f"Системна whois не повернула даних або домен не знайдено ({domain})."
                 self.log(f"System whois result for {domain}: Return Code {p.returncode}, Error: {err}")

             print(" " * 80, end='\r') # Clear status message longer this time

        # --- Display results ---
        if out:
            print(f"\n{Fore.GREEN}[ WHOIS ({method}) для '{domain}' ]{Style.RESET_ALL}\n{out}")
            print(f"\n{Style.DIM+Fore.YELLOW}Примітка: WHOIS не показує піддомени (використовуйте опцію 7). Дані можуть бути приховані (Privacy Protection).{Style.RESET_ALL}")
        elif err:
            print(f"{Fore.RED}\nНе вдалося отримати WHOIS для '{domain}': {err}{Style.RESET_ALL}")
        else:
            # Should not happen if err handling is correct, but as a fallback
            print(f"{Fore.YELLOW}\nНе вдалося отримати WHOIS для '{domain}' (невідома причина).{Style.RESET_ALL}")
        input(f"\n{Fore.CYAN}Натисніть Enter...{Style.RESET_ALL}")


    def author_ip_info(self, ip: str = None):
        self.print_banner()
        print(f"{Fore.GREEN}--- IP Геолокація {AUTHOR_WATERMARK} ---{Style.RESET_ALL}")
        ip = ip or self.get_input_with_prompt("Введіть IP адресу або домен", "1.1.1.1")
        if ip is None: return
        # Basic check if it's an IP or domain
        is_domain = bool(re.match(r"^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", ip))
        target = ip

        if is_domain:
             print(f"{Fore.CYAN}Визначення IP для домену '{ip}'...{Style.RESET_ALL}", end='\r')
             try:
                 ip_addr = dns.resolver.resolve(ip, 'A')[0].to_text()
                 print(" " * 60, end='\r')
                 print(f"{Fore.CYAN}Домен '{ip}' вказує на IP: {ip_addr}{Style.RESET_ALL}")
                 target = ip_addr
                 self.log(f"Resolved domain {ip} to IP {target}")
             except Exception as e:
                 print(" " * 60, end='\r')
                 print(f"{Fore.RED}Не вдалося визначити IP для '{ip}': {e}{Style.RESET_ALL}")
                 self.log(f"Failed to resolve domain {ip}: {e}")
                 input(f"{Fore.CYAN}Натисніть Enter...{Style.RESET_ALL}"); return
        else:
             # Add basic IP validation?
             pass


        self.log(f"Geo IP (ipinfo): {target}")
        if not self.ipinfo_handler:
             print(f"{Fore.RED}Обробник ipinfo не ініціалізовано. Перевірте наявність токена IPINFO_TOKEN.{Style.RESET_ALL}")
             input(f"{Fore.CYAN}Натисніть Enter...{Style.RESET_ALL}"); return

        print(f"{Fore.CYAN}Запит до ipinfo.io для '{target}'...{Style.RESET_ALL}", end='\r')
        try:
            details = self.ipinfo_handler.getDetails(target)
            print(" " * 60, end='\r') # Clear status
            all_details = details.all # Get the raw dictionary

            print(f"\n{Fore.GREEN}[ Дані геолокації для {details.ip} ]{Style.RESET_ALL}")
            print(f"{Fore.GREEN} [+] IP: {details.ip}{Style.RESET_ALL}")
            if all_details.get('hostname'): print(f"{Fore.GREEN} [+] Hostname: {all_details.get('hostname')}{Style.RESET_ALL}")
            if all_details.get('bogon'): print(f"{Fore.YELLOW} [!] Це внутрішня/зарезервована IP адреса (bogon).{Style.RESET_ALL}")
            if all_details.get('anycast'): print(f"{Fore.CYAN} [+] Тип: Anycast{Style.RESET_ALL}")

            # Location
            city = details.city or '?'
            region = details.region or '?'
            country_name = details.country_name or '?'
            country_code = f"({details.country})" if details.country else ""
            print(f"{Fore.GREEN} [+] Локація: {city}, {region}, {country_name} {country_code}{Style.RESET_ALL}")
            print(f"{Fore.GREEN} [+] Координати: {details.latitude or '?'}, {details.longitude or '?'}{Style.RESET_ALL}")
            if all_details.get('postal'): print(f"{Fore.GREEN} [+] Поштовий код: {all_details.get('postal')}{Style.RESET_ALL}")
            print(f"{Fore.GREEN} [+] Часовий пояс: {details.timezone or '?'}{Style.RESET_ALL}")

            # ASN / Organization
            asn_data = all_details.get('asn', {})
            asn_id = asn_data.get('asn', '?')
            asn_name = asn_data.get('name', '?')
            asn_domain = asn_data.get('domain', '')
            asn_type = asn_data.get('type', '')
            print(f"{Fore.GREEN} [+] ASN: {asn_id} ({asn_name}){' Тип: '+asn_type if asn_type else ''}{' Домен: '+asn_domain if asn_domain else ''}{Style.RESET_ALL}")
            # Use 'org' field as fallback/alternative for ASN name
            org_field = all_details.get('org')
            if org_field and org_field != f"{asn_id} {asn_name}": # Show if different from ASN string
                 print(f"{Fore.GREEN} [+] Організація (Org): {org_field}{Style.RESET_ALL}")

            # Company / Carrier Info (if available in token plan)
            company_data = all_details.get('company', {})
            if company_data.get('name'): print(f"{Fore.GREEN} [+] Компанія: {company_data.get('name', '?')}{' ('+company_data.get('type','?')+')' if company_data.get('type') else ''}{Style.RESET_ALL}")
            carrier_data = all_details.get('carrier', {})
            if carrier_data.get('name'): print(f"{Fore.GREEN} [+] Моб. Оператор: {carrier_data.get('name', '?')} (MCC: {carrier_data.get('mcc','?')}, MNC: {carrier_data.get('mnc','?')}){Style.RESET_ALL}")

            # Abuse Contact
            abuse_data = all_details.get('abuse', {})
            if abuse_data.get('email'): print(f"{Fore.YELLOW} [+] Abuse Contact: {abuse_data.get('email', '?')} (тел: {abuse_data.get('phone','?')}){Style.RESET_ALL}")

            # Privacy detection (VPN, Tor, etc. - requires higher tier token usually)
            privacy = all_details.get('privacy', {})
            if privacy.get('vpn'): print(f"{Fore.YELLOW} [!] Виявлено VPN{Style.RESET_ALL}")
            if privacy.get('proxy'): print(f"{Fore.YELLOW} [!] Виявлено Proxy{Style.RESET_ALL}")
            if privacy.get('tor'): print(f"{Fore.YELLOW} [!] Виявлено Tor Exit Node{Style.RESET_ALL}")
            if privacy.get('relay'): print(f"{Fore.YELLOW} [!] Виявлено Relay{Style.RESET_ALL}")
            if privacy.get('hosting'): print(f"{Fore.YELLOW} [!] Ймовірно, хостинг/ЦОД{Style.RESET_ALL}")


        except Exception as e:
            print(" "*60, end='\r')
            print(f"{Fore.RED}\n [-] Помилка запиту до ipinfo.io: {e}{Style.RESET_ALL}")
            self.log(f"ipinfo error for {target}: {e}")
        input(f"\n{Fore.CYAN}Натисніть Enter...{Style.RESET_ALL}")


    def author_subdomain_search(self, domain: str = None):
        self.print_banner()
        print(f"{Fore.GREEN}--- Пошук піддоменів (crt.sh) {AUTHOR_WATERMARK} ---{Style.RESET_ALL}")
        domain = domain or self.get_input_with_prompt("Введіть домен", "example.com")
        if domain is None: return
        domain = domain.lower().strip().replace("http://", "").replace("https://", "").split('/')[0]
        if not domain: print(f"{Fore.RED}Невірний домен.{Style.RESET_ALL}"); return

        self.log(f"Subdomains: {domain}")
        print(f"{Fore.CYAN}Запит до crt.sh для '{domain}'... (Це може зайняти деякий час){Style.RESET_ALL}")
        subs=set()
        # Use %.<domain> to catch subdomains properly
        url=f"https://crt.sh/?q=%.{domain}&output=json"
        try:
            # Increased timeout for potentially large responses
            r=self.session.get(url, timeout=60)
            r.raise_for_status() # Check for HTTP errors like 4xx/5xx

            if not r.text or r.text.strip() == "[]":
                 print(f"{Fore.YELLOW}crt.sh повернув порожню відповідь або не знайдено сертифікатів для '{domain}'.{Style.RESET_ALL}")
                 input(f"{Fore.CYAN}Натисніть Enter...{Style.RESET_ALL}"); return

            try:
                 data=r.json()
            except json.JSONDecodeError:
                  # Handle cases where crt.sh returns HTML error page instead of JSON
                  print(f"{Fore.RED}Помилка: Невірний формат відповіді від crt.sh (не JSON). Можливо, сервіс тимчасово недоступний.{Style.RESET_ALL}")
                  self.log(f"crt.sh non-JSON response for {domain}: {r.text[:200]}") # Log beginning of response
                  input(f"{Fore.CYAN}Натисніть Enter...{Style.RESET_ALL}"); return

            if not data: # Should be redundant after checking r.text, but safe
                print(f"{Fore.YELLOW}Не знайдено сертифікатів для '{domain}'.{Style.RESET_ALL}")
                input(f"{Fore.CYAN}Натисніть Enter...{Style.RESET_ALL}"); return

            for entry in data:
                # Check both common_name and the newline-separated name_value
                names_to_check = []
                cn=entry.get('common_name')
                nv=entry.get('name_value')
                if cn: names_to_check.append(cn)
                if nv: names_to_check.extend(nv.split('\n'))

                for name in names_to_check:
                    name = name.lower().strip()
                    # Check if it's a valid subdomain of the target domain
                    # Ensure it ends with .<domain> or is exactly <domain> (discard later)
                    # Avoid adding the main domain itself or unrelated domains
                    if name.endswith(f".{domain}") or name == domain:
                         # Remove wildcard prefix if present
                         if name.startswith('*.'):
                             name = name[2:]
                         # Basic validation: avoid excessively long names or names with spaces
                         if len(name) < 256 and ' ' not in name and name:
                              subs.add(name)

            subs.discard(domain) # Remove the base domain itself

            if subs:
                 print(f"\n{Fore.GREEN}[ Знайдено піддоменів ({len(subs)}) ]{Style.RESET_ALL}")
                 s_subs=sorted(list(subs))
                 # Attempt to print in columns
                 try:
                     term_width = shutil.get_terminal_size().columns
                     if not s_subs: # Handle case where list is empty after sorting
                          cols = 1
                          width = term_width
                     else:
                          max_len = max(len(s) for s in s_subs) if s_subs else 0
                          width = max_len + 2 # Add padding
                          cols = max(1, term_width // width) if width > 0 else 1
                 except (OSError, ValueError): # Fallback if terminal size fails or max() on empty list
                     cols = 1
                     width = 0 # No padding needed for single column

                 for i in range(0,len(s_subs),cols):
                     print(" ".join(f"{s:<{width if cols>1 else 0}}" for s in s_subs[i:i+cols]))
            else:
                print(f"{Fore.YELLOW}Не знайдено піддоменів через crt.sh.{Style.RESET_ALL}")

        except requests.exceptions.Timeout:
             print(f"{Fore.RED}Помилка: Таймаут запиту до crt.sh.{Style.RESET_ALL}")
             self.log(f"crt.sh timeout for {domain}")
        except requests.exceptions.RequestException as e:
             print(f"{Fore.RED}Помилка мережі crt.sh: {e}{Style.RESET_ALL}")
             self.log(f"crt.sh network error for {domain}: {e}")
        except Exception as e:
             print(f"{Fore.RED}Неочікувана помилка пошуку піддоменів: {e}{Style.RESET_ALL}")
             self.log(f"Subdomain search unexpected error for {domain}: {e}")
        input(f"\n{Fore.CYAN}Натисніть Enter...{Style.RESET_ALL}")


    def author_ai_chat(self):
        self.print_banner()
        print(f"{Fore.GREEN}--- AuthorAI (Hugging Face) {AUTHOR_WATERMARK} ---{Style.RESET_ALL}")

        # Check/Get HF Token
        if not self.hf_token:
            loaded = self.load_hf_token()
            if not loaded:
                validated = self.get_and_validate_hf_token()
                if not validated:
                    print(f"{Fore.RED}Неможливо продовжити без дійсного токена Hugging Face.{Style.RESET_ALL}")
                    input(f"{Fore.CYAN}Натисніть Enter...{Style.RESET_ALL}"); return
                # If validated, self.hf_token should be set

        # Initialize HF Client
        try:
            # Increased timeout for model inference
            client = InferenceClient(token=self.hf_token, timeout=120)
            # Check model availability (optional, might be slow)
            # print(f"{Fore.CYAN}Перевірка доступності моделі {HF_MODEL_ID}...{Style.RESET_ALL}", end='\r')
            # client.list_deployed_models() # Or a similar check if available
            # print(" " * 60, end='\r')
        except Exception as e:
            print(f"{Fore.RED}Помилка ініціалізації Hugging Face Client: {e}{Style.RESET_ALL}")
            self.log(f"HF Client Init Error: {e}")
            input(f"{Fore.CYAN}Натисніть Enter...{Style.RESET_ALL}"); return

        print(f"{Fore.CYAN}Модель: {HF_MODEL_ID}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Введіть 'exit' або 'вихід' для завершення чату.{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Примітка: Відповіді генеруються AI і можуть бути неточними або неповними.{Style.RESET_ALL}")

        # Simple chat history management (limit size)
        chat_history = [] # Store pairs of (user, assistant) messages
        MAX_HISTORY_TOKENS = 2048 # Approximate token limit for context

        while True:
            user_input = self.get_input_with_prompt("Ви", "")
            if user_input is None or user_input.lower() in ['exit', 'вихід', 'quit', '0']: break
            if not user_input.strip(): continue

            self.log(f"HF AI Chat query: {user_input}")

            # Construct prompt with history (using Mistral's preferred format if known)
            # Reference: https://huggingface.co/HuggingFaceH4/zephyr-7b-beta
            prompt_parts = []
            current_token_count = 0
            # Add history in reverse order until token limit
            for role, content in reversed(chat_history):
                 # Rough token estimation (len/4 is a common heuristic)
                 content_tokens = len(content) // 4
                 if current_token_count + content_tokens > MAX_HISTORY_TOKENS:
                     break
                 if role == "user":
                     prompt_parts.insert(0, f"[INST] {content} [/INST]")
                 else:
                     prompt_parts.insert(0, content) # Assistant response follows [/INST]
                 current_token_count += content_tokens

            # Add the latest user message
            user_tokens = len(user_input) // 4
            if current_token_count + user_tokens <= MAX_HISTORY_TOKENS:
                prompt_parts.append(f"[INST] {user_input} [/INST]")
            else:
                 # Handle case where even the new message exceeds limits (unlikely with short prompts)
                 # Or just send the new message without history
                 print(f"{Fore.YELLOW}Історія чату занадто велика, надсилаю тільки останнє повідомлення.{Style.RESET_ALL}")
                 prompt_parts = [f"[INST] {user_input} [/INST]"]


            full_prompt = "".join(prompt_parts) # Combine parts into a single string prompt

            print(f"{Fore.CYAN}Запит до {HF_MODEL_ID}...{Style.RESET_ALL}", end='\r')

            try:
                # Use parameters suitable for Mistral Instruct
                # Reference: https://huggingface.co/docs/huggingface_hub/main/en/package_reference/inference_client#huggingface_hub.InferenceClient.text_generation
                response = client.text_generation(
                    prompt=full_prompt,
                    model=HF_MODEL_ID,
                    max_new_tokens=512, # Max tokens to generate in response
                    do_sample=True,     # Use sampling for more varied output
                    temperature=0.2,    # Control randomness (lower = more focused)
                    top_p=0.95,         # Nucleus sampling (consider only top 95% probability mass)
                    top_k=50,           # Consider top 50 tokens (alternative to top_p)
                    repetition_penalty=1.1 # Penalize repeating tokens slightly
                )
                print(" " * 60, end='\r') # Clear status

                if response:
                    ai_response = response.strip()
                    # Basic formatting/cleanup (optional)
                    ai_response = re.sub(r'\[/INST\].*', '', ai_response).strip() # Remove potential instruction remnants

                    print(f"\n{Fore.MAGENTA}AuthorAI ({HF_MODEL_ID.split('/')[-1]}):{Style.RESET_ALL}\n{ai_response}")

                    # Add user query and AI response to history
                    chat_history.append(("user", user_input))
                    chat_history.append(("assistant", ai_response))

                    # Prune history if too long (based on item count as simple proxy)
                    MAX_HISTORY_ITEMS = 10 # Keep last 5 Q/A pairs
                    if len(chat_history) > MAX_HISTORY_ITEMS * 2:
                        chat_history = chat_history[-(MAX_HISTORY_ITEMS * 2):]

                else:
                    print(f"{Fore.YELLOW}Отримано порожню відповідь від моделі.{Style.RESET_ALL}")

            except HfHubHTTPError as e:
                print(" "*60, end='\r'); print(f"{Fore.RED}Помилка HF API ({e.response.status_code}): {e}{Style.RESET_ALL}")
                self.log(f"HF API Error: {e} - Response: {e.response.text[:200]}") # Log part of the response
                if e.response.status_code == 401: print(f"{Fore.RED}Помилка 401: Неавторизовано. Перевірте ваш токен Hugging Face.{Style.RESET_ALL}"); self.hf_token = None; os.remove(HF_TOKEN_FILE) # Force re-auth
                elif e.response.status_code == 403: print(f"{Fore.YELLOW}Помилка 403: Доступ заборонено. Перевірте права токена або доступ до моделі '{HF_MODEL_ID}'.{Style.RESET_ALL}")
                elif e.response.status_code == 429: print(f"{Fore.YELLOW}Помилка 429: Перевищено ліміт запитів (Rate Limit). Зачекайте.{Style.RESET_ALL}")
                elif e.response.status_code == 503 or "currently loading" in e.response.text.lower(): print(f"{Fore.YELLOW}Помилка 503/Завантаження: Модель '{HF_MODEL_ID}' зараз завантажується або тимчасово недоступна. Спробуйте пізніше.{Style.RESET_ALL}")
                elif e.response.status_code >= 500: print(f"{Fore.YELLOW}Помилка сервера Hugging Face ({e.response.status_code}). Спробуйте пізніше.{Style.RESET_ALL}")
            except Exception as e:
                print(" "*60, end='\r')
                print(f"{Fore.RED}Помилка запиту до AI: {e}{Style.RESET_ALL}")
                self.log(f"HF AI Generic Error: {e}")
        print(f"{Fore.CYAN}Завершення чату AuthorAI.{Style.RESET_ALL}")


    def author_donate(self):
        self.print_banner()
        print(f"{Fore.GREEN}--- Підтримка проєкту {AUTHOR_WATERMARK} ---{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Якщо вам подобається цей інструмент, будь ласка, підтримайте його розвиток!{Style.RESET_ALL}")
        print(f"Ваш донат допоможе покращувати AuthorOSINT та додавати нові функції.")
        print(f"\n{Fore.CYAN}Посилання для підтримки: {DONATE_URL}{Style.RESET_ALL}")
        print("\nНамагаюся відкрити посилання у браузері...")

        opened = False
        # Try termux-open-url first (for Termux environments)
        if 'com.termux' in os.environ.get('PREFIX', ''):
            try:
                process = subprocess.run(['termux-open-url', DONATE_URL], check=False, capture_output=True, text=True, timeout=10)
                if process.returncode == 0:
                    print(f"{Fore.GREEN}Посилання має відкритися у вашому браузері.{Style.RESET_ALL}")
                    opened = True
                else:
                    print(f"{Fore.YELLOW}Не вдалося автоматично відкрити посилання через 'termux-open-url'.{Style.RESET_ALL}")
                    self.log(f"Failed to run termux-open-url (ret {process.returncode}): {process.stderr}")
            except FileNotFoundError:
                print(f"{Fore.YELLOW}Команду 'termux-open-url' не знайдено.{Style.RESET_ALL}")
                self.log("termux-open-url command not found.")
            except subprocess.TimeoutExpired:
                 print(f"{Fore.YELLOW}Таймаут при спробі відкрити посилання через 'termux-open-url'.{Style.RESET_ALL}")
                 self.log("Timeout running termux-open-url.")
            except Exception as e:
                 print(f"{Fore.RED}Сталася помилка при використанні 'termux-open-url': {e}{Style.RESET_ALL}")
                 self.log(f"Error running termux-open-url: {e}")

        # Fallback for other systems (Linux/macOS/Windows if webbrowser works)
        if not opened:
             import webbrowser
             try:
                 if webbrowser.open(DONATE_URL):
                      print(f"{Fore.GREEN}Посилання має відкритися у вашому браузері.{Style.RESET_ALL}")
                      opened = True
                 else:
                     print(f"{Fore.YELLOW}Не вдалося автоматично відкрити посилання через 'webbrowser'.{Style.RESET_ALL}")
                     self.log("webbrowser.open() returned False.")
             except Exception as e:
                 print(f"{Fore.RED}Сталася помилка при використанні 'webbrowser': {e}{Style.RESET_ALL}")
                 self.log(f"Error using webbrowser.open(): {e}")

        # If automatic opening failed
        if not opened:
            print(f"\n{Fore.YELLOW}Будь ласка, відкрийте це посилання вручну у вашому браузері:")
            print(f"{Fore.CYAN}{DONATE_URL}{Style.RESET_ALL}")

        print(f"\n{Fore.YELLOW}Дякую за вашу можливу підтримку!{Style.RESET_ALL}")
        input(f"\n{Fore.CYAN}Натисніть Enter для повернення в меню...{Style.RESET_ALL}")


if __name__ == "__main__":
    # Check if running in Termux and provide a hint
    is_termux = 'com.termux' in os.environ.get('PREFIX', '')
    if is_termux:
        print(f"{Fore.YELLOW}Запуск у Termux. Переконайтесь, що встановлено: 'python', 'git', 'whois', 'openssl'.{Style.RESET_ALL}")
        time.sleep(1.5)

    # Dependency check (basic)
    missing_deps = []
    try: import requests
    except ImportError: missing_deps.append("requests")
    try: from bs4 import BeautifulSoup
    except ImportError: missing_deps.append("beautifulsoup4")
    try: import colorama
    except ImportError: missing_deps.append("colorama")
    try: import phonenumbers
    except ImportError: missing_deps.append("phonenumbers")
    try: from googlesearch import search
    except ImportError: missing_deps.append("googlesearch-python")
    try: import wikipedia
    except ImportError: missing_deps.append("wikipedia-api")
    try: import email_validator
    except ImportError: missing_deps.append("email_validator")
    try: import dns.resolver
    except ImportError: missing_deps.append("dnspython")
    try: from huggingface_hub import InferenceClient
    except ImportError: missing_deps.append("huggingface_hub")
    try: import ipinfo
    except ImportError: missing_deps.append("ipinfo")
    # Optional deps
    # try: import whois; PYTHON_WHOIS_AVAILABLE = True
    # except ImportError: PYTHON_WHOIS_AVAILABLE = False
    # Sherlock check is done inside the function

    if missing_deps:
        print(f"{Fore.RED}ПОМИЛКА: Відсутні необхідні бібліотеки Python!{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Будь ласка, встановіть їх за допомогою pip:")
        print(f"{Fore.CYAN}pip install {' '.join(missing_deps)}")
        if not PYTHON_WHOIS_AVAILABLE:
             print(f"{Fore.CYAN}pip install python-whois  # Опціонально для модуля 5")
        print(f"{Fore.CYAN}pip install sherlock-project # Опціонально для модуля 4")
        sys.exit(1)


    tool = AuthorOSINTLite()

    # Main loop
    while True:
        tool.print_banner()
        print(f"{Fore.GREEN}--- Головне Меню OSINT Lite ---{Style.RESET_ALL}")
        print(f"{Fore.CYAN} 1. {Style.RESET_ALL}Загальний пошук (Google, Wiki)")
        print(f"{Fore.CYAN} 2. {Style.RESET_ALL}Перевірка Номера Телефону")
        print(f"{Fore.CYAN} 3. {Style.RESET_ALL}Перевірка E-mail Адреси")
        print(f"{Fore.CYAN} 4. {Style.RESET_ALL}Пошук Акаунтів за Юзернеймом")
        print(f"{Fore.CYAN} 5. {Style.RESET_ALL}WHOIS Запит для Домену/IP")
        print(f"{Fore.CYAN} 6. {Style.RESET_ALL}Інфо за IP")
        print(f"{Fore.CYAN} 7. {Style.RESET_ALL}Пошук Піддоменів")
        print(f"{Fore.CYAN} 8. {Style.RESET_ALL}AuthorAI Чат")
        print(f"{Fore.YELLOW} 9. {Style.RESET_ALL}Підтримати Проєкт")
        print(f"{Fore.RED} 0. {Style.RESET_ALL}Вихід")
        print(f"{Style.DIM+Fore.GREEN}\n ~ {tool.author_name} OSINT Lite v{tool.version} ~ {Style.RESET_ALL}")

        choice = tool.get_input_with_prompt("Ваш вибір", "1")
        if choice is None: choice = "0" # Handle EOF

        try:
            if choice == "1": tool.author_search()
            elif choice == "2": tool.author_phone_check()
            elif choice == "3": tool.author_email_check()
            elif choice == "4": tool.author_username_check()
            elif choice == "5": tool.author_whois()
            elif choice == "6": tool.author_ip_info()
            elif choice == "7": tool.author_subdomain_search()
            elif choice == "8": tool.author_ai_chat()
            elif choice == "9": tool.author_donate()
            elif choice == "0":
                print(f"{Fore.YELLOW}Завершення роботи... До зустрічі!{Style.RESET_ALL}")
                sys.exit(0)
            else:
                print(f"{Fore.RED}Невірний вибір. Будь ласка, введіть число від 0 до 9.{Style.RESET_ALL}")
                time.sleep(1.5)

        except KeyboardInterrupt:
             print(f"\n{Fore.YELLOW}Перервано користувачем (Ctrl+C)... Завершення.{Style.RESET_ALL}")
             sys.exit(1)
        except Exception as e:
            # Log critical errors and try to continue
            print(f"{Fore.RED}\n--- КРИТИЧНА ПОМИЛКА В ГОЛОВНОМУ ЦИКЛІ ---{Style.RESET_ALL}")
            print(f"{Fore.RED}Тип: {type(e).__name__}, Повідомлення: {e}{Style.RESET_ALL}")
            import traceback
            tb=traceback.format_exc()
            print(f"{Fore.YELLOW}\nДеталі помилки:\n{tb}{Style.RESET_ALL}")
            tool.log(f"КРИТИЧНА ПОМИЛКА (Lite Main Loop): {type(e).__name__} - {e}\nTRACEBACK:\n{tb}")
            input(f"{Fore.CYAN}Сталася неочікувана помилка. Натисніть Enter для спроби повернення в меню...{Style.RESET_ALL}")
