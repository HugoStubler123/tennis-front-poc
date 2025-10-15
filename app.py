import streamlit as st
from pathlib import Path

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
VIDEO_PATH = Path("assets/video.mp4")
JSON_PATHS = {
    "ball": Path("assets/ball_data.json"),
    "players": Path("assets/player_data.json"),
    "shots": Path("assets/shots_data.json")
}

# ------------------
# INIT SESSION STATE
# ------------------
defaults = {
    "show_ball_traj": True,
    "color_by_speed": False,
    "show_player_traj": True,
    "player_tail": True,
    "show_bounce": True,
    "show_hit": True,
    "show_shot_data": False,
    "show_minimap": False,
    "minimap_player_tail": True,
    "minimap_shots": True,
    "show_analytics": False,
    "graphics": [],
    "table": [],
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
st.session_state["player_tail"] = st.sidebar.checkbox("Show Player Tails", value=st.session_state["player_tail"]) if st.session_state["show_player_traj"] else False

st.session_state["show_bounce"] = st.sidebar.checkbox("🟢 Show Bounce Points", value=st.session_state["show_bounce"])
st.session_state["show_hit"] = st.sidebar.checkbox("🎯 Show Hit Points", value=st.session_state["show_hit"])
st.session_state["show_shot_data"] = st.sidebar.checkbox("📈 Show Shot Data", value=st.session_state["show_shot_data"])

st.sidebar.subheader("B. Minimap")
st.session_state["show_minimap"] = st.sidebar.checkbox("🗺️ Show Minimap", value=st.session_state["show_minimap"])
st.session_state["minimap_player_tail"] = st.sidebar.checkbox("Minimap Player Tails", value=st.session_state["minimap_player_tail"]) if st.session_state["show_minimap"] else False
st.session_state["minimap_shots"] = st.sidebar.checkbox("Minimap Shot Trajectories", value=st.session_state["minimap_shots"]) if st.session_state["show_minimap"] else False

st.sidebar.subheader("C. Analytics")
st.session_state["show_analytics"] = st.sidebar.checkbox("📊 Show Analytics", value=st.session_state["show_analytics"])

# ------------------
# MAIN AREA
# ------------------
st.title("🏟️ Tennis Video Overlay Tool")

# VIDEO PREVIEW
st.markdown("### 🎥 Original Match Video")
if VIDEO_PATH.exists():
    st.video(str(VIDEO_PATH))
else:
    st.error("Video not found. Please check path: `assets/video.mp4`")

# ANALYTICS OPTIONS
if st.session_state["show_analytics"]:
    st.markdown("## 📊 Analytics Settings")
    st.session_state["graphics"] = st.multiselect("Choose Graphics to Display", ["speed", "distance", "depth"], default=st.session_state["graphics"])
    st.session_state["table"] = st.multiselect("Choose Tables to Display", ["speed", "shot speed", "shot stats"], default=st.session_state["table"])

    if st.button("🧠 Create Analysis"):
        # Placeholder for analysis logic
        st.success("Analysis created!")
        st.session_state["analysis_created"] = True

# DOWNLOAD BUTTON
if st.session_state["analysis_created"]:
    st.markdown("### ⬇️ Download")
    st.button("🎾 Download Processed Video")

# DEBUG / CONFIG PREVIEW
with st.expander("🔧 Debug Configuration"):
    st.json({
        "ball_trajectory": st.session_state["show_ball_traj"],
        "color_by_speed": st.session_state["color_by_speed"],
        "player_trajectory": st.session_state["show_player_traj"],
        "player_tail": st.session_state["player_tail"],
        "bounce": st.session_state["show_bounce"],
        "hit": st.session_state["show_hit"],
        "shot_data": st.session_state["show_shot_data"],
        "minimap": st.session_state["show_minimap"],
        "minimap_player_tail": st.session_state["minimap_player_tail"],
        "minimap_shots": st.session_state["minimap_shots"],
        "analytics": st.session_state["show_analytics"],
        "graphics": st.session_state["graphics"],
        "table": st.session_state["table"],
        "analysis_created": st.session_state["analysis_created"]
    })
