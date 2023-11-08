import json
import os
from abc import ABC, abstractmethod
from urllib.parse import urlparse

import aiohttp

from database import (
    CityResults,
    SearchEngineResult,
    DomainItem,
)
from middleware import AbstractMiddleware


class AbstractSearchEngine(ABC):
    @abstractmethod
    async def fetch_url_results(
        self,
        session,
        url_to_search: str,
        city_results: CityResults,
    ) -> int:
        pass

    @abstractmethod
    async def search(self, cities: dict) -> SearchEngineResult:
        pass


class SerpAPISearchEngine(AbstractSearchEngine):
    def __init__(self, searcher: str, middlewares: list[AbstractMiddleware]| AbstractMiddleware):
        self.searcher = searcher
        self.middlewares = middlewares

    async def fetch_url_results(
        self,
        session: aiohttp.ClientSession,
        url_to_search: str,
        city_results: CityResults,
    ) -> int:
        async with session.get(url_to_search) as response:
            page_data = await response.json()
            results = page_data.get("organic_results", [])

            for result in results:
                title = result.get("title", "")
                link = result.get("link", "")
                snippet = result.get("snippet", "")
                domain = urlparse(link).netloc.replace("www.", "")

                if domain in city_results:
                    continue

                if any(await middleware.filter(domain) for middleware in self.middlewares):
                    continue

                city_results.append(
                    DomainItem(
                        domain=domain,
                        title=title,
                        link=link,
                        snippet=snippet,
                        searcher=self.searcher,
                    )
                )

            return len(results)

    async def search(self, cities: dict) -> SearchEngineResult:
        search_results = SearchEngineResult()

        async with aiohttp.ClientSession() as session:
            for city_name, urls in cities.items():
                city_results = CityResults(name=city_name, results=[])
                for url in urls:
                    url_to_search = url
                    while True:
                        results_count = await self.fetch_url_results(
                            session, url_to_search, city_results
                        )
                        if results_count < 100:
                            break
                        url_to_search = (
                            url
                            + "&start="
                            + str(len(search_results.get(url_to_search, [])))
                        )

                search_results.cities.append(city_results)

        return search_results


class QueryBuilder:
    def __init__(self, country):
        self.country = country
        self.api_key = os.environ.get("SERPAPI_API_KEY")
        self.temp = (
            "https://serpapi.com/search?q={query}&location={country}&hl={lang}&gl={suf}&api_key={"
            "api_key}&num=100"
        )
        self.country_settings = self._load_country_settings()

    def _load_country_settings(self) -> dict:
        try:
            return json.load(open("package.json"))[self.country]
        except (FileNotFoundError, KeyError):
            raise ValueError(f"Country '{self.country}' not found in package.json")

    def build_queries(self, cities: str | list[str,]) -> dict:
        queries = {}
        for city_name in cities:
            queries[city_name] = []
            for query in self.country_settings.get("queries", []):
                formatted_query = query.format(city_name.replace(" ", "+"))
                query_url = self.temp.format(
                    query=formatted_query,
                    country=self.country_settings["name"],
                    lang=self.country_settings["lang"],
                    suf=self.country_settings["suf"],
                    api_key=self.api_key,
                )
                queries[city_name].append(query_url)
        return queries



