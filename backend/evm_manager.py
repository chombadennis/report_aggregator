import json
import os

class EVMManager:
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = cache_dir
        self.evm_file = os.path.join(self.cache_dir, "contracts_evm.json")
        os.makedirs(self.cache_dir, exist_ok=True)
        if not os.path.exists(self.evm_file):
            with open(self.evm_file, "w") as f:
                json.dump({}, f)

    def get_all_evm_data(self) -> dict:
        try:
            with open(self.evm_file, "r") as f:
                return json.load(f)
        except Exception:
            return {}

    def save_weekly_evm(self, week_name: str, data: dict):
        current_data = self.get_all_evm_data()
        if week_name in current_data:
            raise ValueError(f"Data for {week_name} already exists. Cannot overwrite.")
        current_data[week_name] = data
        with open(self.evm_file, "w") as f:
            json.dump(current_data, f, indent=2)
        return current_data
    def update_weekly_evm(self, week_name: str, data: dict):
        current_data = self.get_all_evm_data()
        if week_name not in current_data:
            raise ValueError(f"Data for {week_name} does not exist. Cannot update.")
        current_data[week_name] = data
        with open(self.evm_file, "w") as f:
            json.dump(current_data, f, indent=2)
        return current_data
