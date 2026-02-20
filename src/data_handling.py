from json import load, dumps
import os

# Saves data as a JSON file, may want to change this to be a CSV file later for faster performance but this works for now
class DataHandler:
    def __init__(self, data_file: str):
        self.data_file = data_file
        if not os.path.exists(data_file):
            with open(data_file, 'w') as f:
                f.write('[]')

    # Loads all saved weeks and their data
    def __load_data(self) -> list[dict[str, str]]:
        with open(self.data_file, 'r') as f:
            return load(f)
    
    # Saves data to the JSON file
    def __save_data(self, data: list[dict[str, str]]) -> None:
        with open(self.data_file, 'w') as f:
            f.write(dumps(data, indent=4))

    # Saves a week's data, will overwrite if the week already exists
    def save_week(self, week: str, data: dict[str, str]) -> None:
        items = self.__load_data()
        for item in items:
            if item["week"] == week:
                for key in data.keys():
                    item[key] = data[key]
                self.__save_data(items)
                return
        data["week"] = week
        items.append(data)
        self.__save_data(items)
    
    # Loads a week's data, returns None if the week doesn't exist
    def load_week(self, week: str) -> dict[str, str] | None:
        items = self.__load_data()
        for item in items:
            if item["week"] == week:
                return item
        return None
