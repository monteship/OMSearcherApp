import asyncio

from database import PostgresqlDatabase
from middleware import DuplicateFilterMiddleware
from search import QueryBuilder, SerpAPISearchEngine


async def run(country: str, cities: str | list[str], searcher: str):
    # Create objects
    query_builder = QueryBuilder(country)
    middleware = DuplicateFilterMiddleware(country)
    search_engine = SerpAPISearchEngine(searcher, middleware)
    database = PostgresqlDatabase()

    # Build queries for each city
    cities_queries = query_builder.build_queries(cities)

    # Fetch search results from each city
    search_results = await search_engine.search(cities_queries)

    # Update collected database
    middleware.update_collected()

    # Write search results to database
    database.write(search_results)


# Example usage
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run(country="Ireland", cities=["Dublin", "Galway", "Cork"]))
    loop.close()
