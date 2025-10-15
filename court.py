import cv2
from params import labels, lines



def draw_court_on_image(image, keypoints, draw_keypoints=True, draw_lines=True, write_keypoints=False, occulted_idx=None, line_width=2, line_color=(0, 255, 0), untrust_in_red=True):
    """
    Affiche l'image avec les keypoints et les lignes entre eux.
    Args:
        image (np.ndarray): Image d'origine (BGR).
        keypoints (dict): Dictionnaire {index: (x, y)} des keypoints.
        draw_keypoints (bool): Indique si les keypoints doivent être dessinés.
        draw_lines (bool): Indique si les lignes entre les keypoints doivent être dessinées.
        write_keypoints (bool): Indique si les labels des keypoints doivent être écrits.
        occulted_idx (list): Liste des indices des keypoints occultés.
        line_width (int): Épaisseur des lignes à dessiner.
        line_color (tuple): Couleur des lignes à dessiner (BGR).
        untrust_in_red (bool): Si True, les lignes entre keypoints non fiables seront dessinées en rouge.
    Returns:
        np.ndarray: Image annotée (RGB).
    """
    # Convertir l'image BGR en RGB pour matplotlib
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # Dessiner les keypoints
    if draw_keypoints:
        for i, (x, y) in keypoints.items():
            x, y = int(x), int(y)  # Conversion explicite en int
            cv2.circle(image_rgb, (x, y), 5, (255, 0, 0), -1)  # Keypoint en rouge
            if write_keypoints:
                cv2.putText(
                    image_rgb,
                    labels[i],
                    (x + 10, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1.2,  # Augmente la taille du texte
                    (255, 255, 255),
                    3,    # Épaisseur du texte plus grande
                    cv2.LINE_AA  # Antialiasing pour une meilleure visibilité
                )

    # Dessiner les lignes entre les keypoints
    if draw_lines:
        for start, end in lines:
            if start in keypoints and end in keypoints:
                pt1 = tuple(map(int, keypoints[start]))
                pt2 = tuple(map(int, keypoints[end]))
                if occulted_idx is None or (start not in occulted_idx and end not in occulted_idx) or not untrust_in_red:
                    cv2.line(image_rgb, pt1, pt2, line_color, line_width)
                else:
                    # Si l'un des points est occulté, dessiner la ligne en rouge
                    cv2.line(image_rgb, pt1, pt2, (255, 0, 0), line_width)
    return image_rgb


def draw_court_on_video(video_path_input, video_path_output, frames_data, draw_keypoints=True, draw_lines=True, write_keypoints=False, line_width=2, line_color=(0, 255, 0), untrust_in_red=True):
    """
    Annotates a video with court keypoints and lines between them.
    Args:
        video_path_input (str): Path to the input video file.
        video_path_output (str): Path to save the annotated video.
        frames_data (dict): Dictionary containing frame data with "keypoints" and "trust_idx".
        draw_keypoints (bool): Whether to draw keypoints on the video.
        draw_lines (bool): Whether to draw lines between keypoints.
        write_keypoints (bool): Whether to write keypoint labels on the video.
        line_width (int): Width of the lines to draw.
        line_color (tuple): Color of the lines to draw (BGR).
        untrust_in_red (bool): If True, lines between untrusted keypoints will be
    Returns:
        None: The annotated video is saved to the specified output path.
    """
    cap = cv2.VideoCapture(video_path_input)
    fourcc = cv2.VideoWriter_fourcc(*'avc1')
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    writer = cv2.VideoWriter(video_path_output, fourcc, fps, (width, height))

    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx in frames_data:
            data = frames_data[frame_idx]
            keypoints = data["keypoints"]
            trust_idx = data["trust_idx"]
            untrust_idx = [i for i in range(14) if i not in trust_idx]

            annotated_frame = draw_court_on_image(
                frame, keypoints, draw_keypoints, draw_lines, write_keypoints, untrust_idx, line_width=line_width, line_color=line_color, untrust_in_red=untrust_in_red
            )
            writer.write(cv2.cvtColor(annotated_frame, cv2.COLOR_RGB2BGR))

        frame_idx += 1

    cap.release()
    writer.release()
