import cv2
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import savgol_filter
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import io

import cv2
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import savgol_filter
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

def prepare_data(dico, fps=25):
    data = {}
    for player, player_data in dico.items():
        frames = sorted(int(f) for f in player_data.keys())
        frames_str = [str(f) for f in frames]
        coords = np.array([[player_data[f]["x"], player_data[f]["y"]] for f in frames_str])
        speeds = np.array([player_data[f]["speed"] for f in frames_str])
        ys = coords[:, 1]

        # Cumulative distance
        dists = np.linalg.norm(np.diff(coords, axis=0), axis=1)
        dists = np.insert(dists, 0, 0)
        cumdist = np.cumsum(dists)

        # Distance from y=1097
        dist_to_1097 = np.where(ys < 1097, ys, ys - 2377)

        data[player] = {
            "frames": np.array(frames),
            "Speed": speeds,
            "Distance": cumdist,
            "Depth": dist_to_1097
        }
    return data


      
def draw_dynamic_graph(data, player_info, frame_idx, keys_to_plot, fps=25, smooth=False, window_sec=2):
    n_graphs = len(keys_to_plot)
    fig_height = 3.5
    fig, axes = plt.subplots(n_graphs, 1, figsize=(10, fig_height * n_graphs), sharex=True)
    if n_graphs == 1:
        axes = [axes]

    current_time = frame_idx / fps
    xmin = current_time - window_sec
    xmax = current_time + window_sec

    for i, key in enumerate(keys_to_plot):
        ax = axes[i]
        ymin, ymax = float("inf"), float("-inf")

        for player in data:
            frames = data[player]['frames']
            x = frames / fps
            y = data[player][key]

            mask = (x >= xmin) & (x <= xmax)
            x_visible = x[mask] - current_time  # shift to be centered around 0
            y_visible = y[mask]

            if len(x_visible) == 0:
                continue

            if smooth and len(y_visible) >= 11:
                y_visible = savgol_filter(y_visible, window_length=11, polyorder=2)

            ax.plot(x_visible, y_visible, label=f"{player_info[int(player)]['name']}", color='blue' if player == '1' else 'red')

            ymin = min(ymin, y_visible.min())
            ymax = max(ymax, y_visible.max())

        if ymin < ymax:
            ax.set_ylim(ymin * 0.95, ymax * 1.05)

        ax.set_xlim(-window_sec, window_sec)  # fixed centered window
        ax.axvline(0, color='black', linestyle='--')  # vertical center line
        ax.set_ylabel(key)
        if i == n_graphs - 1:
            ax.set_xlabel("Time relative to frame (s)")
        ax.legend()

    canvas = FigureCanvas(fig)
    canvas.draw()
    img = np.asarray(canvas.buffer_rgba())[:, :, :3].copy()
    plt.close(fig)
    return img

def create_analysis_video(dico, player_info, keys_to_plot, output_path="dynamic_graphs.mp4", fps=25, smooth=True):
    data = prepare_data(dico, fps)

    # Get common frames
    frame_sets = [set(data[player]['frames']) for player in data]
    common_frames = sorted(set.intersection(*frame_sets))

    if not common_frames:
        raise ValueError("No common frames")

    sample_img = draw_dynamic_graph(data, player_info, common_frames[0], keys_to_plot, fps, smooth=smooth)
    h, w, _ = sample_img.shape
    out = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*'avc1'), fps, (w, h))

    for frame_idx in common_frames:
        frame_img = draw_dynamic_graph(data, player_info, frame_idx, keys_to_plot, fps, smooth=smooth)
        frame_bgr = cv2.cvtColor(frame_img, cv2.COLOR_RGB2BGR)
        out.write(frame_bgr)

    out.release()
    print(f"✅ Saved dynamic analysis video: {output_path}")
