from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box
from rich.prompt import IntPrompt, Prompt
from rich.align import Align
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from art import text2art
import time
import requests
from datetime import datetime
from geopy.geocoders import Nominatim
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
import os
import platform
import json
import csv
import shutil
import uuid

console = Console()

# DaData API configuration
DADATA_API_TOKEN = "b293b21b89479e85df4d0ab1007d34e4e4961712"
DADATA_API_SECRET = "29879ff4cc4c0679d8cf2f98a21be4f983c2b53d"
DADATA_URL = "https://suggestions.dadata.ru/suggestions/api/4_1/rs/suggest/party"
dadata_headers = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Authorization": f"Token {DADATA_API_TOKEN}",
    "X-Secret": DADATA_API_SECRET
}

# LeakOsint API configuration
LEAKOSINT_TOKEN = '7949201327:7z2O7xWq'
LEAKOSINT_URL = 'https://leakosintapi.com/'

# Local database configuration
DATA_FOLDER = "data"

# Константы для анализа номера телефона
ABSTRACT_API_KEY_PHONE = "ed76df700b40404b853cdf9f30e0aef6"
NUMVERIFY_API_KEY = "2d3c0b9d3739a135bd499f5e83094603"
HEADERS_PHONE = {
    "User-Agent": "phone-analysis-script/1.2"
}

def query_abstract(phone, api_key):
    if not api_key:
        return None
    url = "https://phonevalidation.abstractapi.com/v1/"
    params = {"api_key": api_key, "phone": phone}
    try:
        resp = requests.get(url, params=params, headers=HEADERS_PHONE, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException:
        return None

def query_numverify(phone, api_key):
    if not api_key:
        return None
    url = "http://apilayer.net/api/validate"
    params = {"access_key": api_key, "number": phone, "format": 1}
    try:
        resp = requests.get(url, params=params, headers=HEADERS_PHONE, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException:
        return None

def pretty_print_results(phone, abstract_res, numverify_res):
    sep = '_' * 60
    result_text = f"{sep}\nАнализ номера: {phone}\n{sep}\n"
    
    if abstract_res:
        result_text += "AbstractAPI:\n"
        result_text += f"    [+] Номер: {abstract_res.get('phone')}\n"
        result_text += f"    [+] Валидный: {abstract_res.get('valid')}\n"
        fmt = abstract_res.get('format', {})
        if fmt:
            result_text += f"    [+] International: {fmt.get('international')}\n"
            result_text += f"    [+] Local: {fmt.get('local')}\n"
        country = abstract_res.get('country') or {}
        if country:
            result_text += f"    [+] Страна: {country.get('name')} ({country.get('code')}) +{country.get('prefix')}\n"
        result_text += f"    [+] Локация: {abstract_res.get('location')}\n"
        result_text += f"    [+] Тип линии: {abstract_res.get('type')}\n"
        result_text += f"    [+] Оператор: {abstract_res.get('carrier')}\n"
    else:
        result_text += "AbstractAPI: нет данных\n"
    
    result_text += f"{sep}\n"
    
    if numverify_res:
        result_text += "NumVerify:\n"
        result_text += f"    [+] Номер: {numverify_res.get('number')}\n"
        result_text += f"    [+] Валидный: {numverify_res.get('valid')}\n"
        result_text += f"    [+] Международный: {numverify_res.get('international_format')}\n"
        result_text += f"    [+] Локальный: {numverify_res.get('local_format')}\n"
        result_text += f"    [+] Страна: {numverify_res.get('country_name')} ({numverify_res.get('country_code')})\n"
        result_text += f"    [+] Локация: {numverify_res.get('location')}\n"
        result_text += f"    [+] Тип линии: {numverify_res.get('line_type')}\n"
        result_text += f"    [+] Оператор: {numverify_res.get('carrier')}\n"
    else:
        result_text += "NumVerify: нет данных\n"
    
    result_text += sep
    return result_text

def analyze_phone():
    console.print("\n[bold cyan]Введите номер телефона для анализа:[/bold cyan]")
    phone = Prompt.ask("Номер")
    with Progress(transient=True) as progress:
        task = progress.add_task("[cyan]Анализ номера...", total=100)
        for _ in range(100):
            progress.update(task, advance=1)
            time.sleep(0.02)
    abstract_res = query_abstract(phone, ABSTRACT_API_KEY_PHONE)
    time.sleep(0.35)
    numverify_res = query_numverify(phone, NUMVERIFY_API_KEY)
    result_text = pretty_print_results(phone, abstract_res, numverify_res)
    result_panel = Panel(
        Text(result_text, style="white"),
        title="[bold bright_magenta]Результат анализа[/bold bright_magenta]",
        border_style="green",
        box=box.ROUNDED,
        padding=(1, 2),
        width=80
    )
    console.print(result_panel)
    console.input("\n[yellow]Нажмите Enter для возврата в меню...[/yellow]")

# Константы для анализа email
ABSTRACT_API_KEY_EMAIL = "6e7b9deb434b4b4a88ff808260725343"

def format_field(field):
    if isinstance(field, dict):
        return field.get('text') or field.get('value')
    return field or 'N/A'

def analyze_email_func():
    console.print("\n[bold cyan]Введите email для анализа:[/bold cyan]")
    email = Prompt.ask("Email")
    url = f"https://emailvalidation.abstractapi.com/v1/?api_key={ABSTRACT_API_KEY_EMAIL}&email={email}"
    with Progress(transient=True) as progress:
        task = progress.add_task("[cyan]Анализ email...", total=100)
        for _ in range(100):
            progress.update(task, advance=1)
            time.sleep(0.02)
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        result_text = f"{'_' * 50}\n"
        result_text += f" [+] Email: {format_field(data.get('email'))}\n"
        result_text += f" [+] Valid Format: {format_field(data.get('is_valid_format'))}\n"
        result_text += f" [+] Deliverable: {format_field(data.get('is_deliverable'))}\n"
        result_text += f" [+] SMTP Check Passed: {format_field(data.get('is_smtp_valid'))}\n"
        result_text += f" [+] Free Email Provider: {format_field(data.get('is_free_email'))}\n"
        result_text += f" [+] Disposable: {format_field(data.get('is_disposable_email'))}\n"
        result_text += f" [+] Domain: {format_field(data.get('domain'))}\n"
        result_text += f" [+] MX Found: {format_field(data.get('is_mx_found'))}\n"
        result_text += f" [+] Role-based Email: {format_field(data.get('is_role_email'))}\n"
        result_text += f" [+] Syntax Valid: {format_field(data.get('is_valid_format'))}\n"
        result_text += f" [+] Email Type: {format_field(data.get('email_type'))}\n"
        result_text += f" [+] Confidence Score: {format_field(data.get('quality_score'))}\n"
        result_text += f"{'_' * 50}"
        result_panel = Panel(
            Text(result_text, style="white"),
            title="[bold bright_magenta]Результат анализа email[/bold bright_magenta]",
            border_style="green",
            box=box.ROUNDED,
            padding=(1, 2),
            width=80
        )
        console.print(result_panel)
    except requests.RequestException as e:
        error_panel = Panel(
            Text(f" [-] Request Error: {e}", style="red"),
            title="[bold bright_magenta]Ошибка[/bold bright_magenta]",
            border_style="red",
            box=box.ROUNDED,
            padding=(1, 2),
            width=80
        )
        console.print(error_panel)
    console.input("\n[yellow]Нажмите Enter для возврата в меню...[/yellow]")

# Константы для анализа IP
IPGEO_API_KEY = "178e08dfc89f46a28ee1cff258e41bcb"

def search_ip_func():
    console.print("\n[bold cyan]Введите IP-адрес для анализа:[/bold cyan]")
    ip = Prompt.ask("IP-адрес")
    with Progress(transient=True) as progress:
        task = progress.add_task("[cyan]Анализ IP...", total=100)
        for _ in range(100):
            progress.update(task, advance=1)
            time.sleep(0.02)
    
    result_text = f"{'_' * 50}\n"
    result_text += f"IP Search: {ip}\n"
    result_text += f"{'_' * 50}\n"
    
    try:
        response_ipapi = requests.get(f"http://ip-api.com/json/{ip}?fields=status,message,country,regionName,city,zip,lat,lon,isp,org,as,query")
        data_ipapi = response_ipapi.json()
        if data_ipapi.get("status") == "success":
            result_text += f" [+] IP: {data_ipapi.get('query')}\n"
            result_text += f" [+] Country: {data_ipapi.get('country')}\n"
            result_text += f" [+] Region: {data_ipapi.get('regionName')}\n"
            result_text += f" [+] City: {data_ipapi.get('city')}\n"
            result_text += f" [+] ZIP: {data_ipapi.get('zip')}\n"
            result_text += f" [+] Latitude/Longitude: {data_ipapi.get('lat')}/{data_ipapi.get('lon')}\n"
            result_text += f" [+] ISP: {data_ipapi.get('isp')}\n"
            result_text += f" [+] Organization: {data_ipapi.get('org')}\n"
            result_text += f" [+] AS: {data_ipapi.get('as')}\n"
        else:
            result_text += f"- [+] ip-api.com Error: {data_ipapi.get('message')}\n"
    except Exception as e:
        result_text += f" ip-api.com Exception: {e}\n"
    
    result_text += f"{'_' * 50}\n"
    
    try:
        response_geo = requests.get(
            f"https://api.ipgeolocation.io/ipgeo?apiKey={IPGEO_API_KEY}&ip={ip}"
        )
        data_geo = response_geo.json()
        result_text += f" [+] IP: {data_geo.get('ip')}\n"
        result_text += f" [+] Country: {data_geo.get('country_name')}\n"
        result_text += f" [+] Region: {data_geo.get('state_prov')}\n"
        result_text += f" [+] City: {data_geo.get('city')}\n"
        result_text += f" [+] ZIP: {data_geo.get('zipcode')}\n"
        result_text += f" [+] Latitude/Longitude: {data_geo.get('latitude')}/{data_geo.get('longitude')}\n"
        result_text += f" [+] ISP: {data_geo.get('isp')}\n"
        result_text += f" [+] Organization: {data_geo.get('organization')}\n"
        result_text += f" [+] ASN: {data_geo.get('asn')}\n"
        result_text += f" [+] Timezone: {data_geo.get('time_zone', {}).get('name')}\n"
        result_text += f" [+] Threats: {data_geo.get('threat', {})}\n"
    except Exception as e:
        result_text += f"- [+] IPGeolocation.io Exception: {e}\n"
    
    result_text += f"{'_' * 50}"
    
    result_panel = Panel(
        Text(result_text, style="white"),
        title="[bold bright_magenta]Результат анализа IP[/bold bright_magenta]",
        border_style="green",
        box=box.ROUNDED,
        padding=(1, 2),
        width=80
    )
    console.print(result_panel)
    console.input("\n[yellow]Нажмите Enter для возврата в меню...[/yellow]")

# Константы для поиска по ВК
VK_TOKEN = "0af157510af157510af15751aa0a89e69600af10af157516a0bc15996e74fe2b440998c"
VK_API_VERSION = "5.131"

def vk_api(method, params):
    url = f"https://api.vk.com/method/{method}"
    params.update({"access_token": VK_TOKEN, "v": VK_API_VERSION})
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        if "error" in data:
            console.print(f"[red]Ошибка VK API: {data['error']['error_msg']}[/red]")
            return None
        return data.get("response")
    except requests.RequestException as e:
        console.print(f"[red]Ошибка запроса: {e}[/red]")
        return None

def vk_search_func():
    console.print("\n[bold cyan]Введите ID или короткое имя пользователя ВКонтакте:[/bold cyan]")
    user_input = Prompt.ask("ID или имя")
    with Progress(transient=True) as progress:
        task = progress.add_task("[cyan]Поиск в ВК...", total=100)
        for _ in range(100):
            progress.update(task, advance=1)
            time.sleep(0.02)
    
    user = vk_api("users.get", {"user_ids": user_input, "fields": "bdate,city,country,home_town,contacts,photo_200,status,relation,followers_count,occupation,domain"})
    if not user:
        error_panel = Panel(
            Text(" [-] Пользователь не найден или ошибка VK API", style="red"),
            title="[bold bright_magenta]Ошибка[/bold bright_magenta]",
            border_style="red",
            box=box.ROUNDED,
            padding=(1, 2),
            width=80
        )
        console.print(error_panel)
        console.input("\n[yellow]Нажмите Enter для возврата в меню...[/yellow]")
        return
    
    user_data = user[0]
    friends = vk_api("friends.get", {"user_id": user_data["id"], "fields": "domain"}) or {}
    groups = vk_api("groups.get", {"user_id": user_data["id"], "extended": 1}) or {}
    posts = vk_api("wall.get", {"owner_id": user_data["id"], "count": 5}) or {}
    
    friends_list = friends.get("items", [])
    groups_list = groups.get("items", [])
    posts_list = posts.get("items", [])
    
    result_text = f"{'_' * 50}\n"
    result_text += f"VK OSINT: {user_data.get('first_name')} {user_data.get('last_name')}\n"
    result_text += f"{'_' * 50}\n"
    result_text += f" [+] ID: {user_data.get('id')}\n"
    result_text += f" [+] Имя: {user_data.get('first_name')} {user_data.get('last_name')}\n"
    result_text += f" [+] Дата рождения: {user_data.get('bdate')}\n"
    result_text += f" [+] Город: {user_data.get('city', {}).get('title')}\n"
    result_text += f" [+] Страна: {user_data.get('country', {}).get('title')}\n"
    result_text += f" [+] Родной город: {user_data.get('home_town')}\n"
    result_text += f" [+] Статус: {user_data.get('status')}\n"
    result_text += f" [+] Подписчики: {user_data.get('followers_count')}\n"
    result_text += f" [+] Профессия: {user_data.get('occupation', {}).get('name')}\n"
    result_text += f" [+] Ссылка: https://vk.com/{user_data.get('domain')}\n"
    result_text += f" [+] Фото: {user_data.get('photo_200')}\n"
    result_text += f" [+] Друзей: {len(friends_list)}\n"
    result_text += f" [+] Групп: {len(groups_list)}\n"
    result_text += f" [+] Последних постов: {len(posts_list)}\n"
    result_text += f"{'_' * 50}\n"
    
    # Генерация HTML-отчёта
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html = f"""
    <html>
    <head>
        <title>OSINT VK Report - {user_data.get('first_name')} {user_data.get('last_name')}</title>
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px; }}
            h2 {{ color: #333; }}
            .section {{ background-color: #fff; padding: 15px; margin-bottom: 20px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
            .item {{ margin-bottom: 10px; }}
            a {{ color: #1a73e8; text-decoration: none; }}
        </style>
    </head>
    <body>
        <h1>OSINT VK Report</h1>
        <p>Дата создания: {now}</p>
        <div class="section">
            <h2>Пользователь</h2>
            <div class="item"><b>ID:</b> {user_data.get('id')}</div>
            <div class="item"><b>Имя:</b> {user_data.get('first_name')} {user_data.get('last_name')}</div>
            <div class="item"><b>Дата рождения:</b> {user_data.get('bdate')}</div>
            <div class="item"><b>Город:</b> {user_data.get('city', {}).get('title')}</div>
            <div class="item"><b>Страна:</b> {user_data.get('country', {}).get('title')}</div>
            <div class="item"><b>Родной город:</b> {user_data.get('home_town')}</div>
            <div class="item"><b>Статус:</b> {user_data.get('status')}</div>
            <div class="item"><b>Подписчики:</b> {user_data.get('followers_count')}</div>
            <div class="item"><b>Профессия:</b> {user_data.get('occupation', {}).get('name')}</div>
            <div class="item"><b>Ссылка:</b> <a href="https://vk.com/{user_data.get('domain')}" target="_blank">vk.com/{user_data.get('domain')}</a></div>
            <div class="item"><img src="{user_data.get('photo_200')}" alt="Фото"></div>
        </div>
        <div class="section">
            <h2>Друзья ({len(friends_list)})</h2>
            {"<br>".join([f'<a href="https://vk.com/{f.get("domain")}">{f.get("first_name")} {f.get("last_name")}</a>' for f in friends_list])}
        </div>
        <div class="section">
            <h2>Группы ({len(groups_list)})</h2>
            {"<br>".join([f'<a href="https://vk.com/club{g.get("id")}">{g.get("name")}</a>' for g in groups_list])}
        </div>
        <div class="section">
            <h2>Последние посты</h2>
            {"<br>".join([f'<div><b>Дата:</b> {datetime.fromtimestamp(p["date"]).strftime("%Y-%m-%d %H:%M:%S")}<br>{p.get("text","")}</div><hr>' for p in posts_list])}
        </div>
    </body>
    </html>
    """
    with open("vk_report.html", "w", encoding="utf-8") as f:
        f.write(html)
    result_text += "HTML-отчёт vk_report.html создан!\n"
    result_text += f"{'_' * 50}"
    
    result_panel = Panel(
        Text(result_text, style="white"),
        title="[bold bright_magenta]Результат поиска ВК[/bold bright_magenta]",
        border_style="green",
        box=box.ROUNDED,
        padding=(1, 2),
        width=80
    )
    console.print(result_panel)
    console.input("\n[yellow]Нажмите Enter для возврата в меню...[/yellow]")

# Функция поиска по геокоординатам
def generate_map_links(lat, lon):
    links = {
        "Google Maps": f"https://www.google.com/maps/search/?api=1&query={lat},{lon}",
        "Yandex Maps": f"https://yandex.com/maps/?ll={lon}%2C{lat}&z=17",
        "2GIS": f"https://2gis.com/geo/{lat},{lon}"
    }
    return links

def search_geo_func():
    console.print("\n[bold cyan]Выберите режим поиска:[/bold cyan]")
    console.print("1 - По адресу")
    console.print("2 - По координатам (широта/долгота)")
    choice = Prompt.ask("Введите 1 или 2", choices=["1", "2"], show_choices=False)
    geolocator = Nominatim(user_agent="geo_search_app")
    with Progress(transient=True) as progress:
        task = progress.add_task("[cyan]Поиск...", total=100)
        for _ in range(100):
            progress.update(task, advance=1)
            time.sleep(0.02)
    
    result_text = f"{'_' * 50}\n"
    result_text += "Результат поиска\n"
    result_text += f"{'_' * 50}\n"
    
    if choice == "1":
        address = Prompt.ask("Введите адрес")
        location = geolocator.geocode(address)
        if location:
            result_text += f" [+] Адрес: {location.address}\n"
            result_text += f" [+] Координаты: {location.latitude}, {location.longitude}\n"
            addr = location.raw.get('address', {})
            result_text += f" [+] Страна: {addr.get('country', 'Не найдено')}\n"
            result_text += f" [+] Город: {addr.get('city', addr.get('town', addr.get('village', 'Не найдено')))}\n"
            result_text += f" [+] Улица: {addr.get('road', 'Не найдено')}\n"
            result_text += f" [+] Почтовый индекс: {addr.get('postcode', 'Не найдено')}\n"
            links = generate_map_links(location.latitude, location.longitude)
            result_text += f"\nСсылки на карты:\n"
            for name, link in links.items():
                result_text += f" [+] {name}: {link}\n"
        else:
            result_text += " [-] Адрес не найден.\n"
    elif choice == "2":
        try:
            lat = float(Prompt.ask("Введите широту"))
            lon = float(Prompt.ask("Введите долготу"))
            location = geolocator.reverse((lat, lon))
            if location:
                result_text += f" [+] Координаты: {lat}, {lon}\n"
                result_text += f" [+] Адрес: {location.address}\n"
                addr = location.raw.get('address', {})
                result_text += f" [+] Страна: {addr.get('country', 'Не найдено')}\n"
                result_text += f" [+] Город: {addr.get('city', addr.get('town', addr.get('village', 'Не найдено')))}\n"
                result_text += f" [+] Улица: {addr.get('road', 'Не найдено')}\n"
                result_text += f" [+] Почтовый индекс: {addr.get('postcode', 'Не найдено')}\n"
                links = generate_map_links(lat, lon)
                result_text += f"\nСсылки на карты:\n"
                for name, link in links.items():
                    result_text += f" [+] {name}: {link}\n"
            else:
                result_text += " [-] Местоположение не найдено.\n"
        except ValueError:
            result_text += " [-] Неверный формат координат.\n"
    else:
        result_text += " [-] Неверный выбор.\n"
    
    result_text += f"{'_' * 50}"
    
    result_panel = Panel(
        Text(result_text, style="white"),
        title="[bold bright_magenta]Результат поиска по гео[/bold bright_magenta]",
        border_style="green",
        box=box.ROUNDED,
        padding=(1, 2),
        width=80
    )
    console.print(result_panel)
    console.input("\n[yellow]Нажмите Enter для возврата в меню...[/yellow]")

# Функция поиска по нику
class SocialMediaFinder:
    def __init__(self):
        self.platforms = {
            'GitHub': 'https://github.com/{}',
            'Twitter': 'https://twitter.com/{}',
            'Instagram': 'https://instagram.com/{}',
            'Reddit': 'https://reddit.com/user/{}',
            'VK': 'https://vk.com/{}',
            'Telegram': 'https://t.me/{}',
            'YouTube': 'https://youtube.com/{}',
            'Pinterest': 'https://pinterest.com/{}',
            'Tumblr': 'https://{}.tumblr.com',
            'DeviantArt': 'https://{}.deviantart.com',
            'Flickr': 'https://flickr.com/people/{}',
            'SoundCloud': 'https://soundcloud.com/{}',
            'Medium': 'https://medium.com/@{}',
            'Dribbble': 'https://dribbble.com/{}',
            'Behance': 'https://behance.net/{}',
            'Facebook': 'https://facebook.com/{}',
            'Discord': 'https://discord.com/users/{}'
        }

    def check_profile(self, platform, url_template, username):
        try:
            url = url_template.format(username)
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                return {
                    'platform': platform,
                    'username': username,
                    'url': url,
                    'status': 'found',
                    'status_code': response.status_code
                }
            elif response.status_code == 404:
                return {
                    'platform': platform,
                    'username': username,
                    'url': url,
                    'status': 'not_found',
                    'status_code': response.status_code
                }
            else:
                return {
                    'platform': platform,
                    'username': username,
                    'url': url,
                    'status': 'unknown',
                    'status_code': response.status_code
                }
        except requests.exceptions.RequestException as e:
            return {
                'platform': platform,
                'username': username,
                'url': url_template.format(username),
                'status': 'error',
                'error': str(e)
            }

    def search_username(self, username):
        results = []
        found_count = 0
        with Progress(
            transient=True
        ) as progress:
            task = progress.add_task("Поиск профилей...", total=len(self.platforms))
            with ThreadPoolExecutor(max_workers=10) as executor:
                future_to_platform = {
                    executor.submit(self.check_profile, platform, url_template, username): platform
                    for platform, url_template in self.platforms.items()
                }
                for future in as_completed(future_to_platform):
                    platform = future_to_platform[future]
                    try:
                        result = future.result()
                        results.append(result)
                        if result['status'] == 'found':
                            found_count += 1
                    except Exception as e:
                        results.append({
                            'platform': platform,
                            'username': username,
                            'url': self.platforms[platform].format(username),
                            'status': 'error',
                            'error': str(e)
                        })
                    progress.update(task, advance=1)
        return results, found_count

    def print_results(self, results, found_count):
        table = Table(show_header=True, header_style="bold magenta", box=box.MINIMAL_DOUBLE_HEAD)
        table.add_column("Статус", style="dim", width=12)
        table.add_column("Платформа", width=15)
        table.add_column("URL", overflow="fold")
        for result in results:
            if result['status'] == 'found':
                table.add_row("[+] Найден", result['platform'], result['url'], style="green")
            elif result['status'] == 'not_found':
                table.add_row("[-] Не найден", result['platform'], "N/A", style="red")
            elif result['status'] == 'error':
                table.add_row("[!] Ошибка", result['platform'], result.get('error', 'Unknown error'), style="yellow")
            else:
                table.add_row("[?] Неизвестно", result['platform'], f"Status: {result.get('status_code', 'N/A')}", style="blue")
        return table, f"Всего проверено: {len(results)}\nНайдено профилей: {found_count}"

def search_nick_func():
    console.print("\n[bold cyan]Введите ник для поиска:[/bold cyan]")
    username = Prompt.ask("Ник")
    if not username:
        error_panel = Panel(
            Text(" [-] Ошибка: Пустое имя пользователя", style="red"),
            title="[bold bright_magenta]Ошибка[/bold bright_magenta]",
            border_style="red",
            box=box.ROUNDED,
            padding=(1, 2),
            width=80
        )
        console.print(error_panel)
        console.input("\n[yellow]Нажмите Enter для возврата в меню...[/yellow]")
        return

    console.print(f"[blue]Ищем профили для: {username}[/blue]")
    console.print("[yellow]Пожалуйста, подождите...[/yellow]")
    
    finder = SocialMediaFinder()
    start_time = time.time()
    results, found_count = finder.search_username(username)
    end_time = time.time()
    
    table, summary = finder.print_results(results, found_count)
    
    result_panel = Panel(
        table,
        title="[bold bright_magenta]Результаты поиска[/bold bright_magenta]",
        border_style="green",
        box=box.ROUNDED,
        padding=(1, 2),
        width=80
    )
    console.print(result_panel)
    
    summary_panel = Panel(
        Text(summary, style="white"),
        title="[bold bright_magenta]Сводка[/bold bright_magenta]",
        border_style="blue",
        box=box.ROUNDED,
        padding=(1, 2),
        width=80
    )
    console.print(summary_panel)
    console.print(f"[blue]Время поиска: {end_time - start_time:.2f} секунд[/blue]")
    
    console.print("\n[yellow]Нажмите Enter для возврата в меню...[/yellow]")
    console.input()

# Функция поиска по судебным делам
def clear_screen():
    if platform.system() == "Windows":
        os.system('cls')
    else:
        os.system('clear')

def print_header(title):
    console = Console()
    console.print(f"\n{title}")
    console.print("-" * len(title))

def save_to_json(data, filename=None):
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"search_results_{timestamp}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return filename

def sudrf_search(name):
    results = {
        "source": "sudrf.ru",
        "query": name,
        "timestamp": datetime.now().isoformat(),
        "results": []
    }
    url = f"https://sudrf.ru/index.php?id=300&search%5Bname%5D={name.replace(' ', '+')}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        html_results = soup.find_all("div", class_="result-item")
        if not html_results:
            results["status"] = "no_results"
            return results
        results["status"] = "success"
        results["count"] = len(html_results)
        for i, res in enumerate(html_results[:10], 1):
            text = res.get_text(strip=True)
            if text:
                text = ' '.join(text.split())
                results["results"].append({
                    "id": i,
                    "text": text
                })
    except requests.exceptions.RequestException as e:
        results["status"] = "network_error"
        results["error"] = str(e)
    except Exception as e:
        results["status"] = "error"
        results["error"] = str(e)
    return results

def kad_arbitr_search(name):
    results = {
        "source": "kad.arbitr.ru",
        "query": name,
        "timestamp": datetime.now().isoformat(),
        "results": []
    }
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Content-Type": "application/json",
    }
    try:
        session.get("https://kad.arbitr.ru", headers=headers, timeout=10)
        payload = {
            "CaseNumber": "",
            "Participant": name,
            "DateFrom": None,
            "DateTo": None,
            "CourtCode": None,
            "Judge": None,
            "WithVKSInstances": False,
            "Page": 1
        }
        response = session.post(
            "https://kad.arbitr.ru/Search/Results",
            headers=headers,
            json=payload,
            timeout=15
        )
        response.raise_for_status()
        data = response.json()
        items = data.get("Result", {}).get("Items", [])
        if not items:
            results["status"] = "no_results"
            return results
        results["status"] = "success"
        results["count"] = len(items)
        for i, item in enumerate(items[:10], 1):
            results["results"].append({
                "id": i,
                "case_number": item.get('CaseNumber'),
                "court_name": item.get('CourtName'),
                "date": item.get('Date')
            })
    except requests.exceptions.RequestException as e:
        results["status"] = "network_error"
        results["error"] = str(e)
    except Exception as e:
        results["status"] = "error"
        results["error"] = str(e)
    return results

def fssp_search(name):
    results = {
        "source": "fssp.gov.ru",
        "query": name,
        "timestamp": datetime.now().isoformat(),
        "results": []
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }
    try:
        payload = {
            "is": "physical",
            "is_name": name,
            "is_address": "",
            "is_id_number": "",
            "is_birth_date": "",
            "is_doc_number": "",
            "is_region_id": "0"
        }
        response = requests.post(
            "https://fssp.gov.ru/iss/ip_search/",
            headers=headers,
            data=payload,
            timeout=15
        )
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        html_results = soup.find_all("div", class_="search-result-item")
        if not html_results:
            results["status"] = "no_results"
            return results
        results["status"] = "success"
        results["count"] = len(html_results)
        for i, result in enumerate(html_results[:5], 1):
            text = result.get_text(strip=True)
            if text:
                text = ' '.join(text.split())
                results["results"].append({
                    "id": i,
                    "text": text
                })
    except requests.exceptions.RequestException as e:
        results["status"] = "network_error"
        results["error"] = str(e)
    except Exception as e:
        results["status"] = "error"
        results["error"] = str(e)
    return results

def nalog_ip_search(name):
    results = {
        "source": "nalog.ru",
        "query": name,
        "timestamp": datetime.now().isoformat(),
        "results": []
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Content-Type": "application/json",
    }
    try:
        response = requests.post(
            "https://egrul.nalog.ru/",
            json={"query": name, "vyp3CaptchaToken": ""},
            headers=headers,
            timeout=15
        )
        response.raise_for_status()
        data = response.json()
        request_id = data.get("t")
        if not request_id:
            results["status"] = "no_request_id"
            return results
        time.sleep(2)
        response2 = requests.get(
            f"https://egrul.nalog.ru/search-result/{request_id}",
            headers=headers,
            timeout=15
        )
        response2.raise_for_status()
        result_data = response2.json()
        rows = result_data.get("rows", [])
        if not rows:
            results["status"] = "no_results"
            return results
        results["status"] = "success"
        results["count"] = len(rows)
        for i, row in enumerate(rows[:5], 1):
            results["results"].append({
                "id": i,
                "name": row.get('n'),
                "inn": row.get('i'),
                "ogrn": row.get('o'),
                "address": row.get('a')
            })
    except requests.exceptions.RequestException as e:
        results["status"] = "network_error"
        results["error"] = str(e)
    except Exception as e:
        results["status"] = "error"
        results["error"] = str(e)
    return results

def display_results(results, source_name):
    result_text = f"\n{source_name}\n"
    if results["status"] == "success" and results["results"]:
        result_text += f"найдено: {results['count']}\n"
        for result in results["results"]:
            if "text" in result:
                result_text += f"{result['id']}. {result['text']}\n"
            elif "case_number" in result:
                result_text += f"{result['id']}. дело №{result['case_number']}\n"
                result_text += f"   суд: {result['court_name']}\n"
                if result['date']:
                    result_text += f"   дата: {result['date']}\n"
            elif "name" in result:
                result_text += f"{result['id']}. {result['name']}\n"
                result_text += f"   инн: {result['inn']}\n"
                if result['address']:
                    result_text += f"   адрес: {result['address']}\n"
    elif results["status"] == "no_results":
        result_text += "ничего не найдено\n"
    else:
        result_text += f"ошибка: {results.get('error', 'неизвестная ошибка')}\n"
    return result_text

def search_sud_func():
    console.print("\n[bold cyan]Выберите тип поиска:[/bold cyan]")
    console.print("1. Поиск по ФИО")
    console.print("2. Поиск по ИНН")
    choice = Prompt.ask("введите вариант", choices=["1", "2"], show_choices=False)
    
    if choice == "1":
        query = Prompt.ask("введите фио для поиска").strip()
        search_type = "фио"
    elif choice == "2":
        query = Prompt.ask("введите инн для поиска").strip()
        search_type = "инн"
    else:
        console.print("[red]неверный выбор[/red]")
        console.input("\n[yellow]Нажмите Enter для возврата в меню...[/yellow]")
        return
    
    if not query:
        console.print("[red]запрос не может быть пустым[/red]")
        console.input("\n[yellow]Нажмите Enter для возврата в меню...[/yellow]")
        return

    with Progress(transient=True) as progress:
        task = progress.add_task("Поиск судебных дел...", total=100)
        for _ in range(100):
            progress.update(task, advance=1)
            time.sleep(0.02)
    
    all_results = {
        "search_query": query,
        "search_type": search_type,
        "timestamp": datetime.now().isoformat(),
        "sources": {}
    }

    result_text = f"{'_' * 50}\n"
    result_text += f"Результаты поиска: {query}\n"
    result_text += f"{'_' * 50}\n"
    
    sudrf_data = sudrf_search(query)
    all_results["sources"]["sudrf"] = sudrf_data
    result_text += display_results(sudrf_data, "суды общей юрисдикции")
    
    kad_data = kad_arbitr_search(query)
    all_results["sources"]["kad_arbitr"] = kad_data
    result_text += display_results(kad_data, "арбитражные суды")
    
    fssp_data = fssp_search(query)
    all_results["sources"]["fssp"] = fssp_data
    result_text += display_results(fssp_data, "фссп")
    
    nalog_data = nalog_ip_search(query)
    all_results["sources"]["nalog"] = nalog_data
    result_text += display_results(nalog_data, "ип и юрлица")
    
    filename = save_to_json(all_results)
    result_text += f"\nрезультаты сохранены в: {filename}\n"
    
    total_results = sum(len(source["results"]) for source in all_results["sources"].values() 
                      if source["status"] == "success")
    result_text += f"всего найдено: {total_results}\n"
    result_text += f"{'_' * 50}"
    
    result_panel = Panel(
        Text(result_text, style="white"),
        title="[bold bright_magenta]Результат поиска судебных дел[/bold bright_magenta]",
        border_style="green",
        box=box.ROUNDED,
        padding=(1, 2),
        width=80
    )
    console.print(result_panel)
    console.input("\n[yellow]Нажмите Enter для возврата в меню...[/yellow]")

def search_company(query: str):
    payload = {"query": query, "count": 5}
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
        progress.add_task(description="Идет поиск...", total=None)
        try:
            response = requests.post(DADATA_URL, headers=dadata_headers, json=payload, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            console.print(f"Ошибка запроса: {e}")
            return
    data = response.json()
    suggestions = data.get("suggestions", [])
    if not suggestions:
        console.print("Ничего не найдено.")
        return
    table = Table(show_header=True, header_style=None)
    table.add_column("Название")
    table.add_column("ИНН")
    table.add_column("ОГРН")
    table.add_column("Адрес")
    for item in suggestions:
        value = item.get("value", "")
        inn = item["data"].get("inn", "")
        ogrn = item["data"].get("ogrn", "")
        address = item["data"].get("address", {}).get("value", "")
        table.add_row(value, inn, ogrn, address)
    console.print(table)

def send_osint_request(query, limit=100, lang='ru', report_type='json'):
    data = {
        "token": LEAKOSINT_TOKEN,
        "request": query,
        "limit": limit,
        "lang": lang,
        "type": report_type
    }
    try:
        response = requests.post(LEAKOSINT_URL, json=data, timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def format_results(results):
    result_text = ""
    if "error" in results:
        result_text += f"Ошибка запроса: {results['error']}\n"
        return result_text
    if not results.get("List"):
        result_text += "Нет данных по вашему запросу.\n"
        return result_text
    for source, data in results["List"].items():
        result_text += f"\nИсточник: {source}\n"
        result_text += '-' * 60 + "\n"
        for entry in data.get("Data", []):
            if isinstance(entry, dict):
                for key, value in entry.items():
                    result_text += f"{key:20}: {value}\n"
                result_text += '-' * 60 + "\n"
    result_text += f"\nСвободных запросов осталось: {results.get('free_requests_left', 'N/A')}\n"
    return result_text

def loading_animation(duration=3):
    animation = ["|", "/", "-", "\\"]
    for i in range(duration * 10):
        console.print(f"Идет обработка {animation[i % len(animation)]}", end='\r')
        time.sleep(0.1)
    console.print()

def get_folder_size(folder):
    total_size = 0
    for dirpath, _, filenames in os.walk(folder):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.isfile(fp):
                total_size += os.path.getsize(fp)
    return total_size

def human_readable_size(size_bytes):
    for unit in ['Б', 'КБ', 'МБ', 'ГБ', 'ТБ']:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} ТБ"

def search_in_csv(file_path, query):
    results = []
    with open(file_path, encoding="utf-8", errors="ignore") as f:
        reader = csv.reader(f)
        for row_num, row in enumerate(reader, start=1):
            line = ",".join(row)
            if query.lower() in line.lower():
                results.append((row_num, line))
    return results

def search_in_txt(file_path, query):
    results = []
    with open(file_path, encoding="utf-8", errors="ignore") as f:
        for row_num, line in enumerate(f, start=1):
            if query.lower() in line.lower():
                results.append((row_num, line.strip()))
    return results

def search_in_json(file_path, query):
    results = []
    with open(file_path, encoding="utf-8", errors="ignore") as f:
        try:
            data = json.load(f)
        except Exception as e:
            return [("Ошибка", f"Не удалось загрузить JSON: {e}")]
        def recursive_search(obj, path="root"):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    recursive_search(v, f"{path}.{k}")
            elif isinstance(obj, list):
                for i, v in enumerate(obj):
                    recursive_search(v, f"{path}[{i}]")
            else:
                if query.lower() in str(obj).lower():
                    results.append((path, str(obj)))
        recursive_search(data)
    return results

def print_results(file_path, matches):
    result_text = f"\n" + "=" * 60 + f"\nФайл: {file_path}\n" + "=" * 60 + "\n"
    for row_num, line in matches:
        result_text += f"  Найдено ({row_num}): {line}\n"
    result_text += "=" * 60 + "\n"
    return result_text

def search_local_database():
    folder_size = get_folder_size(DATA_FOLDER)
    result_text = f"=" * 60 + f"\nПоиск в папке: {DATA_FOLDER}\nОбщий размер базы: {human_readable_size(folder_size)}\n" + "=" * 60 + "\n"
    query = Prompt.ask("Введите строку для поиска")
    found_any = False
    for root, _, files in os.walk(DATA_FOLDER):
        for file in files:
            file_path = os.path.join(root, file)
            if file.endswith(".csv"):
                matches = search_in_csv(file_path, query)
            elif file.endswith(".txt"):
                matches = search_in_txt(file_path, query)
            elif file.endswith(".json"):
                matches = search_in_json(file_path, query)
            else:
                continue
            if matches:
                found_any = True
                result_text += print_results(file_path, matches)
    if not found_any:
        result_text += "\nСовпадений не найдено.\n"
    result_panel = Panel(
        Text(result_text, style="white"),
        title="[bold bright_magenta]Результат поиска в локальной базе[/bold bright_magenta]",
        border_style="green",
        box=box.ROUNDED,
        padding=(1, 2),
        width=80
    )
    console.print(result_panel)
    console.input("\n[yellow]Нажмите Enter для возврата в меню...[/yellow]")

def collect_data():
    result_text = "Заполните анкету для создания досье\n"
    data = {}
    data['name'] = Prompt.ask("ФИО")
    data['birth_date'] = Prompt.ask("Дата рождения (ДД.ММ.ГГГГ)")
    data['birth_place'] = Prompt.ask("Место рождения")
    data['inn'] = Prompt.ask("ИНН (12 цифр)")
    data['passport'] = Prompt.ask("Паспортные данные (серия, номер, кем выдан, дата выдачи)")
    data['passport_issued_date'] = Prompt.ask("Дата выдачи паспорта (ДД.ММ.ГГГГ)")
    data['registration_address'] = Prompt.ask("Адрес прописки")
    data['actual_address'] = Prompt.ask("Фактический адрес проживания")
    data['occupation'] = Prompt.ask("Род занятий")
    data['education'] = Prompt.ask("Образование (учебное заведение, специальность, год окончания)")
    data['phone'] = Prompt.ask("Телефон")
    data['email'] = Prompt.ask("Email")
    data['marital_status'] = Prompt.ask("Семейное положение")
    data['relatives'] = []
    result_text += "Введите информацию о родственниках (оставьте ФИО пустым для завершения):\n"
    while True:
        relative_name = Prompt.ask("ФИО родственника")
        if not relative_name:
            break
        relative_relation = Prompt.ask("Степень родства")
        relative_birth_date = Prompt.ask("Дата рождения родственника (ДД.ММ.ГГГГ)")
        relative_contact = Prompt.ask("Контактные данные родственника")
        data['relatives'].append({
            'name': relative_name,
            'relation': relative_relation,
            'birth_date': relative_birth_date,
            'contact': relative_contact
        })
    data['work_experience'] = Prompt.ask("Опыт работы (место работы, должность, период)")
    data['additional'] = Prompt.ask("Дополнительная информация (хобби, навыки, награды и т.д.)")
    return data

def generate_html(data):
    relatives_html = ""
    for relative in data['relatives']:
        relatives_html += f"""
                <div class="flex flex-col border-t pt-2 mt-2">
                    <span class="font-semibold text-gray-600">ФИО родственника:</span> <span class="text-gray-800">{relative['name']}</span>
                    <span class="font-semibold text-gray-600">Степень родства:</span> <span class="text-gray-800">{relative['relation']}</span>
                    <span class="font-semibold text-gray-600">Дата рождения:</span> <span class="text-gray-800">{relative['birth_date']}</span>
                    <span class="font-semibold text-gray-600">Контакты:</span> <span class="text-gray-800">{relative['contact']}</span>
                </div>
        """
    html_content = f"""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Досье: {data['name']}</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 font-sans">
    <div class="container mx-auto p-6">
        <div class="bg-white shadow-lg rounded-lg p-8 max-w-3xl mx-auto">
            <h1 class="text-3xl font-bold text-center text-gray-800 mb-6">Досье</h1>
            <div class="space-y-4">
                <div class="flex items-center">
                    <span class="font-semibold text-gray-600 w-1/3">ФИО:</span>
                    <span class="text-gray-800">{data['name']}</span>
                </div>
                <div class="flex items-center">
                    <span class="font-semibold text-gray-600 w-1/3">Дата рождения:</span>
                    <span class="text-gray-800">{data['birth_date']}</span>
                </div>
                <div class="flex items-center">
                    <span class="font-semibold text-gray-600 w-1/3">Место рождения:</span>
                    <span class="text-gray-800">{data['birth_place']}</span>
                </div>
                <div class="flex items-center">
                    <span class="font-semibold text-gray-600 w-1/3">ИНН:</span>
                    <span class="text-gray-800">{data['inn']}</span>
                </div>
                <div class="flex items-center">
                    <span class="font-semibold text-gray-600 w-1/3">Паспортные данные:</span>
                    <span class="text-gray-800">{data['passport']}</span>
                </div>
                <div class="flex items-center">
                    <span class="font-semibold text-gray-600 w-1/3">Дата выдачи паспорта:</span>
                    <span class="text-gray-800">{data['passport_issued_date']}</span>
                </div>
                <div class="flex items-center">
                    <span class="font-semibold text-gray-600 w-1/3">Адрес прописки:</span>
                    <span class="text-gray-800">{data['registration_address']}</span>
                </div>
                <div class="flex items-center">
                    <span class="font-semibold text-gray-600 w-1/3">Фактический адрес:</span>
                    <span class="text-gray-800">{data['actual_address']}</span>
                </div>
                <div class="flex items-center">
                    <span class="font-semibold text-gray-600 w-1/3">Род занятий:</span>
                    <span class="text-gray-800">{data['occupation']}</span>
                </div>
                <div class="flex items-center">
                    <span class="font-semibold text-gray-600 w-1/3">Образование:</span>
                    <span class="text-gray-800">{data['education']}</span>
                </div>
                <div class="flex items-center">
                    <span class="font-semibold text-gray-600 w-1/3">Телефон:</span>
                    <span class="text-gray-800">{data['phone']}</span>
                </div>
                <div class="flex items-center">
                    <span class="font-semibold text-gray-600 w-1/3">Email:</span>
                    <span class="text-gray-800">{data['email']}</span>
                </div>
                <div class="flex items-center">
                    <span class="font-semibold text-gray-600 w-1/3">Семейное положение:</span>
                    <span class="text-gray-800">{data['marital_status']}</span>
                </div>
                <div class="flex flex-col">
                    <span class="font-semibold text-gray-600 w-1/3">Родственники:</span>
                    {relatives_html if relatives_html else '<span class="text-gray-800">Нет данных</span>'}
                </div>
                <div class="flex items-start">
                    <span class="font-semibold text-gray-600 w-1/3">Опыт работы:</span>
                    <span class="text-gray-800">{data['work_experience']}</span>
                </div>
                <div class="flex items-start">
                    <span class="font-semibold text-gray-600 w-1/3">Дополнительно:</span>
                    <span class="text-gray-800">{data['additional']}</span>
                </div>
            </div>
            <div class="mt-8 text-center text-gray-500 text-sm">
                Создано: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}
            </div>
        </div>
    </div>
</body>
</html>
"""
    return html_content

def save_html(html_content, filename="dossier.html"):
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html_content)
    console.print(f"Досье сохранено в файл: {filename}")

def create_dossier():
    data = collect_data()
    html_content = generate_html(data)
    save_html(html_content)

def list_osint_bots():
    result_text = "Боты для OSINT и не только\n"
    result_text += "@osintereptarobot - Старый добрый шерлок, хорошая база данных, ну и для поверхностной инфы тоже сойдет\n"
    result_text += "@UniversalSearchCoolBot - бот ищет только по открытым источникам, также чекает ботов\n"
    result_text += "@phonebook_space_bot - неплохой бот, ищет вроде только по номеру, но бд мелкая\n"
    result_text += "@dyx_robot - Духлесс, очень большая бд, но бот платный\n"
    result_text += "@VKHistoryRobot - ахуенный бот для поиска по вк, выдает старые страницы вк\n"
    result_text += "@cultureosintbot - Вектор инфо бот, хороший бот для пробива\n"
    result_text += "@Telelogoff_robot  - Телелог, очень полезнный бот, ищет гурппы, сообщения и старые юзеры человека\n"
    result_text += "@TrueCaller1Bot - хороший бот по типу гетконтакта\n"
    result_panel = Panel(
        Text(result_text, style="white"),
        title="[bold bright_magenta]Список ботов для OSINT[/bold bright_magenta]",
        border_style="green",
        box=box.ROUNDED,
        padding=(1, 2),
        width=80
    )
    console.print(result_panel)
    console.input("\n[yellow]Нажмите Enter для возврата в меню...[/yellow]")

def list_osint_websites():
    result_text = "Список сайтов для OSINT\n"
    result_text += "https://smsc.ru/testhlr/ - Проверяет номер на валидность\n"
    result_text += "https://220vk.com/ - сайт старый но довольно хороший находит скрытых друзей и тд\n"
    result_text += "https://www.whois.net - ищет по домену, связанные страницы с заданным профилем, используется в программах основанных на python.\n"
    result_text += "www.pipl.com - бесплатный сайт. ищет легко и просто\n"
    result_text += "fa-fa.kz - найдёт ФИО и проверка долгов.\n"
    result_text += "https://cybersec.org/search - довольно хороший сайт со слитыми базами данных  Вес бд около 2тб\n"
    result_panel = Panel(
        Text(result_text, style="white"),
        title="[bold bright_magenta]Список сайтов для OSINT[/bold bright_magenta]",
        border_style="green",
        box=box.ROUNDED,
        padding=(1, 2),
        width=80
    )
    console.print(result_panel)
    console.input("\n[yellow]Нажмите Enter для возврата в меню...[/yellow]")

def universal_search_func():
    banner = r"""
   __  __      _                            __
  / / / /___  (_)   _____  ______________ _/ /
 / / / / __ \/ / | / / _ \/ ___/ ___/ __ `/ / 
/ /_/ / / / / /| |/ /  __/ /  (__  ) /_/ / /  
\____/_/ /_/_/ |___/\___/_/  /____/\__,_/_/   
"""
    console.print(banner)
    console.print("Выберите действие:")
    console.print("1. Поиск по LeakOsint")
    console.print("2. Поиск по Названию Компании")
    console.print("3. Поиск по локальной базе данных")
    console.print("4. Составить досье в HTML формате")
    console.print("5. Список ботов для OSINT и не только")
    console.print("6. Список сайтов для OSINT")
    console.print("0. Назад")
    choice = Prompt.ask("Введите номер действия", choices=["0", "1", "2", "3", "4", "5", "6"], show_choices=False)
    if choice == "1":
        query = Prompt.ask("Введите запрос для анализа").strip()
        if query:
            loading_animation()
            results = send_osint_request(query)
            result_text = format_results(results)
            result_panel = Panel(
                Text(result_text, style="white"),
                title="[bold bright_magenta]Результаты LeakOsint[/bold bright_magenta]",
                border_style="green",
                box=box.ROUNDED,
                padding=(1, 2),
                width=80
            )
            console.print(result_panel)
        else:
            console.print("[red]Запрос не может быть пустым.[/red]")
        console.input("\n[yellow]Нажмите Enter для возврата в меню...[/yellow]")
    elif choice == "2":
        query = Prompt.ask("Введите название компании").strip()
        if query:
            search_company(query)
        else:
            console.print("[red]Запрос не может быть пустым.[/red]")
        console.input("\n[yellow]Нажмите Enter для возврата в меню...[/yellow]")
    elif choice == "3":
        search_local_database()
    elif choice == "4":
        create_dossier()
        console.input("\n[yellow]Нажмите Enter для возврата в меню...[/yellow]")
    elif choice == "5":
        list_osint_bots()
    elif choice == "6":
        list_osint_websites()
    elif choice == "0":
        return
    else:
        console.print("[red]Неверный выбор, попробуйте снова.[/red]")
        console.input("\n[yellow]Нажмите Enter для возврата в меню...[/yellow]")

def show_banner():
    # Генерируем ASCII-арт для "Black Search V3" с шрифтом 'slant'
    banner_text = text2art("Black Search V3", font="slant", chr_ignore=True)
    console.print(Align.center(Text(banner_text, style="bold bright_magenta")))
    console.print(Align.center(Text("Инструмент для поиска по открытым источникам", style="italic cyan")))

def show_menu():
    table = Table(
        box=box.MINIMAL_DOUBLE_HEAD,
        border_style="bright_cyan",
        show_header=True,
        header_style="bold white on bright_blue",
        padding=(0, 2),
        expand=False,
        width=90
    )
    table.add_column("№", style="cyan", width=5, justify="center")
    table.add_column("Функция", style="white", justify="left")
    table.add_column("Категория", style="yellow", justify="left")
    table.add_column("Статус", style="green", justify="center")
    menu_items = [
        ("1", "Анализ номера телефона", "Коммуникации", "Активно"),
        ("2", "Анализ email-адреса", "Коммуникации", "Активно"),
        ("3", "Поиск по номеру телефона", "Поиск", "Активно"),
        ("4", "Поиск по IP-адресу", "Сеть", "Активно"),
        ("5", "Поиск по имени пользователя", "Идентификация", "Активно"),
        ("6", "Поиск по координатам", "Геолокация", "Активно"),
        ("7", "Поиск судебных записей", "Юридические", "Активно"),
        ("8", "Поиск профиля ВКонтакте", "Социальные сети", "Активно"),
        ("9", "Универсальный поиск", "Многофункциональный", "Активно"),
        ("0", "Выход из программы", "Система", "Активно")
    ]
    for number, description, category, status in menu_items:
        table.add_row(number, description, category, status)
    panel = Panel(
        Align.center(table),
        title="[bold bright_magenta]BlackSearch[/bold bright_magenta]",
        subtitle="[italic white][/italic white]",
        border_style="bright_cyan",
        box=box.DOUBLE_EDGE,
        padding=(1, 4),
        width=100
    )
    console.print(Align.center(panel))

def show_welcome():
    welcome_text = Text.assemble(
        ("BlackSearch  v3.0\n", "bold green"),
        ("Разработчик: @attackland1x\n", "italic white"),
        ("Version:pro ", "cyan")
    )
    welcome_panel = Panel(
        Align.center(welcome_text),
        box=box.SIMPLE_HEAVY,
        border_style="green",
        padding=(1, 4),
        width=60
    )
    console.print(Align.center(welcome_panel))
    console.print()

def simulate_loading():
    with Progress(transient=True) as progress:
        task = progress.add_task("[cyan]Инициализация системы...", total=100)
        for _ in range(100):
            progress.update(task, advance=1)
            time.sleep(0.02)

def main():
    simulate_loading()
    while True:
        console.clear()
        show_banner()
        show_welcome()
        show_menu()
        try:
            console.print()
            choice = IntPrompt.ask(
                "[bold yellow]Выберите функцию (0-9)[/bold yellow]", 
                choices=[str(i) for i in range(10)],
                show_choices=False
            )
            if choice == 0:
                with Progress(transient=True) as progress:
                    task = progress.add_task("[red]Завершение работы...", total=100)
                    for _ in range(100):
                        progress.update(task, advance=1)
                        time.sleep(0.01)
                console.print("[bold red]Программа завершена.[/bold red]")
                break
            elif choice == 1:
                analyze_phone()
            elif choice == 2:
                analyze_email_func()
            elif choice == 3:
                search_nick_func()
            elif choice == 4:
                search_ip_func()
            elif choice == 5:
                search_nick_func()
            elif choice == 6:
                search_geo_func()
            elif choice == 7:
                search_sud_func()
            elif choice == 8:
                vk_search_func()
            elif choice == 9:
                universal_search_func()
            else:
                action_panel = Panel(
                    f"[bold cyan]Выбрана функция #[/bold cyan][bold yellow]{choice}[/bold yellow]\n"
                    f"[white]Обработка запроса...[/white]",
                    box=box.ROUNDED,
                    border_style="yellow",
                    padding=(1, 4),
                    width=60
                )
                console.print()
                console.print(Align.center(action_panel))
                console.input("[yellow]Нажмите Enter для продолжения...[/yellow]")
        except KeyboardInterrupt:
            console.print("[red bold]Программа прервана пользователем.[/red bold]")
            break
        except Exception as e:
            error_panel = Panel(
                f"[red]Ошибка: {str(e)}[/red]",
                box=box.ROUNDED,
                border_style="red",
                padding=(1, 4),
                width=60
            )
            console.print(Align.center(error_panel))
            console.input("[yellow]Нажмите Enter для продолжения...[/yellow]")

if __name__ == "__main__":
    main()