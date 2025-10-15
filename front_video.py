import numpy as np 
import cv2
import matplotlib.pyplot as plt
import supervision as sv
import pandas as pd
from collections import deque


def create_players_graphics(out, frame, frame_idx, trajectory_buffer, team_tracks, smoothed_tracks, tail_length, ellipse=True, tail=True, name=True):
        #trajectory_buffer = {0: [], 1: []} 
        for team_id in [0, 1]:
            if frame_idx in smoothed_tracks[team_id]:
                x, y = smoothed_tracks[team_id][frame_idx]

                # Estimate dynamic ellipse size from recent motion
                recent_frames = [f for f in range(frame_idx - 5, frame_idx + 1) if f in smoothed_tracks[team_id]]
                if len(recent_frames) >= 2:
                    ys = [smoothed_tracks[team_id][f][1] for f in recent_frames]
                    bbox_heights = np.abs(np.diff(ys))
                    est_h = np.clip(np.mean(bbox_heights) * 10 + 80, 100, 180)
                else:
                    est_h = 120

                ellipse_w, ellipse_h = int(est_h * 0.9), int(est_h)

                center_x = int(x)
                foot_y = int(y)
                fx1 = int(center_x - ellipse_w / 2)
                fy1 = int(foot_y - ellipse_h)
                fx2 = int(center_x + ellipse_w / 2)
                fy2 = int(foot_y)

                color = (27, 94, 32) if team_id == 0 else (198, 40, 40)
                ellipse_annotator = sv.EllipseAnnotator(color=sv.Color(*color[::-1]), thickness=3)
                detection = sv.Detections(
                    xyxy=np.array([[fx1, fy1, fx2, fy2]]),
                    confidence=np.array([1.0]),
                    class_id=np.array([0])
                )
                if ellipse:
                    frame = ellipse_annotator.annotate(scene=frame, detections=detection)

                # Draw team label
                if name:
                    label_text = "SINNER" if team_id == 0 else "DJOKOVIC"
                    text_position = (fx1, max(0, fy1 - 20))  # Draw 10 pixels above top of ellipse
                    cv2.putText(frame, label_text, text_position,
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2, cv2.LINE_AA)

                # Tail drawing
                if tail:
                    trajectory_buffer[team_id].append((center_x, foot_y))
                    if len(trajectory_buffer[team_id]) > tail_length:
                        trajectory_buffer[team_id] = trajectory_buffer[team_id][-tail_length:]

                    num_points = len(trajectory_buffer[team_id])
                    for i, (tx, ty) in enumerate(trajectory_buffer[team_id]):
                        alpha = int(255 * (i + 1) / num_points)
                        tail_color = tuple(int(c * (alpha / 255)) for c in color)
                        cv2.circle(frame, (int(tx), int(ty)), 4, tail_color, -1)

        
        return out.write(frame)


def create_players_graphics(dico_player, out, frame, frame_idx, trajectory_buffer, team_tracks, smoothed_tracks, tail_length, ellipse=True, tail=True, name=True, debug=False):
    for team_id in [0, 1]:
        if frame_idx in smoothed_tracks[team_id]:
            x1, y1, x2, y2 = smoothed_tracks[team_id][frame_idx]

            # 1. Get bottom center of bbox
            center_x = int((x1 + x2) / 2)
            foot_y = int(y2)

            # 2. Estimate ellipse size proportional to bbox size
            width = x2 - x1
            height = y2 - y1
            est_area = width * height
            base_area = 80 * 160  # Reference area
            scale = np.sqrt(est_area / base_area)

            ellipse_h = int(100 * scale)
            ellipse_w = int(ellipse_h * 0.9)

            fx1 = int(center_x - ellipse_w / 2)
            fy1 = int(foot_y - ellipse_h)
            fx2 = int(center_x + ellipse_w / 2)
            fy2 = int(foot_y)

            color = (40, 40, 198) if team_id == 0 else (198, 40, 40)
            ellipse_annotator = sv.EllipseAnnotator(color=sv.Color(*color[::-1]), thickness=3)
            detection = sv.Detections(
                xyxy=np.array([[fx1, fy1, fx2, fy2]]),
                confidence=np.array([1.0]),
                class_id=np.array([0])
            )
            if ellipse:
                frame = ellipse_annotator.annotate(scene=frame, detections=detection)

            # 3. Draw player name 3px above the top of bbox
            if name:
                
                #label_text = "SINNER" if team_id == 0 else "DJOKOVIC"
                label_text = dico_player[team_id]['name']
                text_position = (int(x1), max(0, int(y1) - 3))
                cv2.putText(frame, label_text, text_position,
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2, cv2.LINE_AA)

            # 4. Tail drawing
            if tail:
                trajectory_buffer[team_id].append((center_x, foot_y))
                if len(trajectory_buffer[team_id]) > tail_length:
                    trajectory_buffer[team_id] = trajectory_buffer[team_id][-tail_length:]

                num_points = len(trajectory_buffer[team_id])
                for i, (tx, ty) in enumerate(trajectory_buffer[team_id]):
                    alpha = int(255 * (i + 1) / num_points)
                    tail_color = tuple(int(c * (alpha / 255)) for c in color)
                    cv2.circle(frame, (int(tx), int(ty)), 4, tail_color, -1)

    # 5. Optional debug plots
    if debug:
        xy_0 = pd.DataFrame(team_tracks[0]).T
        xy_1 = pd.DataFrame(team_tracks[1]).T
        clean_xy_0 = pd.DataFrame(clean_and_smooth_track(team_tracks[0], speed_thresh=1, return_window=10, return_dist=10)).T
        clean_xy_1 = pd.DataFrame(clean_and_smooth_track(team_tracks[1], speed_thresh=1, return_window=10, return_dist=10)).T

        plt.title(f"video {frame_idx} player 0")
        xy_0[1].plot(label='Raw Y')
        clean_xy_0[1].plot(label='Cleaned Y')
        plt.legend()
        plt.show()

        xy_0[0].plot(label='Raw X')
        clean_xy_0[0].plot(label='Cleaned X')
        plt.legend()
        plt.show()

        plt.title(f"video {frame_idx} player 1")
        xy_1[1].plot(label='Raw Y')
        clean_xy_1[1].plot(label='Cleaned Y')
        plt.legend()
        plt.show()

        xy_1[0].plot(label='Raw X')
        clean_xy_1[0].plot(label='Cleaned X')
        plt.legend()
        plt.show()

    return out.write(frame)



def create_video_front(input_video_path, player_xy, output_video_path, dico_player, ellipse=True, tail=True, name=True, debug=False):
    trajectory_buffer = {0: [], 1: []} 
    team_tracks = {0: {}, 1: {}} 
    cap = cv2.VideoCapture(input_video_path) 

    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    out = cv2.VideoWriter(output_video_path, cv2.VideoWriter_fourcc(*'MJPG'), fps, (width, height))
        
    tail_length = int(fps * 2)  
    print(tail_length) 

    frame_idx = 0
    while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            create_players_graphics(dico_player, out, frame, frame_idx, trajectory_buffer, team_tracks, player_xy, tail_length, ellipse, tail, name, debug)
            frame_idx += 1
    cap.release()
    out.release()
    return print(f"Video {output_video_path} is created !")



def annotate_video_with_hits_overlay(
    video_path,
    player_info,
    player_xy,
    dico_ball,
    dico_shots,
    ellipse,
    tail,
    name,
    ball_show,
    player_annot_show,
    speed_tail,
    bounce_show,
    hit_show,
    output_path="annotated_hits_overlay.mp4",
    tail_duration=1.5): 
    """ Annotate video with ball trajectory, hits, and bounces overlay.
    Args:
        video_path (str): Path to the input video file.
        dico_ball (dict): Dictionary containing ball trajectory data.
        output_path (str): Path to save the annotated video.
        tail_duration (float): Duration of the tail in seconds.
    """
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    tail_length = int(tail_duration * fps)

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    out = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*'MJPG'), fps, (width, height))

    # Step 1: Get hit classifications
    hit_results = dico_shots

    # Map hit messages per frame range
    hit_overlay_text = {}
    for i, res in enumerate(hit_results):
        start = res["frame"]
        #end = hit_results[i + 1]["frame"] if i + 1 < len(hit_results) else float('inf')
        end = hit_results[i + 1]["frame"] if i + 1 < len(hit_results) else int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        for f in range(start, end):
            hit_overlay_text[f] = f"{res['player name']}{res['type'][13:]} at {np.round(res['speed'],0)}km/h"

    # Step 2: Interpolated ball DataFrame
    df = pd.DataFrame.from_dict(dico_ball, orient='index')
    df.index = df.index.astype(int)
    df = df.sort_index()
    df[['x', 'y']] = df[['x', 'y']].astype('float')
    df['x_interp'] = df['x'].interpolate(limit_direction='both')
    df['y_interp'] = df['y'].interpolate(limit_direction='both')

    # Step 3: Render frames
    frame_idx = 0
    tail_buffer = deque()
    bounce_positions = []
    trajectory_buffer = {0: [], 1: []} 
    team_tracks = {0: {}, 1: {}} 

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx not in df.index:
            out.write(frame)
            frame_idx += 1
            continue

        row = df.loc[frame_idx]
        x, y = int(row['x_interp']), int(row['y_interp'])
        action = dico_ball.get(str(frame_idx), {}).get("action", "air")
        
        if ball_show :
        # --- Draw tail ---
            tail_buffer.append((x, y, frame_idx))
            while tail_buffer and frame_idx - tail_buffer[0][2] > tail_length:
                tail_buffer.popleft()
            # Draw colored tail line by connecting points
            for j in range(1, len(tail_buffer)):
                x1, y1, f1 = tail_buffer[j - 1]
                x2, y2, f2 = tail_buffer[j]
                if None in [x1, y1, x2, y2]: continue

                # Compute speed (pixels per frame)
                dist = np.hypot(x2 - x1, y2 - y1)
                speed = dist / max(f2 - f1, 1)

                # Map speed to color (green = slow, red = fast)
                # Define thresholds based on your video scale
                min_speed, max_speed = 1, 50  # tune if needed
                norm_speed = np.clip((speed - min_speed) / (max_speed - min_speed), 0, 1)
                if speed_tail:
                    color = (
                        0,        # R
                        int(255 * (1 - norm_speed)),  # G
                        int(255 * norm_speed)                             # B
                    )
                else : 
                    color = (0, 255, 255)  # Yellow in BGR

                cv2.line(frame, (int(x1), int(y1)), (int(x2), int(y2)), color, 3)

            # --- Draw current ball ---
            if row.get("visible", True):
                cv2.circle(frame, (x, y), 8, (0, 200, 255), -1)

            # --- Draw bounce marker ---
        if bounce_show:
            if action == "bounce":
                bounce_positions.append((x, y))  # store the bounce position

            # Draw all stored bounces
            for bx, by in bounce_positions:
                cv2.ellipse(frame, (bx, by), (12, 6), 0, 0, 360, (0, 255, 255), 2)

        # --- Draw HIT splash ---
        if hit_show : 
            if action == "hit":
                cv2.circle(frame, (x, y), 20, (255, 0, 0), 2)
                cv2.line(frame, (x - 10, y - 10), (x + 10, y + 10), (255, 0, 0), 2)
                cv2.line(frame, (x - 10, y + 10), (x + 10, y - 10), (255, 0, 0), 2)

        # --- Draw overlay text if needed ---
        if player_annot_show:
            if frame_idx in hit_overlay_text:
                text = hit_overlay_text[frame_idx]
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 1.8
                thickness = 5
                color = (30, 255, 255)  # orange/blue
                text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
                text_x = (frame.shape[1] - text_size[0]) // 2
                text_y = int(frame.shape[0] * 0.12)
                cv2.putText(frame, text, (text_x, text_y), font, font_scale, color, thickness, cv2.LINE_AA)
        
        out.write(frame)
        frame_idx += 1

    cap.release()
    out.release()
    print(f"✅ Video saved to: {output_path}")
