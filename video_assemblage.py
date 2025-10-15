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
