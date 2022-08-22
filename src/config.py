import json

DEFAULT_POS = 300
INCREMENT_DIST = 20

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


def clamp_detent(pos, prev=None, next=None):
    """Clamp a position to the limits given by this config."""
    minimum = prev or 0
    maximum = next or config["axes"][0]["length_encoder_steps"]
    return min(max(minimum, pos), maximum)


def append_detent():
    num_detents = len(config["axes"][0]["detents"])
    if num_detents == 0:
        pos = DEFAULT_POS
    elif num_detents == 1:
        pos = clamp_detent(config["axes"][0]["detents"][-1]["position"] + DEFAULT_POS)
    else:
        pos = clamp_detent(
            2 * config["axes"][0]["detents"][-1]["position"]
            - config["axes"][0]["detents"][-2]["position"])
    config["axes"][0]["detents"].append({
        "position": pos,
        "overshoot_method": 1,
        "overshoot_proportion": 0.1,
        "overshoot_distance": 10
    })
    save()


def pop_detent():
    if len(config["axes"][0]["detents"]) <= 2:
        return
    else:
        config["axes"][0]["detents"].pop()
        save()


def increment_detent(detent):
    config["axes"][0]["detents"][detent]["position"] = clamp_detent(
        config["axes"][0]["detents"][detent]["position"] + INCREMENT_DIST)
    save()


def decrement_detent(detent):
    config["axes"][0]["detents"][detent]["position"] = clamp_detent(
        config["axes"][0]["detents"][detent]["position"] - INCREMENT_DIST)
    save()


def increment_offset():
    if (
        config["axes"][0]["detents"][-1]["position"] + INCREMENT_DIST
        < config["axes"][0]["length_encoder_steps"]):
        for detent in config["axes"][0]["detents"]:
            detent["position"] += INCREMENT_DIST
        for detent in config["axes"][0]["detents"]:
            print(detent["position"])
        save()


def decrement_offset():
    if (
        config["axes"][0]["detents"][0]["position"] - INCREMENT_DIST
        > 0):
        for detent in config["axes"][0]["detents"]:
            detent["position"] -= INCREMENT_DIST
        for detent in config["axes"][0]["detents"]:
            print(detent["position"])
        save()
