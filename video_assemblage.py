import cv2
import numpy as np
from pathlib import Path

def assemble_four_videos(
    video1_path: str,
    video2_path: str = None,
    video3_path: str = None,
    video4_path: str = None,
    output_path: str = "output.avi",
    bottom_h: int = 900,
    bottom_w_left: int = 1210,
    fourcc: str = "avc1",
):
    TOP_H = 1080
    W1 = 1920
    W2 = 500 if video2_path else 0
    TOTAL_W = W1 + W2

    include_bottom = bool(video3_path or video4_path)
    TOTAL_H = TOP_H + (bottom_h if include_bottom else 0)
    bottom_w_right = TOTAL_W - bottom_w_left if include_bottom else 0

    def try_open(path):
        if path is None or not Path(path).exists():
            return None
        cap = cv2.VideoCapture(path)
        return cap if cap.isOpened() else None

    # Open videos
    cap1 = try_open(video1_path)
    cap2 = try_open(video2_path)
    cap3 = try_open(video3_path)
    cap4 = try_open(video4_path)

    if cap1 is None:
        raise FileNotFoundError("❌ Vidéo 1 obligatoire.")

    # Determine common frame count
    caps = [c for c in [cap1, cap2, cap3, cap4] if c]
    frame_counts = [int(c.get(cv2.CAP_PROP_FRAME_COUNT)) for c in caps]
    common_frames = min(frame_counts)
    fps = cap1.get(cv2.CAP_PROP_FPS) or 30

    # Writer
    writer = cv2.VideoWriter(
        output_path,
        cv2.VideoWriter_fourcc(*fourcc),
        fps,
        (TOTAL_W, TOTAL_H),
        isColor=True,
    )

    for _ in range(common_frames):
        rets_frames = [
            (c.read() if c else (True, None))
            for c in [cap1, cap2, cap3, cap4]
        ]

        if not rets_frames[0][0]:
            break  # failed to read frame from video1

        f1 = cv2.resize(rets_frames[0][1], (W1, TOP_H))
        f2 = (
            cv2.resize(rets_frames[1][1], (W2, TOP_H))
            if W2 > 0 and rets_frames[1][1] is not None
            else np.zeros((TOP_H, W2, 3), dtype=np.uint8)
        )

        # Create canvas
        canvas = np.zeros((TOTAL_H, TOTAL_W, 3), dtype=np.uint8)
        canvas[0:TOP_H, 0:W1] = f1
        if W2 > 0:
            canvas[0:TOP_H, W1:W1+W2] = f2

        if include_bottom:
            f3 = (
                cv2.resize(rets_frames[2][1], (bottom_w_left, bottom_h))
                if rets_frames[2][1] is not None
                else np.zeros((bottom_h, bottom_w_left, 3), dtype=np.uint8)
            )
            f4 = (
                cv2.resize(rets_frames[3][1], (bottom_w_right, bottom_h))
                if rets_frames[3][1] is not None
                else np.zeros((bottom_h, bottom_w_right, 3), dtype=np.uint8)
            )
            canvas[TOP_H:TOTAL_H, 0:bottom_w_left] = f3
            canvas[TOP_H:TOTAL_H, bottom_w_left:TOTAL_W] = f4

        writer.write(canvas)

    for c in [cap1, cap2, cap3, cap4]:
        if c: c.release()
    writer.release()

    print(f"✅ Vidéo écrite : {Path(output_path).resolve()}")



import os
import math
import cv2
import numpy as np
from pathlib import Path

def assemble_four_videos(
    video1_path: str,
    video2_path: str = None,
    video3_path: str = None,
    video4_path: str = None,
    output_path: str = "output.mp4",
    bottom_h: int = 900,
    bottom_w_left: int = 1210,
    fourcc: str = "mp4v",   # safer default than 'avc1' in many Linux containers
):
    """
    Stack up to 4 videos:
      ┌─────────────────── TOP_H (=1080) ───────────────────┐
      │  video1 (1920x1080) | optional video2 (500x1080)    │
      └──────────────────────────────────────────────────────┘
      ┌────────────────── bottom_h ──────────────────────────┐
      │ video3 (bottom_w_left x bottom_h) | video4 (rest)    │
      └──────────────────────────────────────────────────────┘
    Output size = (W1 + W2, TOP_H [+ bottom_h if bottom row included])
    """

    # --- Layout constants (expected by your pipeline) ---
    TOP_H = 1080
    W1 = 1920
    W2 = 500 if video2_path else 0
    TOTAL_W = W1 + W2

    include_bottom = bool(video3_path or video4_path)
    TOTAL_H = TOP_H + (bottom_h if include_bottom else 0)
    bottom_w_right = (TOTAL_W - bottom_w_left) if include_bottom else 0
    if include_bottom and bottom_w_right < 0:
        raise ValueError(f"bottom_w_left ({bottom_w_left}) > TOTAL_W ({TOTAL_W}).")

    # --- Helpers ---
    def try_open(path):
        if path is None:
            return None
        p = Path(path)
        if not p.exists():
            print(f"[assemble] Skipping missing video: {p}")
            return None
        cap = cv2.VideoCapture(str(p))
        if not cap.isOpened():
            print(f"[assemble] Cannot open video: {p}")
            return None
        return cap

    def safe_fps(cap, fallback=25.0):
        fps = cap.get(cv2.CAP_PROP_FPS)
        if not fps or math.isnan(fps) or fps <= 0:
            return float(fallback)
        return float(fps)

    def ensure_parent_dir(path_str):
        Path(path_str).parent.mkdir(parents=True, exist_ok=True)

    def open_writer_with_fallback(out_path, fps, size, preferred):
        for code in preferred:
            code4 = cv2.VideoWriter_fourcc(*code)
            vw = cv2.VideoWriter(out_path, code4, fps, size, isColor=True)
            if vw.isOpened():
                print(f"[assemble] Using codec: {code}")
                return vw, code
            else:
                vw.release()
        return None, None

    # --- Open videos ---
    cap1 = try_open(video1_path)
    cap2 = try_open(video2_path)
    cap3 = try_open(video3_path)
    cap4 = try_open(video4_path)

    if cap1 is None:
        raise FileNotFoundError("❌ Vidéo 1 obligatoire (video1_path missing or cannot be opened).")

    # Determine frame budget
    caps = [c for c in [cap1, cap2, cap3, cap4] if c is not None]
    frame_counts = []
    for c in caps:
        cnt = int(c.get(cv2.CAP_PROP_FRAME_COUNT))
        # Some containers report 0; we’ll treat that as 'unknown' and fall back to iteration below
        frame_counts.append(cnt if cnt > 0 else 10**9)
    common_frames = min(frame_counts) if frame_counts else 0
    fps = safe_fps(cap1, fallback=25.0)

    print(f"[assemble] Layout: {TOTAL_W}x{TOTAL_H} (top: {W1}+{W2} x {TOP_H}, bottom_h: {bottom_h if include_bottom else 0})")
    print(f"[assemble] common_frames (upper-bound): {common_frames}, fps: {fps:.2f}")

    # --- Writer (with codec fallback) ---
    ensure_parent_dir(output_path)
    preferred_codecs = (fourcc, "mp4v", "avc1", "H264", "MJPG")
    writer, used_codec = open_writer_with_fallback(
        str(output_path),
        fps,
        (TOTAL_W, TOTAL_H),
        preferred=preferred_codecs
    )
    if writer is None:
        raise RuntimeError(
            "Could not open VideoWriter for output. Tried codecs: "
            + ", ".join(preferred_codecs)
            + ". Ensure `ffmpeg` is installed in the container, or switch to a supported codec."
        )

    # --- Main loop ---
    frames_written = 0
    while True:
        # If we have an upper-bound (common_frames), stop there
        if frames_written >= common_frames:
            break

        rets_frames = []
        for c in (cap1, cap2, cap3, cap4):
            if c is None:
                rets_frames.append((True, None))
            else:
                ok, frame = c.read()
                rets_frames.append((ok, frame))

        # Stop if we cannot read from primary video
        if not rets_frames[0][0]:
            break

        f1_raw = rets_frames[0][1]
        if f1_raw is None:
            break
        f1 = cv2.resize(f1_raw, (W1, TOP_H))

        f2 = (
            cv2.resize(rets_frames[1][1], (W2, TOP_H))
            if W2 > 0 and rets_frames[1][1] is not None
            else np.zeros((TOP_H, W2, 3), dtype=np.uint8)
        )

        # Canvas
        canvas = np.zeros((TOTAL_H, TOTAL_W, 3), dtype=np.uint8)
        canvas[0:TOP_H, 0:W1] = f1
        if W2 > 0:
            canvas[0:TOP_H, W1:W1 + W2] = f2

        if include_bottom:
            f3 = (
                cv2.resize(rets_frames[2][1], (bottom_w_left, bottom_h))
                if rets_frames[2][1] is not None
                else np.zeros((bottom_h, bottom_w_left, 3), dtype=np.uint8)
            )
            f4 = (
                cv2.resize(rets_frames[3][1], (bottom_w_right, bottom_h))
                if rets_frames[3][1] is not None
                else np.zeros((bottom_h, bottom_w_right, 3), dtype=np.uint8)
            )
            canvas[TOP_H:TOP_H + bottom_h, 0:bottom_w_left] = f3
            canvas[TOP_H:TOP_H + bottom_h, bottom_w_left:TOTAL_W] = f4

        writer.write(canvas)
        frames_written += 1

    # --- Cleanup ---
    for c in (cap1, cap2, cap3, cap4):
        if c is not None:
            c.release()
    writer.release()

    outp = Path(output_path).resolve()
    size_str = f"{outp.stat().st_size/1e6:.2f} MB" if outp.exists() else "NA"
    print(f"✅ Vidéo écrite : {outp} | frames={frames_written} | fps≈{fps:.2f} | size={size_str}")
    return str(outp)
