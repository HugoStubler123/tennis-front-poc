import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

def draw_cumulative_table_frame(frame_idx, dico_players, dico_shots, player_info,
                                 params=["speed", "shot speed", "shot stats"],
                                 fps=25, last_max_state=None, fade_tracker=None,
                                 fade_duration=10):

    fig, ax = plt.subplots(figsize=(6.8, 2.2))
    ax.axis('off')

    players = sorted(player_info.keys())
    col_labels = ["Player"]
    table_data = []
    cell_colors = []
    cell_text_props = {}

    if last_max_state is None:
        last_max_state = {}
    if fade_tracker is None:
        fade_tracker = {}

    new_max_state = {}
    new_fade_tracker = fade_tracker.copy()

    for row_idx, player in enumerate(players, start=1):
        name = player_info[player]['name']
        row = [name]
        color_row = ['white']

        # --- SPEED
        if "speed" in params:
            frames = [int(f) for f in dico_players[str(player)].keys() if int(f) <= frame_idx]
            speeds = [dico_players[str(player)][str(f)]['speed'] for f in frames]

            avg_speed = np.mean(speeds) if speeds else 0
            max_speed = np.max(speeds) if speeds else 0

            row += [f"{avg_speed:.1f}", f"{max_speed:.1f}"]
            col_labels += ["Avg Speed", "Max Speed"]
            color_row += ["white", "white"]

            key = (player, "max_speed")
            prev_val = last_max_state.get(player, {}).get("max_speed", -1)

            if max_speed > prev_val:
                new_fade_tracker[key] = fade_duration
            elif key in new_fade_tracker:
                new_fade_tracker[key] = max(0, new_fade_tracker[key] - 1)

            fade_val = new_fade_tracker.get(key, 0)
            cell_text_props[(row_idx, len(row) - 1)] = {
                "weight": "bold" if fade_val > 0 else "normal",
                "size": 9 + int(3 * fade_val / fade_duration),
                "color": "black"
            }

            new_max_state.setdefault(player, {})["max_speed"] = max_speed

        # --- SHOT SPEED
        player_shots = [s for s in dico_shots if s["player"] == player and s["frame"] <= frame_idx]
        if "shot speed" in params:
            shot_speeds = [s["speed"] for s in player_shots]
            avg_shot_speed = np.mean(shot_speeds) if shot_speeds else 0
            max_shot_speed = np.max(shot_speeds) if shot_speeds else 0

            row += [f"{avg_shot_speed:.1f}", f"{max_shot_speed:.1f}"]
            col_labels += ["Avg Shot Spd", "Max Shot Spd"]
            color_row += ["white", "white"]

            key = (player, "max_shot_speed")
            prev_val = last_max_state.get(player, {}).get("max_shot_speed", -1)

            if max_shot_speed > prev_val:
                new_fade_tracker[key] = fade_duration
            elif key in new_fade_tracker:
                new_fade_tracker[key] = max(0, new_fade_tracker[key] - 1)

            fade_val = new_fade_tracker.get(key, 0)
            cell_text_props[(row_idx, len(row) - 1)] = {
                "weight": "bold" if fade_val > 0 else "normal",
                "size": 8 + int(3 * fade_val / fade_duration),
                "color": "black"
            }

            new_max_state.setdefault(player, {})["max_shot_speed"] = max_shot_speed

        # --- SHOT STATS
        if "shot stats" in params:
            depths = [s["depth"] for s in player_shots]
            lateralities = [s["laterality"] for s in player_shots]
            avg_depth = np.mean(depths) if depths else 0
            avg_lat = np.mean(lateralities) if lateralities else 0

            row += [f"{avg_depth:.1f}", f"{avg_lat:.1f}"]
            col_labels += ["Avg Depth", "Avg Laterality"]
            color_row += ["white", "white"]

        table_data.append(row)
        cell_colors.append(color_row)

    # --- Draw Table
    table = ax.table(cellText=table_data,
                     colLabels=col_labels,
                     cellLoc='center',
                     cellColours=cell_colors,
                     loc='center')

    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.scale(1.2, 1.6)

    for (row, col), cell in table.get_celld().items():
        if row == 0:
            cell.set_text_props(weight='bold', color='white')
            cell.set_facecolor('#444444')
        elif (row, col) in cell_text_props:
            props = cell_text_props[(row, col)]
            cell.set_text_props(**props)

    # --- Render
    canvas = FigureCanvas(fig)
    canvas.draw()
    img = np.asarray(canvas.get_renderer().buffer_rgba())[..., :3].copy()
    plt.close(fig)

    return img, new_max_state, new_fade_tracker

import cv2

def create_cumulative_stats_video(dico_players, dico_shots, player_info,
                                  output_path="cumulative_table.mp4",
                                  params=["speed", "shot speed", "shot stats"],
                                  fps=25, fade_duration=10):
    # Get common frames
    frame_keys = sorted([int(k) for k in dico_players['0'].keys()])
    total_frames = frame_keys[-1]

    # Sample every fps frame (1Hz)
    sampled_frames = [f for f in frame_keys if f % fps == 0]

    # Init table dimensions
    sample_img, _, _ = draw_cumulative_table_frame(
        frame_idx=sampled_frames[0],
        dico_players=dico_players,
        dico_shots=dico_shots,
        player_info=player_info,
        params=params,
        fps=fps,
        last_max_state=None,
        fade_tracker=None
    )
    h, w, _ = sample_img.shape

    # Init writer at real FPS (25)
    out = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*'avc1'), fps, (w, h))

    last_max_state = {}
    fade_tracker = {}

    for frame_idx in sampled_frames:
        frame_img, last_max_state, fade_tracker = draw_cumulative_table_frame(
            frame_idx, dico_players, dico_shots, player_info,
            params=params, fps=fps,
            last_max_state=last_max_state,
            fade_tracker=fade_tracker,
            fade_duration=fade_duration
        )
        for _ in range(fps):  # Repeat each frame to match real-time pace
            out.write(cv2.cvtColor(frame_img, cv2.COLOR_RGB2BGR))

    out.release()
    print(f"✅ Video saved to: {output_path}")

import cv2
import numpy as np

def create_cumulative_stats_video(dico_players, dico_shots, player_info,
                                  output_path="cumulative_table.mp4",
                                  params=["speed", "shot speed", "shot stats"],
                                  fps=25, fade_duration=10, updates_per_second=4):
    # Get frame list
    frame_keys = sorted([int(k) for k in dico_players['0'].keys()])
    total_frames = frame_keys[-1]
    
    # Interval between updates
    step = max(1, fps // updates_per_second)  # e.g. 6 if updates_per_second=4
    sampled_frames = list(range(0, total_frames + 1, step))

    # Initialize video writer
    sample_img, _, _ = draw_cumulative_table_frame(
        frame_idx=sampled_frames[0],
        dico_players=dico_players,
        dico_shots=dico_shots,
        player_info=player_info,
        params=params,
        fps=fps
    )
    h, w, _ = sample_img.shape
    out = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (w, h))

    # State tracking
    last_max_state = {}
    fade_tracker = {}

    for frame_idx in sampled_frames:
        # Draw updated table
        frame_img, last_max_state, fade_tracker = draw_cumulative_table_frame(
            frame_idx=frame_idx,
            dico_players=dico_players,
            dico_shots=dico_shots,
            player_info=player_info,
            params=params,
            fps=fps,
            last_max_state=last_max_state,
            fade_tracker=fade_tracker,
            fade_duration=fade_duration
        )

        # Write `step` frames to video
        for _ in range(step):
            out.write(cv2.cvtColor(frame_img, cv2.COLOR_RGB2BGR))

    out.release()
    print(f"✅ Video saved to: {output_path}")



import cv2
import numpy as np
def create_cumulative_stats_video(dico_players, dico_shots, player_info,
                                  output_path="cumulative_table.mp4",
                                  params=["speed", "shot speed", "shot stats"],
                                  fps=25, fade_duration=10):

    

    # Get full frame range from player 0
    frame_keys = sorted([int(k) for k in dico_players['0'].keys()])
    total_frames = frame_keys[-1]

    # Initial render to get shape
    sample_img, _, _ = draw_cumulative_table_frame(
        frame_idx=0,
        dico_players=dico_players,
        dico_shots=dico_shots,
        player_info=player_info,
        params=params,
        fps=fps
    )
    h, w, _ = sample_img.shape

    # Create video writer at 25 FPS
    out = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (w, h))

    # Init state
    last_max_state = {}
    fade_tracker = {}

    for frame_idx in range(0, total_frames + 1):
        frame_img, last_max_state, fade_tracker = draw_cumulative_table_frame(
            frame_idx=frame_idx,
            dico_players=dico_players,
            dico_shots=dico_shots,
            player_info=player_info,
            params=params,
            fps=fps,
            last_max_state=last_max_state,
            fade_tracker=fade_tracker,
            fade_duration=fade_duration
        )

        out.write(cv2.cvtColor(frame_img, cv2.COLOR_RGB2BGR))

    out.release()
    print(f"✅ Video saved to: {output_path}")
