import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

def draw_table_frame(speeds, shot_classif, player_info, frame_idx, fps=25,
                     smoothing_window=25,
                     last_max_state=None,
                     last_max_state_ = None,
                     last_shot_state=None):
    
    SHOT_ICONS = {
        "service": "🎯",
        "groundstroke forehand": "🤚",
        "groundstroke backhand": "✋",
        "volley": "🥎",
        "smash": "💥",
        "default": "🎾"
    }

    fig, ax = plt.subplots(figsize=(6.8, 2.2))  # Smaller and square layout
    ax.axis('off')

    players = sorted(player_info.keys())
    col_labels = ["Player", "Avg Speed", "Max Speed", "Avg Shot", "Max Shot"]
    table_data = []
    cell_colors = []

    new_max_state = {}
    new_shot_state = {}

    for player in players:
        name = player_info[player]['name']
        frame_keys = sorted([f for f in speeds[player] if f <= frame_idx])
        speed_vals = [speeds[player][f] for f in frame_keys]

        if len(speed_vals) >= smoothing_window:
            avg_speed = np.mean(speed_vals[-smoothing_window:])
        else:
            avg_speed = np.mean(speed_vals) if speed_vals else 0
        max_speed = np.max(speed_vals) if speed_vals else 0

        player_shots = [s for s in shot_classif if s['player'] == player and s['frame'] <= frame_idx]
        shot_dists = [s['distance'] for s in player_shots]
        avg_shot = np.mean(shot_dists) if shot_dists else 0
        max_shot = np.max(shot_dists) if shot_dists else 0

        # Last shot type with emoji
        if player_shots:
            last_shot = player_shots[-1]
            shot_type = last_shot['type']
            icon = SHOT_ICONS.get(shot_type, SHOT_ICONS['default'])
        else:
            shot_type = None
            icon = ""

        new_max_state[player] = {"max_speed": max_speed, "max_shot": max_shot}
        new_shot_state[player] = shot_type

        row = [
            name,
            f"{avg_speed:.1f}",
            f"{max_speed:.1f}",
            f"{avg_shot:.1f}",
            f"{max_shot:.1f}"
        ]
        table_data.append(row)

        # Cell colors
        color_row = ['white', 'white']  # Player, Last Shot, Avg Speed

        # Highlight max speed if new
        prev_max_speed = last_max_state.get(player, {}).get("max_speed") if last_max_state else None
        if prev_max_speed is None or max_speed > prev_max_speed:
            color_row.append('#ede621')  # light green
        else:
            color_row.append('white')

        prev_max_shot = last_max_state_.get(player, {}).get("max_shot") if last_max_state_ else None
        if prev_max_shot is None or max_shot > prev_max_shot:
            color_row.append('#ede621')  # light green
        else:
            color_row.append('white')

        color_row += ['white']  # Avg Shot, Max Shot
        cell_colors.append(color_row)

    # Draw table
    table = ax.table(cellText=table_data,
                     colLabels=col_labels,
                     cellLoc='center',
                     cellColours=cell_colors,
                     loc='center')

    table.auto_set_font_size(False)
    table.set_fontsize(12)
    table.scale(1.4, 1.6)

    # Style header
    for key, cell in table.get_celld().items():
        row, col = key
        if row == 0:
            cell.set_text_props(weight='bold', color='white')
            cell.set_facecolor('#444444')

    # Render to image
    canvas = FigureCanvas(fig)
    canvas.draw()
    img = np.asarray(canvas.get_renderer().buffer_rgba())[..., :3].copy()
    plt.close(fig)
    return img, new_max_state, new_shot_state




def create_table_video(bbox_dico, shot_classif, player_info, output_path="table_stats_styled.mp4", fps=25):
    speeds = compute_speeds(bbox_dico, fps)
    all_frames = sorted(set.intersection(*(set(speeds[p].keys()) for p in player_info)))

    last_max_state = {}
    last_max_state_ = {}
    last_shot_state = {}
    sample_img, _, _ = draw_table_frame(speeds, shot_classif, player_info, all_frames[0], fps,
                                        last_max_state=last_max_state,
                                        last_max_state_ = last_max_state_,
                                        last_shot_state=last_shot_state)
    
    h, w, _ = sample_img.shape
    out = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (w, h))

    for frame in all_frames:
        frame_img, last_max_state, last_shot_state = draw_table_frame(
            speeds, shot_classif, player_info, frame, fps,
            last_max_state=last_max_state,
            last_shot_state=last_shot_state
        )

        frame_bgr = cv2.cvtColor(frame_img, cv2.COLOR_RGB2BGR)
        out.write(frame_bgr)

    out.release()
    print(f"Saved with max transitions: {output_path}")

