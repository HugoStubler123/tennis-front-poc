import cv2
import numpy as np
from params import ref_points
from court import draw_court_on_image





def generate_court_image(canvas_height, canvas_width, top_margin, side_margin, court_type="roland"):  # shift = margin-min_x

    if court_type == "roland":
        blank_court = np.full((canvas_height, canvas_width, 3), (155, 76, 50), dtype=np.uint8)

    # --- Ajouter la ligne du filet ---
    pt1 = (int(0 + side_margin), int(1188.5 + top_margin))
    pt2 = (int(1097 + side_margin), int(1188.5 + top_margin))
    cv2.line(blank_court, pt1, pt2, (255, 255, 255), 10)

    # --- Ajouter les marques de service ---
    pt1 = (int(548.5 + side_margin), int(0 + top_margin))
    pt2 = (int(548.5 + side_margin), int(20 + top_margin))
    cv2.line(blank_court, pt1, pt2, (255, 255, 255), 10)
    pt1 = (int(548.5 + side_margin), int(2377 + top_margin))
    pt2 = (int(548.5 + side_margin), int(2357 + top_margin))
    cv2.line(blank_court, pt1, pt2, (255, 255, 255), 10)

    # Dessiner les lignes du terrain
    ref_points_canvas = {k: (int(pt[0] + side_margin), int(pt[1] + top_margin)) for k, pt in ref_points.items()}
    court_image = draw_court_on_image(blank_court, ref_points_canvas, draw_keypoints=False, draw_lines=True, write_keypoints=False, line_width=10, line_color=(255, 255, 255), untrust_in_red=False)

    return court_image


def generate_minimap_video(video_path_input, video_path_output, frames_data, bounces_data=None, hits_data=None, players_data=True, trajectories_data=None, plot_bounces=True, plot_hits=True, plot_players=True, plot_trajectories=True, plot_players_tail=True, top_margin=650, side_margin=300, trace_duration_players=1.5, trace_duration_bounces=1, trace_duration_hits=1, trace_duration_trajectories=1, width_goal=800):
    """
    Génère une vidéo avec une minimap du terrain de tennis, affichant les rebonds de balle récents.
    Args:
        video_path_input (str): Chemin vers la vidéo d'entrée.
        video_path_output (str): Chemin pour enregistrer la vidéo de sortie.
        frames_data (dict): Dictionnaire contenant les données de chaque frame, avec "homography_matrix" pour chaque frame.
        ball_info (dict): Dictionnaire contenant les informations de la balle pour chaque frame, avec "visible", "action", "x" et "y".
        players_info (dict): Dictionnaire contenant les informations des joueurs pour chaque frame, avec les coordonnées des boîtes englobantes.
        plot_bounces (bool): Indique si les rebonds de balle doivent être tracés.
        plot_hits (bool): Indique si les coups de balle doivent être tracés.
        plot_players (bool): Indique si les joueurs doivent être tracés.
        plot_trajectories (bool): Indique si les trajectoires de balle doivent être
        top_margin (int): Marge en haut et en bas du canevas pour l'affichage.
        side_margin (int): Marge à gauche et à droite du canevas pour l'affichage.
        trace_duration_players (float): Durée en secondes pendant laquelle les traces de rebond sont affichées.
        trace_duration_ball (float): Durée en secondes pendant laquelle les traces de la balle sont affichées.
        trace_duration_hits (float): Durée en secondes pendant laquelle les traces des coups sont affichées.
        trace_duration_trajectories (float): Durée en secondes pendant laquelle les trajectoires sont affichées.
        width_goal (int): Largeur cible pour la vidéo de sortie.
    Returns:
        None: La vidéo annotée est enregistrée dans le chemin spécifié.
    """

    k_frottements = 0.0005

    yellow_ball_color = (79, 255, 223)  # Couleur de la balle jaune
    red_ball_color = (0, 0, 255)        # Couleur de la balle rouge
    hit_color = (0, 0, 255)             # Couleur des frappes


    # Vérifier si les données de balle et de joueurs sont fournies, et déterminer les options de tracé
    plot_bounces = (bounces_data is not None) and plot_bounces
    plot_hits = (hits_data is not None) and plot_hits
    plot_players = (players_data is not None) and plot_players
    plot_trajectories = (trajectories_data is not None) and plot_trajectories

    # Calculer les dimensions de la minimap
    ref_pts_arr = np.array(list(ref_points.values()))
    min_x, min_y = ref_pts_arr.min(axis=0).astype(int)
    max_x, max_y = ref_pts_arr.max(axis=0).astype(int)
    canvas_width = max_x - min_x + 1 + 2 * side_margin
    canvas_height = max_y - min_y + 1 + 2 * top_margin
    scale_factor = width_goal / canvas_width
    final_height = int(canvas_height * scale_factor)

    # Générer l'image vide du terrain de tennis
    court_image = generate_court_image(canvas_height, canvas_width, top_margin, side_margin, court_type="roland")

    # Ouvrir la vidéo d'entrée et préparer l'écriture de la vidéo de sortie
    cap = cv2.VideoCapture(video_path_input)
    fourcc = cv2.VideoWriter_fourcc(*'avc1')
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    writer = cv2.VideoWriter(video_path_output, fourcc, fps, (width_goal, final_height))

    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # Durée des traces en frames
    trace_duration_players_frames = int(trace_duration_players * fps)
    trace_duration_bounces_frames = int(trace_duration_bounces * fps)
    trace_duration_hits_frames = int(trace_duration_hits * fps)
    trace_duration_trajectories_frames = int(trace_duration_trajectories * fps)
    
    # Lire la vidéo et traiter chaque frame pour y afficher les informations
    for frame_idx in range(frame_count):
        ret, _ = cap.read()
        if not ret:
            break

        frame_data = frames_data.get(str(frame_idx))
        img_out = court_image.copy()

        if frame_data is not None:

            # Joueurs
            if plot_players:
                for player_id, player_data in players_data.items():
                    color = (40, 40, 198) if player_id == '0' else (198, 40, 40)
                    #color = (0, 255, 0) if player_id == '0' else (255, 0, 0)
                    # Joueur
                    if str(frame_idx) in player_data:
                        x = player_data[str(frame_idx)]['x'] + side_margin
                        y = player_data[str(frame_idx)]['y'] + top_margin
                        cv2.circle(img_out, (x, y), 50, color, 10)
                        cv2.circle(img_out, (x, y), 10, color, -1)

                    # Tail du joueur
                    if plot_players_tail:
                        for frame_id_trace, player_data_trace in player_data.items():
                            if frame_idx > int(frame_id_trace):
                                if int(frame_id_trace) >= frame_idx - trace_duration_players_frames:
                                    x = player_data_trace['x'] + side_margin
                                    y = player_data_trace['y'] + top_margin
                                    cv2.circle(img_out, (x, y), 10, color, -1)
                            else:
                                break


            # Trajectoires
            if plot_trajectories:
                for start, end, frame_start, frame_end in trajectories_data:
                    # Trajectoire en cours
                    if frame_start <= frame_idx <= frame_end:
                        t = frame_idx - frame_start
                        T = frame_end - frame_start
                        distance = np.linalg.norm(np.array(end) - np.array(start))
                        temp_distance = (1/k_frottements) * np.log(1 + (t/T)*(np.exp(k_frottements*distance)-1))
                        temp_end = np.array(start) + (temp_distance / distance) * (np.array(end) - np.array(start))
                        start = (int(start[0] + side_margin), int(start[1] + top_margin))
                        temp_end = (int(temp_end[0] + side_margin), int(temp_end[1] + top_margin))
                        cv2.line(img_out, start, temp_end, yellow_ball_color, 5)
                    
                    # Traces
                    elif frame_idx <= frame_end + trace_duration_trajectories_frames and frame_idx > frame_start:
                        alpha = 1 - ((frame_idx - frame_end) / trace_duration_trajectories_frames)**3
                        start = (int(start[0] + side_margin), int(start[1] + top_margin))
                        end = (int(end[0] + side_margin), int(end[1] + top_margin))
                        overlay = img_out.copy()
                        cv2.line(overlay, start, end, (255, 255, 255), 5)
                        cv2.addWeighted(overlay, alpha, img_out, 1 - alpha, 0, img_out)


            # Rebonds
            if plot_bounces:
                for frame_idx_bounce, bounce_data in bounces_data.items():
                    age = frame_idx - int(frame_idx_bounce)
                    if age >= 0:
                        # Dessiner un disque avec transparence décroissante, et une couleur qui passe du rouge au jaune
                        alpha = max(1 - (age / trace_duration_bounces_frames)**3, 0)
                        color = tuple([
                            int((1-alpha) * yellow_ball_color[c] + alpha * red_ball_color[c])
                            for c in range(3)
                        ])
                        x_canvas = bounce_data[0] + side_margin
                        y_canvas = bounce_data[1] + top_margin
                        cv2.circle(img_out, (x_canvas, y_canvas), 15, color, -1)


            # Frappes
            if plot_hits:
                for frame_idx_hit, hit_data in hits_data.items():
                    age = frame_idx - int(frame_idx_hit)
                    if 0 <= age <= trace_duration_hits_frames:
                        # Dessiner une croix (X) avec transparence décroissante
                        alpha = 1 - (age / trace_duration_hits_frames)**3
                        overlay = img_out.copy()
                        size = 20       # longueur de la croix
                        thickness = 8   # épaisseur de la croix
                        x_canvas = hit_data['x'] + side_margin
                        y_canvas = hit_data['y'] + top_margin
                        cv2.line(overlay, (x_canvas - size, y_canvas - size), (x_canvas + size, y_canvas + size), hit_color, thickness)
                        cv2.line(overlay, (x_canvas - size, y_canvas + size), (x_canvas + size, y_canvas - size), hit_color, thickness)
                        cv2.addWeighted(overlay, alpha, img_out, 1 - alpha, 0, img_out)


        # Redimensionner l'image de sortie pour correspondre à la largeur cible, et écrire dans la vidéo
        resized_img = cv2.resize(img_out, (width_goal, final_height))
        writer.write(resized_img)
    
    cap.release()
    writer.release()


# --- Cell 2: robust generate_minimap_video (AVI -> H.264 MP4) ---
import os, math, subprocess
from pathlib import Path
import cv2
import numpy as np

def _ensure_parent_dir(p: Path):
    p.parent.mkdir(parents=True, exist_ok=True)

def _ffmpeg_to_h264(src_path: Path, dst_path: Path) -> None:
    cmd = [
        "ffmpeg", "-y",
        "-i", str(src_path),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        str(dst_path),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def generate_minimap_video(
    video_path_input,
    video_path_output,
    frames_data,
    bounces_data=None,
    hits_data=None,
    players_data=True,
    trajectories_data=None,
    plot_bounces=True,
    plot_hits=True,
    plot_players=True,
    plot_trajectories=True,
    plot_players_tail=True,
    top_margin=650,
    side_margin=300,
    trace_duration_players=1.5,
    trace_duration_bounces=1,
    trace_duration_hits=1,
    trace_duration_trajectories=1,
    width_goal=800,
):
    """
    Writes temp AVI (MJPG), then ffmpeg → H.264 yuv420p MP4.
    More resilient to codec support differences in Cloud Run.
    """

    # ---- 0) Resolve / ensure output dirs
    video_path_output = Path(video_path_output)
    _ensure_parent_dir(video_path_output)
    tmp_avi = video_path_output.with_suffix(".avi")

    # ---- 1) Flags
    plot_bounces = (bounces_data is not None) and plot_bounces
    plot_hits = (hits_data is not None) and plot_hits
    plot_players = (players_data is not None) and plot_players
    plot_trajectories = (trajectories_data is not None) and plot_trajectories

    # ---- 2) Dimensions from ref_points (assumed global)
    ref_pts_arr = np.array(list(ref_points.values()))  # expects ref_points to exist globally
    min_x, min_y = ref_pts_arr.min(axis=0).astype(int)
    max_x, max_y = ref_pts_arr.max(axis=0).astype(int)
    canvas_width  = max_x - min_x + 1 + 2 * side_margin
    canvas_height = max_y - min_y + 1 + 2 * top_margin
    scale_factor  = width_goal / float(canvas_width)
    final_height  = int(round(canvas_height * scale_factor))

    # ---- 3) Base court image (assumes your function exists)
    court_image = generate_court_image(canvas_height, canvas_width, top_margin, side_margin, court_type="roland")

    # ---- 4) Input video + FPS fallback
    cap = cv2.VideoCapture(str(video_path_input))
    if not cap.isOpened():
        raise FileNotFoundError(f"Cannot open input video: {video_path_input}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    if not fps or math.isnan(fps) or fps <= 0:
        fps = 25.0  # sane default in Cloud Run

    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if frame_count <= 0:
        # Fall back to iterating until read() fails
        frame_count = 10**9

    # ---- 5) OpenCV writer (MJPG AVI)
    mjpg = cv2.VideoWriter_fourcc(*"MJPG")
    writer = cv2.VideoWriter(str(tmp_avi), mjpg, float(fps), (width_goal, final_height), True)
    if not writer.isOpened():
        cap.release()
        raise RuntimeError("OpenCV VideoWriter failed to open with MJPG. "
                           "Check /tmp is writable in Cloud Run.")

    # Durations in frames
    trace_players_f = int(trace_duration_players * fps)
    trace_bounces_f = int(trace_duration_bounces * fps)
    trace_hits_f    = int(trace_duration_hits * fps)
    trace_traj_f    = int(trace_duration_trajectories * fps)

    # Colors
    yellow_ball_color = (79, 255, 223)
    red_ball_color    = (0, 0, 255)
    hit_color         = (0, 0, 255)

    k_frottements = 0.0005

    # ---- 6) Main loop
    frame_idx = 0
    while frame_idx < frame_count:
        ret, _ = cap.read()
        if not ret:
            break

        frame_key = str(frame_idx)
        frame_data = frames_data.get(frame_key)
        img_out = court_image.copy()

        if frame_data is not None:
            # Players
            if plot_players:
                for player_id, player_data in players_data.items():
                    color = (40, 40, 198) if player_id == '0' else (198, 40, 40)
                    if frame_key in player_data:
                        x = player_data[frame_key]['x'] + side_margin
                        y = player_data[frame_key]['y'] + top_margin
                        cv2.circle(img_out, (x, y), 50, color, 10)
                        cv2.circle(img_out, (x, y), 10, color, -1)

                    if plot_players_tail:
                        # Tail points in the last 'trace_players_f' frames
                        lower = max(0, frame_idx - trace_players_f)
                        for f_str, pdata in player_data.items():
                            f_int = int(f_str)
                            if lower <= f_int < frame_idx:
                                x = pdata['x'] + side_margin
                                y = pdata['y'] + top_margin
                                cv2.circle(img_out, (x, y), 10, color, -1)

            # Trajectories
            if plot_trajectories:
                for start, end, frame_start, frame_end in trajectories_data:
                    if frame_start <= frame_idx <= frame_end:
                        t = frame_idx - frame_start
                        T = max(1, frame_end - frame_start)
                        distance = np.linalg.norm(np.array(end) - np.array(start))
                        if distance > 0:
                            temp_distance = (1/k_frottements) * np.log(1 + (t/T)*(np.exp(k_frottements*distance)-1))
                            temp_end = np.array(start) + (temp_distance / distance) * (np.array(end) - np.array(start))
                            start_pt = (int(start[0] + side_margin), int(start[1] + top_margin))
                            temp_pt  = (int(temp_end[0] + side_margin), int(temp_end[1] + top_margin))
                            cv2.line(img_out, start_pt, temp_pt, yellow_ball_color, 5)
                    elif frame_start < frame_idx <= frame_end + trace_traj_f:
                        alpha = 1 - ((frame_idx - frame_end) / float(trace_traj_f))**3
                        start_pt = (int(start[0] + side_margin), int(start[1] + top_margin))
                        end_pt   = (int(end[0] + side_margin),   int(end[1] + top_margin))
                        overlay = img_out.copy()
                        cv2.line(overlay, start_pt, end_pt, (255, 255, 255), 5)
                        cv2.addWeighted(overlay, alpha, img_out, 1 - alpha, 0, img_out)

            # Bounces
            if plot_bounces:
                for f_bounce_str, bounce in bounces_data.items():
                    age = frame_idx - int(f_bounce_str)
                    if age >= 0:
                        alpha = max(1 - (age / float(trace_bounces_f))**3, 0)
                        color = tuple(int((1-alpha)*yellow_ball_color[c] + alpha*red_ball_color[c]) for c in range(3))
                        x_canvas = bounce[0] + side_margin
                        y_canvas = bounce[1] + top_margin
                        cv2.circle(img_out, (x_canvas, y_canvas), 15, color, -1)

            # Hits
            if plot_hits:
                for f_hit_str, hit in hits_data.items():
                    age = frame_idx - int(f_hit_str)
                    if 0 <= age <= trace_hits_f:
                        alpha = 1 - (age / float(trace_hits_f))**3
                        overlay = img_out.copy()
                        size = 20
                        thickness = 8
                        x_canvas = hit['x'] + side_margin
                        y_canvas = hit['y'] + top_margin
                        cv2.line(overlay, (x_canvas - size, y_canvas - size), (x_canvas + size, y_canvas + size), hit_color, thickness)
                        cv2.line(overlay, (x_canvas - size, y_canvas + size), (x_canvas + size, y_canvas - size), hit_color, thickness)
                        cv2.addWeighted(overlay, alpha, img_out, 1 - alpha, 0, img_out)

        # Resize to target width/height and write
        resized_img = cv2.resize(img_out, (width_goal, final_height))
        writer.write(resized_img)
        frame_idx += 1

    cap.release()
    writer.release()

    # Transcode to H.264 (browser-friendly & Cloud-Run-readable)
    _ffmpeg_to_h264(tmp_avi, video_path_output)

    # Clean temp
    try:
        tmp_avi.unlink(missing_ok=True)
    except Exception:
        pass

    print(f"✅ Saved minimap video (H.264): {video_path_output}")
    return str(video_path_output)
