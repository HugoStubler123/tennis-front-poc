import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from collections import deque
from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip, TextClip
from PIL import Image, ImageDraw, ImageFont
import io


def create_ellipse_image(width, height, ellipse_w, ellipse_h, center_x, foot_y, color, thickness=3):
    """Create an ellipse image using PIL"""
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Calculate ellipse bounds
    fx1 = center_x - ellipse_w // 2
    fy1 = foot_y - ellipse_h
    fx2 = center_x + ellipse_w // 2
    fy2 = foot_y
    
    # Draw ellipse outline
    for i in range(thickness):
        draw.ellipse([fx1-i, fy1-i, fx2+i, fy2+i], outline=color, width=1)
    
    return img


def create_frame_with_graphics(frame_array, frame_idx, trajectory_buffer, smoothed_tracks, 
                              tail_length, dico_player, ellipse=True, tail=True, name=True):
    """Create frame with player graphics overlaid"""
    height, width = frame_array.shape[:2]
    
    # Convert frame to PIL Image
    frame_img = Image.fromarray(frame_array)
    draw = ImageDraw.Draw(frame_img)
    
    try:
        # Try to load a basic font
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
    except:
        # Fallback to default font
        font = ImageFont.load_default()
    
    for team_id in [0, 1]:
        if frame_idx in smoothed_tracks[team_id]:
            x1, y1, x2, y2 = smoothed_tracks[team_id][frame_idx]
            
            # Get bottom center of bbox
            center_x = int((x1 + x2) / 2)
            foot_y = int(y2)
            
            # Estimate ellipse size proportional to bbox size
            bbox_width = x2 - x1
            bbox_height = y2 - y1
            est_area = bbox_width * bbox_height
            base_area = 80 * 160
            scale = np.sqrt(est_area / base_area)
            
            ellipse_h = int(100 * scale)
            ellipse_w = int(ellipse_h * 0.9)
            
            # Colors (BGR to RGB conversion)
            color = (198, 40, 40) if team_id == 0 else (40, 40, 198)
            
            # Draw ellipse
            if ellipse:
                fx1 = center_x - ellipse_w // 2
                fy1 = foot_y - ellipse_h
                fx2 = center_x + ellipse_w // 2
                fy2 = foot_y
                
                # Draw ellipse outline with thickness
                for i in range(3):
                    draw.ellipse([fx1-i, fy1-i, fx2+i, fy2+i], outline=color, width=1)
            
            # Draw player name
            if name:
                label_text = dico_player[team_id]['name']
                text_position = (int(x1), max(0, int(y1) - 30))
                draw.text(text_position, label_text, fill=color, font=font)
            
            # Draw tail
            if tail:
                trajectory_buffer[team_id].append((center_x, foot_y))
                if len(trajectory_buffer[team_id]) > tail_length:
                    trajectory_buffer[team_id] = trajectory_buffer[team_id][-tail_length:]
                
                num_points = len(trajectory_buffer[team_id])
                for i, (tx, ty) in enumerate(trajectory_buffer[team_id]):
                    alpha = int(255 * (i + 1) / num_points)
                    tail_color = tuple(int(c * (alpha / 255)) for c in color)
                    
                    # Draw circle for tail point
                    circle_size = 4
                    draw.ellipse([tx-circle_size, ty-circle_size, tx+circle_size, ty+circle_size], 
                               fill=tail_color)
    
    return np.array(frame_img)


def create_video_front(input_video_path, player_xy, output_video_path, dico_player, 
                      ellipse=True, tail=True, name=True, debug=False):
    """Create video with player graphics using moviepy"""
    
    # Load the video
    video = VideoFileClip(input_video_path)
    fps = video.fps
    tail_length = int(fps * 2)
    trajectory_buffer = {0: [], 1: []}
    
    print(f"Tail length: {tail_length}")
    
    def process_frame(get_frame, t):
        """Process each frame with graphics"""
        frame_idx = int(t * fps)
        frame_array = get_frame(t)
        
        # Add graphics to frame
        processed_frame = create_frame_with_graphics(
            frame_array, frame_idx, trajectory_buffer, {0: {}, 1: {}}, 
            player_xy, tail_length, dico_player, ellipse, tail, name
        )
        
        return processed_frame
    
    # Apply the processing to the video
    processed_video = video.fl(process_frame)
    
    # Write the output video
    processed_video.write_videofile(
        output_video_path, 
        codec='libx264',
        audio_codec='aac',
        temp_audiofile='temp-audio.m4a',
        remove_temp=True
    )
    
    video.close()
    processed_video.close()
    
    print(f"Video {output_video_path} is created!")


def create_ball_trajectory_frame(frame_array, frame_idx, dico_ball, tail_buffer, tail_length, 
                                bounce_positions, speed_tail=True, ball_show=True, 
                                bounce_show=True, hit_show=True):
    """Add ball trajectory graphics to frame"""
    
    frame_img = Image.fromarray(frame_array)
    draw = ImageDraw.Draw(frame_img)
    
    # Get ball data for this frame
    ball_data = dico_ball.get(str(frame_idx), {})
    if not ball_data:
        return np.array(frame_img)
    
    x, y = ball_data.get('x_interp', ball_data.get('x')), ball_data.get('y_interp', ball_data.get('y'))
    if x is None or y is None:
        return np.array(frame_img)
    
    x, y = int(x), int(y)
    action = ball_data.get("action", "air")
    
    if ball_show:
        # Add to tail buffer
        tail_buffer.append((x, y, frame_idx))
        while tail_buffer and frame_idx - tail_buffer[0][2] > tail_length:
            tail_buffer.popleft()
        
        # Draw tail
        for j in range(1, len(tail_buffer)):
            x1, y1, f1 = tail_buffer[j - 1]
            x2, y2, f2 = tail_buffer[j]
            if None in [x1, y1, x2, y2]:
                continue
            
            # Compute speed for color
            dist = np.hypot(x2 - x1, y2 - y1)
            speed = dist / max(f2 - f1, 1)
            
            if speed_tail:
                min_speed, max_speed = 1, 50
                norm_speed = np.clip((speed - min_speed) / (max_speed - min_speed), 0, 1)
                color = (int(255 * norm_speed), int(255 * (1 - norm_speed)), 0)  # Red to Green
            else:
                color = (255, 255, 0)  # Yellow
            
            # Draw line segment
            draw.line([(x1, y1), (x2, y2)], fill=color, width=3)
        
        # Draw current ball
        if ball_data.get("visible", True):
            ball_color = (255, 200, 0)  # Orange
            ball_size = 8
            draw.ellipse([x-ball_size, y-ball_size, x+ball_size, y+ball_size], fill=ball_color)
    
    # Draw bounce marker
    if bounce_show and action == "bounce":
        bounce_positions.append((x, y))
    
    # Draw all bounces
    if bounce_show:
        for bx, by in bounce_positions:
            draw.ellipse([bx-12, by-6, bx+12, by+6], outline=(255, 255, 0), width=2)
    
    # Draw hit marker
    if hit_show and action == "hit":
        hit_color = (0, 0, 255)  # Blue
        draw.ellipse([x-20, y-20, x+20, y+20], outline=hit_color, width=2)
        draw.line([(x-10, y-10), (x+10, y+10)], fill=hit_color, width=2)
        draw.line([(x-10, y+10), (x+10, y-10)], fill=hit_color, width=2)
    
    return np.array(frame_img)


def annotate_video_with_hits_overlay(
    video_path, player_info, player_xy, dico_ball, dico_shots,
    ellipse, tail, name, ball_show, player_annot_show, speed_tail,
    bounce_show, hit_show, output_path="annotated_hits_overlay.mp4",
    tail_duration=1.5):
    """Annotate video with ball trajectory, hits, and bounces overlay using moviepy"""
    
    video = VideoFileClip(video_path)
    fps = video.fps
    tail_length = int(tail_duration * fps)
    
    # Prepare hit overlay text
    hit_overlay_text = {}
    for i, res in enumerate(dico_shots):
        start = res["frame"]
        end = dico_shots[i + 1]["frame"] if i + 1 < len(dico_shots) else int(video.duration * fps)
        
        for f in range(start, end):
            hit_overlay_text[f] = f"{res['player name']}{res['type'][13:]} at {np.round(res['speed'], 0)}km/h"
    
    # Prepare ball data
    df = pd.DataFrame.from_dict(dico_ball, orient='index')
    if not df.empty:
        df.index = df.index.astype(int)
        df = df.sort_index()
        df[['x', 'y']] = df[['x', 'y']].astype('float')
        df['x_interp'] = df['x'].interpolate(limit_direction='both')
        df['y_interp'] = df['y'].interpolate(limit_direction='both')
        
        # Update dico_ball with interpolated values
        for idx, row in df.iterrows():
            if str(idx) in dico_ball:
                dico_ball[str(idx)]['x_interp'] = row['x_interp']
                dico_ball[str(idx)]['y_interp'] = row['y_interp']
    
    # Initialize buffers
    tail_buffer = deque()
    bounce_positions = []
    
    def process_frame_with_annotations(get_frame, t):
        """Process each frame with all annotations"""
        frame_idx = int(t * fps)
        frame_array = get_frame(t)
        
        # Add ball trajectory
        frame_array = create_ball_trajectory_frame(
            frame_array, frame_idx, dico_ball, tail_buffer, tail_length,
            bounce_positions, speed_tail, ball_show, bounce_show, hit_show
        )
        
        # Add text overlay
        if player_annot_show and frame_idx in hit_overlay_text:
            frame_img = Image.fromarray(frame_array)
            draw = ImageDraw.Draw(frame_img)
            
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
            except:
                font = ImageFont.load_default()
            
            text = hit_overlay_text[frame_idx]
            
            # Get text size and center it
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            text_x = (frame_array.shape[1] - text_width) // 2
            text_y = int(frame_array.shape[0] * 0.12)
            
            # Draw text with outline for better visibility
            outline_color = (0, 0, 0)
            text_color = (255, 255, 30)
            
            # Draw outline
            for adj in range(-2, 3):
                for adj2 in range(-2, 3):
                    draw.text((text_x + adj, text_y + adj2), text, fill=outline_color, font=font)
            
            # Draw main text
            draw.text((text_x, text_y), text, fill=text_color, font=font)
            
            frame_array = np.array(frame_img)
        
        return frame_array
    
    # Apply processing
    processed_video = video.fl(process_frame_with_annotations)
    
    # Write output
    processed_video.write_videofile(
        output_path,
        codec='libx264',
        audio_codec='aac',
        temp_audiofile='temp-audio.m4a',
        remove_temp=True
    )
    
    video.close()
    processed_video.close()
    
    print(f"✅ Video saved to: {output_path}")
