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


# --- Cell 1: robust create_analysis_video (AVI -> H.264 MP4) ---
import os, math, subprocess
from pathlib import Path
import cv2
import numpy as np

def _ensure_parent_dir(p: Path):
    p.parent.mkdir(parents=True, exist_ok=True)

def _ffmpeg_to_h264(src_path: Path, dst_path: Path) -> None:
    # Requires `ffmpeg` in your Dockerfile (apt-get install ffmpeg)
    cmd = [
        "ffmpeg", "-y",
        "-i", str(src_path),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        str(dst_path),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def create_analysis_video(dico, player_info, keys_to_plot, output_path="dynamic_graphs.mp4", fps=25, smooth=True):
    """
    Writes a temp AVI (MJPG) with OpenCV, then transcodes to H.264 yuv420p MP4.
    This avoids codec issues on Cloud Run and guarantees browser playback.
    """
    # 1) Prepare data and frames
    data = prepare_data(dico, fps)  # <-- your existing function

    frame_sets = [set(data[player]['frames']) for player in data]
    common_frames = sorted(set.intersection(*frame_sets))
    if not common_frames:
        raise ValueError("No common frames")

    # 2) First frame to determine width/height
    sample_img_rgb = draw_dynamic_graph(data, player_info, common_frames[0], keys_to_plot, fps, smooth=smooth)  # RGB
    h, w, _ = sample_img_rgb.shape

    # 3) Output paths
    output_path = Path(output_path)
    _ensure_parent_dir(output_path)
    tmp_avi = output_path.with_suffix(".avi")  # temp container for OpenCV

    # 4) OpenCV writer (MJPG -> highly compatible)
    mjpg = cv2.VideoWriter_fourcc(*"MJPG")
    out = cv2.VideoWriter(str(tmp_avi), mjpg, float(fps), (w, h), True)
    if not out.isOpened():
        raise RuntimeError("OpenCV VideoWriter failed to open with MJPG. "
                           "Check permissions and that /tmp is writable on Cloud Run.")

    # 5) Write frames (convert RGB->BGR for OpenCV)
    for frame_idx in common_frames:
        frame_img_rgb = draw_dynamic_graph(data, player_info, frame_idx, keys_to_plot, fps, smooth=smooth)
        frame_bgr = cv2.cvtColor(frame_img_rgb, cv2.COLOR_RGB2BGR)
        out.write(frame_bgr)

    out.release()

    # 6) Transcode to H.264 yuv420p + faststart (browser-friendly)
    _ffmpeg_to_h264(tmp_avi, output_path)

    # 7) Clean temp
    try:
        tmp_avi.unlink(missing_ok=True)
    except Exception:
        pass

    print(f"✅ Saved dynamic analysis video (H.264): {output_path}")
    return str(output_path)

