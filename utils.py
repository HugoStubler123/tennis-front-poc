def str_to_int_keys(obj):
    if isinstance(obj, dict):
        new_dict = {}
        for k, v in obj.items():
            try:
                new_k = int(k)
            except ValueError:
                new_k = k
            new_dict[new_k] = str_to_int_keys(v)
        return new_dict
    elif isinstance(obj, list):
        return [str_to_int_keys(v) for v in obj]
    else:
        return obj

def merge_shots_and_hits(dico_shots, dico_hits):
    merged_data = []

    for shot in dico_shots:
        frame = shot["frame"]
        hit_data = dico_hits.get(str(frame))  # hit keys are strings

        if hit_data:  # only merge if there's a match in dico_hits
            merged_entry = {
                "frame": frame,
                "player name": shot["player_name"],
                "player": shot["player"],
                "x": hit_data["x"],
                "y": hit_data["y"],
                "type": shot["type"],
                "speed": hit_data["speed"],
                "depth": hit_data["depth"],
                "laterality": hit_data["laterality"]
            }
            merged_data.append(merged_entry)

    return merged_data
