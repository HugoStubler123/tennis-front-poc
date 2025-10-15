import json
from utils import str_to_int_keys, merge_shots_and_hits

# Load in another notebook
with open("data_json/bounces.json", 'r') as f:
    dico_bounces = json.load(f)

# Load in another notebook
with open("data_json/hits.json", 'r') as f:
    dico_hits = json.load(f)

# Load in another notebook
with open("data_json/players.json", 'r') as f:
    dico_players = json.load(f)

# Load in another notebook
with open("data_json/trajectories.json", 'r') as f:
    dico_trajectories = json.load(f)


# Load in another notebook
with open("data_json/ball_info.json", 'r') as f:
    dico_ball = json.load(f)

with open("data_json/shot_classif.json", 'r') as f:
    dico_shots = json.load(f)


output_path = "data_json/smoothed_tracks.json"

with open(output_path, 'r') as json_file:
    smoothed_tracks = str_to_int_keys(json.load(json_file))

with open("data_json/frames_data.json", 'r', encoding='utf-8') as f5:
    frames_data = json.load(f5) 


player_info = {
    0: {'name': 'Sinner', 'handedness': 'right handed'},
    1: {'name': 'Djokovic', 'handedness': 'right handed'}
}

dico_shots = merge_shots_and_hits(dico_shots, dico_hits)