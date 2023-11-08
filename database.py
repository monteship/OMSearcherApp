import os
from abc import ABC, abstractmethod
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
