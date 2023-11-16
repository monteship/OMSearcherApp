import json
import os
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List

import psycopg2
from pydantic import BaseModel


class DomainItem(BaseModel):
    domain: str
    link: str
    title: str
    snippet: str
    searcher: str


class CityResults(BaseModel):
    city_name: str
    results: List[DomainItem]


class SearchEngineResult(BaseModel):
    cities: List[CityResults]


class AbstractDatabase(ABC):
    @abstractmethod
    def write(self, results: SearchEngineResult):
        pass

    @abstractmethod
    def read(self) -> set:
        pass


class PostgresqlDatabase(AbstractDatabase):
    def __init__(self):
        self.host = os.environ.get("DB_HOST", "localhost")
        self.port = os.environ.get("DB_PORT", 5432)
        self.database = os.environ.get("POSTGRES_DATABASE")
        self.user = os.environ.get("DB_USER")
        self.password = os.environ.get("DB_PASSWORD")
        self.schema = os.environ.get("DB_NAME", "OMScrapers")
        self.seen_domains = set()

    def _connect(self):
        """
        Connect to the database.
        :return:
        """
        return psycopg2.connect(
            host=self.host,
            port=self.port,
            database=self.database,
            user=self.user,
            password=self.password,
        )

    def write(self, results: SearchEngineResult):
        """
        Write the results to the database.
        :param results:
        :return:
        """
        conn = self._connect()
        cursor = conn.cursor()

        try:
            for city_results in results.cities:
                for domain_item in city_results.results:
                    domain = domain_item.domain

                    # Check if domain is already in the local seen_domains set.
                    if domain in self.seen_domains:
                        continue
                    self.seen_domains.add(domain)

                    # Check if domain is already in the database.
                    cursor.execute(
                        "SELECT COUNT(*) FROM research_team WHERE domain = %s",
                        (domain,),
                    )
                    if cursor.fetchone()[0] != 0:
                        continue

                    # Insert domain into the database.
                    cursor.execute(
                        """
                        INSERT INTO research_team (city, domain, link, title, snippet, searcher) 
                        VALUES (%s, %s, %s, %s, %s, %s)
                        """,
                        (
                            city_results.city_name,
                            domain,
                            domain_item.link,
                            domain_item.title,
                            domain_item.snippet,
                            domain_item.searcher,
                        ),
                    )
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Failed to write to the database: {str(e)}")
        finally:
            cursor.close()
            conn.close()

    def read(self):
        pass


def normalize_text(text: str) -> str:
    return text.replace(" ", "_").lower()


class JsonWriter(AbstractDatabase):
    def __init__(self, country: str):
        self.file_path = f"results/{normalize_text(country)}/"

    def write(self, engine_results: SearchEngineResult):
        if not os.path.exists(self.file_path):
            os.makedirs(self.file_path)
        timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M")
        for city in engine_results.cities:
            with open(f"{self.file_path}{normalize_text(city.city_name)}-{timestamp}.json", "w") as f:
                results = {index: result.model_dump(mode="python") for index, result in enumerate(city.results, 1)}
                f.write(json.dumps(results))

    def read(self):
        pass


if __name__ == "__main__":
    from faker import Faker

    fake = Faker()

    def fake_domain_item():
        return DomainItem(
            domain=fake.url(),
            link=fake.url(),
            title=fake.company(),
            snippet=fake.sentence(),
            searcher=fake.word(),
        )

    def fake_city_item():
        return CityResults(
            city_name=fake.city(),
            results=[fake_domain_item() for _ in range(1000)],
        )

    engine_result = SearchEngineResult(
        cities=[
            fake_city_item(),
            fake_city_item(),
            fake_city_item(),
            fake_city_item(),
            fake_city_item(),
            fake_city_item(),
        ]
    )
    countries = [fake.country() for _ in range(40)]
    for country in countries:
        writer = JsonWriter(country)
        writer.write(engine_result)
