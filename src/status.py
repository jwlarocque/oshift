import json

STATUS_FILEPATH = "/status.json"

status = {
    "target_detent": 0,
    "position": 0
}

with open(STATUS_FILEPATH) as fp:
    status = json.load(fp)

def save():
    try:
        with open(STATUS_FILEPATH, "w") as fp:
            json.dump(status, fp)
    except Exception as e:
        print(f"Unable to save status to file, probably because the filesystem is in use by a connected comptuer.\n", e)
