import curses
import asyncio
from simple_ui import display_ui
from api_client import Provider, create_httpx_client
from scraper import run_scraping_pipeline
from gtfs_generator import generate_gtfs
from data_structures import Customer

def main():
    print("Scrap GTFS file")
    selected_agency = curses.wrapper(display_ui)
    if selected_agency:
        provider = Customer(
            name=selected_agency['name'],
            prefix=selected_agency['prefix'],
            domain=selected_agency['domain']
        )
        async def run():
            client = await create_httpx_client(provider)
            scraped_data = await run_scraping_pipeline(provider, client)
            await client.aclose()
            if scraped_data:
                generate_gtfs(scraped_data)
                print("File generated successfully.")
            else:
                print("Scraping failed.")

        asyncio.run(run())

if __name__ == "__main__":
    main()