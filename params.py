# Nom des keypoints du terrain
labels = [
    "coin ext 1", "coin ext 2", "coin ext 3", "coin ext 4",
    "coin int 1", "coin int 2", "coin int 3", "coin int 4",
    "service 1", "service 2", "service 3", "service 4",
    "milieu 1", "milieu 2"
]

# Lignes du terrain, chaque tuple représente une ligne entre deux points
lines = [
    (0, 1), (0, 4), (1, 5), (4, 8), (8, 9), (9, 5), (4, 7), (8, 12), (9, 13), (5, 6),
    (12, 13), (11, 12), (10, 13), (7, 11), (10, 11), (6, 10), (3, 7), (2, 6), (2, 3)
]

# Points de référence du terrain, chaque clé correspondant à un index de keypoint
# et chaque valeur étant un tuple (x, y) représentant les coordonnées du point
# dans le système de coordonnées du terrain (en cm)
ref_points = {
    0: (0, 0),
    1: (0, 2377),
    2: (1097, 2377),
    3: (1097, 0),
    4: (137, 0),
    5: (137, 2377),
    6: (960, 2377),
    7: (960, 0),
    8: (137, 548),
    9: (137, 1829),
    10: (960, 1829),
    11: (960, 548),
    12: (548.5, 548),
    13: (548.5, 1829)
}
