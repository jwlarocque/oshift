import json

config = {}

with open("/config.json") as fp:
    config = json.load(fp)

def save():
    try:
        with open("/config.json", "w") as fp:
            json.dump(config, fp)
            fp.flush()
    except Exception as e:
        print(f"Unable to save config to file, probably because the filesystem is in use by a connected comptuer.\n", e)
