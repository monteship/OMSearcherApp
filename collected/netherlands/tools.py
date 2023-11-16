import csv
import pickle
from collections import deque

if __name__ == '__main__':
    cities = deque(pickle.load(open('sorted_cities.pkl', 'rb')))
    with open('sorted_cities.csv', 'w') as file:
        writer = csv.writer(file)
        for city in cities:
            print(city)
            writer.writerow([city])
