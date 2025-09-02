import os
import aiohttp
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()
URL = os.getenv("LUNCH_URL")

async def fetch_lunch_menu():
    async with aiohttp.ClientSession() as session:
        async with session.get(URL) as response:
            if response.status != 200:
                raise Exception(f"Failed to fetch menu: HTTP {response.status}")
            html = await response.text()
            return parse_menu(html)

def parse_menu(html: str):
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(separator="\n")
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    menu = {"Eat The Street": [], "Flow": [], "Fresh 4 You": []}
    current = None
    for line in lines:
        if "Eat The Street" in line:
            current = "Eat The Street"
        elif "Flow" in line:
            current = "Flow"
        elif "Fresh 4 You" in line:
            current = "Fresh 4 You"
        elif line.startswith("*") and current:
            menu[current].append(line.lstrip("* ").strip())

    return menu
