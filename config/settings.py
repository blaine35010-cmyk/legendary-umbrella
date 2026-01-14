import os
import json


def load_settings():
    here = os.path.dirname(__file__)
    cfg_path = os.path.join(here, "settings.json")
    with open(cfg_path, "r", encoding="utf-8") as f:
        return json.load(f)


if __name__ == "__main__":
    print(load_settings())
