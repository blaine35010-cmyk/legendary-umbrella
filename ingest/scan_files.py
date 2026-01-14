import os
import json

def load_settings():
    here = os.path.dirname(os.path.dirname(__file__))
    cfg_path = os.path.join(here, "config", "settings.json")
    with open(cfg_path, "r", encoding="utf-8") as f:
        return json.load(f)

def scan_case_files():
    settings = load_settings()
    root = settings["case_root"]
    ignore = set(settings.get("ignore_folders", []))

    file_list = []

    for dirpath, dirnames, filenames in os.walk(root):
        # Skip ignored folders
        if any(ig.lower() in dirpath.lower() for ig in ignore):
            continue

        for file in filenames:
            full_path = os.path.join(dirpath, file)
            ext = os.path.splitext(file)[1].lower()

            if ext in settings.get("file_types", []):
                file_list.append(full_path)

    return file_list

if __name__ == "__main__":
    files = scan_case_files()
    print("\nFound files:")
    for f in files:
        print(f)
