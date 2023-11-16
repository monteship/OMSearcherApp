import os
import pickle
from abc import ABC, abstractmethod


class AbstractMiddleware(ABC):
    @abstractmethod
    def load_collected(self):
        pass

    @abstractmethod
    async def filter(self, domain: str) -> bool:
        pass

    @abstractmethod
    def update_collected(self) -> None:
        pass


class DuplicateFilterMiddleware(AbstractMiddleware):
    def __init__(self, country):
        self.path = os.path.join(os.getcwd(), country.lower().replace(" ", "_"), "collected.pkl")
        self.collected = self.load_collected()

    def load_collected(self) -> set:
        if not os.path.exists(self.path):
            with open(self.path, "wb") as f:
                pickle.dump(set(), file=f)

        return pickle.load(open(self.path, "rb"))

    async def filter(self, domain: str) -> bool:
        if domain in self.collected:
            return False
        self.collected.add(domain)
        return True

    def update_collected(self) -> None:
        old_data = self.load_collected()

        # Union of old and new data
        written_data = old_data.union(self.collected)

        # Write to file
        with open(self.path, "wb") as f:
            pickle.dump(written_data, file=f)
