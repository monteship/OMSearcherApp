import os
import pickle
from abc import ABC, abstractmethod

from database import CityResults, DomainItem


class AbstractMiddleware(ABC):
    @abstractmethod
    def load_collected(self):
        pass

    @abstractmethod
    async def filter(self, city_results: CityResults) -> CityResults:
        pass

    @abstractmethod
    def update_collected(self) -> None:
        pass


class DuplicateFilterMiddleware(AbstractMiddleware):
    def __init__(self, country):
        self.path = os.path.join(os.getcwd(), country, "data.pkl")
        self.collected = self.load_collected()

    def load_collected(self) -> set:
        if not os.path.exists(self.path):
            with open(self.path, "wb") as f:
                pickle.dump(set(), file=f)

        return pickle.load(open(self.path, "rb"))

    async def filter(self, city_results: CityResults) -> CityResults:
        for _, city_result in city_results:
            domain_item: DomainItem = city_result["domain"]
            if (domain := domain_item.domain) in self.collected:
                city_results.remove(city_result)
            self.collected.add(domain)
        return city_results

    def update_collected(self) -> None:
        old_data = self.load_collected()

        # Union of old and new data
        written_data = old_data.union(self.collected)

        # Write to file
        with open(self.path, "wb") as f:
            pickle.dump(written_data, file=f)
