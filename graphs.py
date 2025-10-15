import cv2
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import savgol_filter
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import io

def compute_centroids(bbox_dico):
    centroids = {0: {}, 1: {}}
    for player in bbox_dico:
        for frame_idx, (x1, y1, x2, y2) in bbox_dico[player].items():
            cx = (x1 + x2) / 2
            cy = min(y1, y2) # (y1 + y2) / 2
            centroids[player][frame_idx] = (cx, cy)
    return centroids

def compute_distances_and_speeds(centroids, fps=25):
    data = {}
    for player, frames in centroids.items():
        sorted_frames = sorted(frames.keys())
        coords = np.array([centroids[player][f] for f in sorted_frames])
        dists = np.linalg.norm(np.diff(coords, axis=0), axis=1)
        dists = np.insert(dists, 0, 0)  # insert 0 for first frame
        cumdist = np.cumsum(dists)
        speed = dists * fps  # pixels/sec

        data[player] = {
            "frames": np.array(sorted_frames),
            "cumdist": cumdist,
            "speed": speed
        }
    return data



def draw_graph_frame(data, frame_idx, fps=25, window_sec=5, smooth=False):
    window = int(window_sec * fps)
    fig, axes = plt.subplots(2, 1, figsize=(10, 4), sharex=True)
    
    # Time aligned per player
    for i, key in enumerate(["cumdist", "speed"]):
        ax = axes[i]
        for player in [0, 1]:
            frames = data[player]['frames']
            y = data[player][key]
            x = frames / fps

            # Only plot if lengths match
            if len(x) != len(y):
                continue

            if smooth and len(y) >= 11:
                y = savgol_filter(y, window_length=11, polyorder=2)
            ax.plot(x, y, label=f"Player {player}", color='blue' if player == 0 else 'red')

        # Set window range
        current_time = frame_idx / fps
        xmin = current_time - window_sec
        xmax = current_time + window_sec
        ax.set_xlim(xmin, xmax)

        # Compute dynamic y-limits from visible range
        ymin, ymax = float('inf'), float('-inf')
        for player in [0, 1]:
            frames = data[player]['frames']
            y = data[player][key]
            x = frames / fps
            mask = (x >= xmin) & (x <= xmax)

            if mask.sum() == 0:
                continue

            y_visible = y[mask]
            if smooth and len(y_visible) >= 5:
                y_visible = savgol_filter(y_visible, window_length=5, polyorder=2)
            ymin = min(ymin, y_visible.min())
            ymax = max(ymax, y_visible.max())

        if ymin < ymax:
            ax.set_ylim(ymin * 0.95, ymax * 1.05)

        ax.axvline(current_time, color='black', linestyle='--')
        ax.set_ylabel(key)
        if i == 1:
            ax.set_xlabel("Time (s)")
        ax.legend()

    canvas = FigureCanvas(fig)
    canvas.draw()

    # Get the RGBA buffer from the figure
    renderer = canvas.get_renderer()
    img = np.asarray(renderer.buffer_rgba())

    # Convert RGBA to RGB if needed
    img = img[..., :3].copy()

    plt.close(fig)
    return img


def create_analysis_video(bbox_dico, output_path="output_analysis.mp4", fps=25, smooth=False):
    centroids = compute_centroids(bbox_dico)
    data = compute_distances_and_speeds(centroids, fps=fps)

    # Only use frames present in both players
    frames_0 = set(data[0]["frames"])
    frames_1 = set(data[1]["frames"])
    all_frames = sorted(frames_0.intersection(frames_1))

    if not all_frames:
        raise ValueError("No common frames between player 0 and 1")

    # Get image size for video
    sample_img = draw_graph_frame(data, all_frames[0], fps, smooth=smooth)
    h, w, _ = sample_img.shape
    out = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (w, h))

    for f in all_frames:
        frame_img = draw_graph_frame(data, f, fps, smooth=smooth)
        frame_bgr = cv2.cvtColor(frame_img, cv2.COLOR_RGB2BGR)
        out.write(frame_bgr)

    out.release()
    print(f"Saved analysis video to: {output_path}")

