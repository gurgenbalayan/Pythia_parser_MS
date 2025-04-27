import json
from idlelib import query
import aiohttp
from bs4 import BeautifulSoup
from utils.logger import setup_logger
import os
from dotenv import load_dotenv
from typing import List, Dict
load_dotenv()

STATE = os.getenv("STATE")
logger = setup_logger("scraper")



async def fetch_company_details(url: str) -> dict:
    try:

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                html = await response.text()
                return await parse_html_details(html)
    except Exception as e:
        logger.error(f"Error fetching data for query '{url}': {e}")
        return []
async def fetch_company_data(query: str) -> list[dict]:
    url = "https://corp.sos.ms.gov/corp/Services/MS/CorpServices.asmx/BusinessNameSearch"

    payload = {
        "SearchType": "startingwith",
        "BusinessName": query
    }
    headers = {
        'Content-Type': 'application/json; charset=utf-8'
    }
    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.post(url, json=payload) as response:
                response.raise_for_status()
                data = json.loads(await response.text())
                return await parse_html_search(data)
    except Exception as e:
        logger.error(f"Error fetching data for query '{query}': {e}")
        return []

async def parse_html_search(data: dict) -> list[dict]:
    try:
        results = []
        d = data.get("d")
        if not d or d == '""':
            return []
        parsed_data = json.loads(data["d"])
        businesses = parsed_data.get("Table", [])

        for biz in businesses:
            name = biz.get("BusinessName")
            status = biz.get("FilingStatus")
            biz_id = biz.get("BusinessId")
            filing_id = biz.get("FilingId")

            url = f"https://corp.sos.ms.gov/corp/portal/c/page/corpbusinessidsearch/~/ViewXSLTFileByName.aspx?providerName=MSBSD_CorporationBusinessDetails&FilingId={filing_id}"
            results.append({
                "state": STATE,
                "name": name,
                "status": status,
                "id": biz_id,
                "url": url,
            })

        return results
    except Exception as e:
        logger.error(f"Error fetching data for query '{query}': {e}")
        return []


async def parse_html_details(html: str) -> dict:
    soup = BeautifulSoup(html, 'html.parser')

    async def fetch_documents(id: str) -> list[dict]:
        url = "https://corp.sos.ms.gov/corp/Services/MS/CorpServices.asmx/GetFiledFilingsV2"

        payload = {"FileNumber": id}
        headers = {
            'Content-Type': 'application/json; charset=utf-8'
        }
        try:
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.post(url, json=payload) as response:
                    response.raise_for_status()
                    data = json.loads(await response.text())
                    decoded_data = json.loads(data["d"])
                    entries = decoded_data.get("Table", [])
                    return [
                        {
                            "link": "https://corp.sos.ms.gov/corpconv/portal/c/ExecuteWorkflow.aspx?workflowid=g12dbd558-fa5d-49a1-a869-ad8b9db198db&FilingId="+entry["FilingId"],
                            "description": entry["Description"],
                            "name": entry["FilingTypeName"],
                            "date": entry["FiledDate"]
                        }
                        for entry in entries if entry.get("Referenece") == "True"
                    ]
        except Exception as e:
            logger.error(f"Error fetching data for query '{query}': {e}")
            return []

    async def get_value_or_none(label):
        element = soup.find('td', string=label)
        if element:
            return element.find_next('td').text.strip() if element.find_next('td') else None
        return None

    name = ""
    name_row = soup.find('td', string='Name')
    if name_row:
        name = name_row.find_next('tr').find_all('td')[0].text.strip()
    status = await get_value_or_none("Status:")
    registration_number = await get_value_or_none("Business ID:")
    date_registered = await get_value_or_none("Effective Date:")
    entity_type = await get_value_or_none("Business Type:")
    principal_address = await get_value_or_none("Principal Office Address:")

    agent_name = ""
    agent_address = ""
    registered_agent_div = None
    for div in soup.find_all('div'):
        if 'Registered Agent' in div.get_text(strip=True):
            registered_agent_div = div
    if registered_agent_div:
        table_agent = registered_agent_div.find_next('table', class_='subTable')
        info_td = table_agent.find_all('tr')[1].find('td')
        agent_name = info_td.find('a').text.strip()
        parts = info_td.decode_contents().split('<br/>')
        for part in parts[1:]:
            agent_address += part+" "
        agent_address = agent_address.strip()
    officers = []
    officers_div = None
    for div in soup.find_all('div'):
        if 'Officers & Directors' in div.get_text(strip=True):
            officers_div = div
    if officers_div:
        table_officers = officers_div.find_next('table', class_='subTable')
        rows = table_officers.find_all('tr')[1:]
        officers_address = ""
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 3:
                name_td = cols[0]
                title_td = cols[2]
                name_tag = name_td.find('a')
                name = name_tag.text.strip() if name_tag else None
                address_lines = name_td.decode_contents().split('<br/>')
                for part in address_lines[1:]:
                    officers_address += part + " "
                officers_address = officers_address.strip()
                title = title_td.get_text(strip=True)
                officers.append({
                    "name": name,
                    "address": officers_address,
                    "title": title
                })


    return {
        "state": STATE,
        "name": name,
        "status": status,
        "registration_number": registration_number,
        "date_registered": date_registered,
        "entity_type": entity_type,
        "principal_address": principal_address,
        "agent_name": agent_name,
        "agent_address": agent_address,
        "officers": officers if officers else None,
        "documents": await fetch_documents(registration_number)
    }




