"""App catalog: which apps a given TV shows on its home screen."""


def get_apps_for_device(store, device, include_hidden=False):
    apps = store.fixture("apps")
    models = store.fixture("models")
    mdl = None
    for m in models:
        if m["model"] == device["model"]:
            mdl = m
    if mdl == None:
        return []
    fw = device.get("firmware", "0.0")
    try:
        p = fw.split(".")
        fwn = int(p[0]) * 100 + int(p[1])
    except (ValueError, IndexError):
        fwn = 0
    res = []
    feat = []
    for a in apps:
        ok = True
        if a.get("hidden") and not include_hidden:
            ok = False
        if ok:
            r = a.get("regions", [])
            if "*" in r:
                pass
            elif device.get("region") in r:
                pass
            else:
                ok = False
        if ok:
            mf = a.get("min_firmware", "0.0")
            try:
                q = mf.split(".")
                mfn = int(q[0]) * 100 + int(q[1])
            except (ValueError, IndexError):
                mfn = 0
            if fwn < mfn:
                ok = False
        if not ok:
            continue
        pkg = None
        if mdl.get("year") == 2019:
            pkg = a["packages"][0]
        else:
            for x in a["packages"]:
                if x["api"] <= mdl.get("max_api", 0):
                    if pkg == None or x["api"] > pkg["api"]:
                        pkg = x
        if pkg == None:
            continue
        item = {
            "id": a["id"],
            "name": a["name"],
            "color": a.get("color", "#444444"),
            "version": pkg["version"],
            "api": pkg["api"],
        }
        if a.get("featured"):
            feat.append(item)
        else:
            res.append(item)
    feat.sort(key=lambda i: i["name"].lower())
    res.sort(key=lambda i: i["name"].lower())
    out = []
    for i in feat:
        i["featured"] = True
        out.append(i)
    for i in res:
        i["featured"] = False
        out.append(i)
    return out
