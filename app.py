import streamlit as st
from pathlib import Path
from main import dico_bounces, dico_hits, dico_players, dico_trajectories, dico_ball, dico_shots, player_info, smoothed_tracks, frames_data
from front_video import create_video_front, annotate_video_with_hits_overlay
from graphs import create_analysis_video
from minimap import generate_minimap_video
from table import create_cumulative_stats_video
from video_assemblage import assemble_four_videos


VIDEO_DIR = Path("video")
VIDEO_DIR.mkdir(exist_ok=True)

video_input_path = VIDEO_DIR / "input_video.mp4"

video_output_path = VIDEO_DIR / "front_overlay.mp4"
video_intermediate_path = VIDEO_DIR / "annotated_hits_overlay.mp4"
analysis_output_path = VIDEO_DIR / "my_dynamic_video.mp4"
minimap_output_path = VIDEO_DIR / "minimap_overlay.mp4"
table_output_path = VIDEO_DIR / "cumulative_table.mp4"
final_output_path = VIDEO_DIR / "final_output.mp4"


# ------------------
# PAGE CONFIG
# ------------------
st.set_page_config(page_title="🎾 Tennis Video Overlay", layout="wide")

# ------------------
# CUSTOM CSS
# ------------------
custom_css = """
<style>
body {
    background-color: #f0fff0;
    color: #002147;
    font-family: 'Helvetica', sans-serif;
}
h1, h2, h3 {
    color: #006400;
    font-weight: bold;
}
.stButton>button {
    background-color: #ffd700 !important;
    color: black !important;
    border-radius: 10px;
    font-weight: bold;
}
.stCheckbox>label {
    font-size: 16px;
    font-weight: 500;
    color: #003366;
}
.sidebar .sidebar-content {
    background-color: #e6ffe6;
}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# ------------------
# LOAD FILES
# ------------------

# ------------------
# INIT SESSION STATE
# ------------------
defaults = {
    "show_ball_traj": True,
    "color_by_speed": False,
    "show_player_traj": True,
    "player_tail": True,
    "ellipse": True,
    "name": True,
    "show_bounce": True,
    "show_hit": True,
    "show_shot_data": True,
    "show_minimap": True,
    "minimap_player_tail": True,
    "show_analytics": True,
    "graphics": ["Speed", "Distance", "Depth"],
    "table": ["speed", "shot speed", "shot stats"],
    "analysis_created": False
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# ------------------
# SIDEBAR CONTROLS
# ------------------
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/3/3e/Tennis_ball_2.png", width=100)
st.sidebar.title("🎾 Overlay Options")

st.sidebar.subheader("A. Video Overlays")
st.session_state["show_ball_traj"] = st.sidebar.checkbox("🎾 Ball Trajectory", value=st.session_state["show_ball_traj"])
st.session_state["color_by_speed"] = st.sidebar.checkbox("Color by Speed", value=st.session_state["color_by_speed"]) if st.session_state["show_ball_traj"] else False

st.session_state["show_player_traj"] = st.sidebar.checkbox("🏃 Player Trajectories", value=st.session_state["show_player_traj"])
if st.session_state["show_player_traj"]:
    st.session_state["player_tail"] = st.sidebar.checkbox("Show Player Tails", value=st.session_state["player_tail"])
    st.session_state["ellipse"] = st.sidebar.checkbox("Show Ellipse", value=st.session_state["ellipse"])
    st.session_state["name"] = st.sidebar.checkbox("Show Name", value=st.session_state["name"])

st.session_state["show_bounce"] = st.sidebar.checkbox("🟢 Show Bounce Points", value=st.session_state["show_bounce"])
st.session_state["show_hit"] = st.sidebar.checkbox("🎯 Show Hit Points", value=st.session_state["show_hit"])
st.session_state["show_shot_data"] = st.sidebar.checkbox("📈 Show Shot Data", value=st.session_state["show_shot_data"])

st.sidebar.subheader("B. Minimap")
st.session_state["show_minimap"] = st.sidebar.checkbox("🗺️ Show Minimap", value=st.session_state["show_minimap"])
if st.session_state["show_minimap"]:
    st.session_state["minimap_player_tail"] = st.sidebar.checkbox("Minimap Player Tails", value=st.session_state["minimap_player_tail"])

st.sidebar.subheader("C. Analytics")
st.session_state["show_analytics"] = st.sidebar.checkbox("📊 Show Analytics", value=st.session_state["show_analytics"])

# ------------------
# MAIN AREA
# ------------------
st.title("🏟️ Tennis AI Analyser")

# VIDEO PREVIEW
st.markdown("### 🎥 Original Match Video")
#if video_input_path.exists():
#    st.video(str(video_input_path))
#else:
#    st.error("Video not found. Please check path: `assets/video.mp4`")


# ------------------
# STORE PARAMETERS
# ------------------
parameters_dico = {
    "ball_trajectory": st.session_state["show_ball_traj"],
    "color_by_speed": st.session_state["color_by_speed"],
    "player_trajectory": st.session_state["show_player_traj"],
    "player_tail": st.session_state["player_tail"],
    "ellipse": st.session_state["ellipse"],
    "name": st.session_state["name"],
    "bounce": st.session_state["show_bounce"],
    "hit": st.session_state["show_hit"],
    "shot_data": st.session_state["show_shot_data"],
    "minimap": st.session_state["show_minimap"],
    "minimap_player_tail": st.session_state["minimap_player_tail"],
    "analytics": st.session_state["show_analytics"],
    "graphics": st.session_state["graphics"],
    "table": st.session_state["table"],
    "analysis_created": st.session_state["analysis_created"]
}


# ANALYTICS OPTIONS
if st.session_state["show_analytics"]:
    st.markdown("## 📊 Analytics Settings")
    st.session_state["graphics"] = st.multiselect("Choose Graphics to Display", ["Speed", "Distance", "Depth"], default=st.session_state["graphics"])
    st.session_state["table"] = st.multiselect("Choose Tables to Display", ["speed", "shot speed", "shot stats"], default=st.session_state["table"])

if st.button("🧠 Create Analysis"):
        # Placeholder for analysis logic
        create_video_front(video_input_path, smoothed_tracks, video_intermediate_path, 
                           player_info, ellipse=parameters_dico['ellipse'], 
                           tail=parameters_dico['player_tail'], 
                           name=parameters_dico['name'], debug=False)
        
        annotate_video_with_hits_overlay(
            video_intermediate_path,
            player_info,
            smoothed_tracks,
            dico_ball,
            dico_shots,
            ellipse=True,
            tail=False,
            name=True,
            ball_show=parameters_dico['ball_trajectory'],
            player_annot_show=parameters_dico['shot_data'],
            speed_tail=parameters_dico['color_by_speed'],
            bounce_show=parameters_dico['bounce'],
            hit_show =parameters_dico['hit'],
            output_path=video_output_path,
            tail_duration=1.5)
        st.success("Video with overlays created!")
        
         # Conditional outputs
        
        
       
        if parameters_dico['minimap']:
            generate_minimap_video(video_input_path, minimap_output_path, frames_data, 
                                   bounces_data=dico_bounces, hits_data=dico_hits, 
                                   players_data=dico_players, trajectories_data=dico_trajectories, 
                                   plot_players_tail=True, width_goal=500)
            st.success("Minimap video created!")
        else :
            minimap_output_path = None

        if parameters_dico['analytics']:
            create_analysis_video(
                dico=dico_players,
                player_info=player_info,
                keys_to_plot=parameters_dico["graphics"],
                output_path=analysis_output_path,
                smooth=True
            )
            st.success("Graphs created!")
            create_cumulative_stats_video(
                dico_players=dico_players,
                dico_shots=dico_shots,
                player_info=player_info,
                output_path=table_output_path,
                params=parameters_dico["table"],
                fps=25,
                fade_duration=5
            )
            st.success("Table stats video created!")
        else:
            analysis_output_path = None
            table_output_path = None
        
        # ---------------------------------------------------------------------------
        # Exemple d’usage -----------------------------------------------------------
        assemble_four_videos(
            video1_path = str(video_output_path),  # 1920×1080
            video2_path = str(minimap_output_path) if minimap_output_path and minimap_output_path.exists() else None,  # 500×1080
            video3_path = str(analysis_output_path) if analysis_output_path and Path(analysis_output_path).exists() else None,  # largeur param.
            video4_path = str(table_output_path) if table_output_path and Path(table_output_path).exists() else None,  # auto
            output_path = str(final_output_path),
            bottom_h = 850,
            bottom_w_left = 1000,
        )


        
        
        st.success("Analysis created!")
        st.session_state["analysis_created"] = True

# DOWNLOAD + VIDEO
if st.session_state["analysis_created"]:
    st.markdown("### ⬇️ Download")
    #st.download_button("🎾 Download Final Video", data=open(final_output_path, "rb"), file_name="final_output.mp4")

    if final_output_path.exists():
        with open(final_output_path, "rb") as f:
            video_bytes = f.read()

        st.download_button("🎾 Download Final Video", data=video_bytes, file_name="final_output.mp4")
        st.markdown("### 🎬 Final Video Preview")
        st.video(str(final_output_path))
    else:
        st.warning("⚠️ Processed video not found. Please ensure the pipeline ran correctly.")

