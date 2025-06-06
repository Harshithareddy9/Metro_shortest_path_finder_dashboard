import streamlit as st
import networkx as nx
import folium
from streamlit_folium import st_folium
import io

# --------- Sample Data Setup ---------

stations = {
    "Miyapur": {"line": "Orange", "pos": (17.4840, 78.3712)},
    "JNTU": {"line": "Orange", "pos": (17.4624, 78.3802)},
    "KPHB": {"line": "Orange", "pos": (17.4580, 78.3780)},
    "Kukatpally": {"line": "Orange", "pos": (17.4495, 78.3884)},
    "Bal Nagar": {"line": "Orange", "pos": (17.4387, 78.3970)},
    "Moosapet": {"line": "Orange", "pos": (17.4259, 78.4120)},
    "Bharat Nagar": {"line": "Orange", "pos": (17.4203, 78.4284)},
    "Ameerpet": {"line": "Green", "pos": (17.4376, 78.4481)},
    "Begumpet": {"line": "Green", "pos": (17.4470, 78.4678)},
    "Secunderabad": {"line": "Green", "pos": (17.4399, 78.4983)},
    "Paradise": {"line": "Green", "pos": (17.4066, 78.4744)},
    "Charminar": {"line": "Green", "pos": (17.3616, 78.4747)},
}

edges = [
    ("Miyapur", "JNTU", 3.5, 5),
    ("JNTU", "KPHB", 2.0, 3),
    ("KPHB", "Kukatpally", 2.2, 3),
    ("Kukatpally", "Bal Nagar", 2.0, 3),
    ("Bal Nagar", "Moosapet", 3.0, 4),
    ("Moosapet", "Bharat Nagar", 2.5, 4),
    ("Bharat Nagar", "Ameerpet", 5.0, 7),
    ("Ameerpet", "Begumpet", 3.0, 4),
    ("Begumpet", "Secunderabad", 4.0, 5),
    ("Secunderabad", "Paradise", 3.0, 4),
    ("Paradise", "Charminar", 6.0, 8),
    ("Bharat Nagar", "Ameerpet", 0.5, 5),  # transfer edge
]

fare_per_km = 2.5

def create_graph():
    G = nx.Graph()
    for st, info in stations.items():
        G.add_node(st, line=info["line"], pos=info["pos"])
    for u, v, dist, time in edges:
        G.add_edge(u, v, distance=dist, time=time)
    return G

G = create_graph()

def calculate_route_info(path):
    total_distance = 0
    total_time = 0
    for i in range(len(path)-1):
        edge = G[path[i]][path[i+1]]
        total_distance += edge['distance']
        total_time += edge['time']
    fare = total_distance * fare_per_km
    return total_distance, total_time, fare

def create_map(path):
    if not path:
        return None
    latitudes = [stations[st]['pos'][0] for st in path]
    longitudes = [stations[st]['pos'][1] for st in path]
    mid_lat = sum(latitudes)/len(latitudes)
    mid_lon = sum(longitudes)/len(longitudes)
    m = folium.Map(location=[mid_lat, mid_lon], zoom_start=13)
    for st in path:
        info = stations[st]
        folium.CircleMarker(
            location=info['pos'], radius=7, color='blue', fill=True, fill_color='blue',
            popup=f"{st} ({info['line']} Line)",
            tooltip=f"{st} ({info['line']} Line)"  # <-- Tooltip added here
        ).add_to(m)
    for i in range(len(path)-1):
        loc1 = stations[path[i]]['pos']
        loc2 = stations[path[i+1]]['pos']
        folium.PolyLine(locations=[loc1, loc2], color="red", weight=5).add_to(m)
    return m

st.set_page_config(page_title="Metro Route Finder", layout="wide")

st.title("🟠 Metro Route Finder & Fare Calculator")

# High contrast toggle
high_contrast = st.sidebar.checkbox("High Contrast Mode", value=False)
if high_contrast:
    st.markdown("""
        <style>
        body { background-color: #000 !important; color: #FFF !important; }
        .stButton>button { background-color: #444 !important; color: #FFF !important; }
        </style>
        """, unsafe_allow_html=True)

station_list = list(stations.keys())
source = st.selectbox("Select Source Station", options=station_list)
destination = st.selectbox("Select Destination Station", options=station_list)

if source == destination:
    st.warning("Source and destination cannot be the same!")
    st.stop()

route_type = st.radio("Route Preference:", ["Shortest Distance", "Shortest Time"])
weight_key = 'distance' if route_type == "Shortest Distance" else 'time'

try:
    shortest_path = nx.shortest_path(G, source, destination, weight=weight_key)
except nx.NetworkXNoPath:
    st.error("No path found between the selected stations.")
    st.stop()

distance, time_min, fare = calculate_route_info(shortest_path)

st.subheader("Route Details")
st.write(f"Route: {' -> '.join(shortest_path)}")
st.write(f"Total Distance: {distance:.2f} km")
st.write(f"Estimated Travel Time: {time_min} minutes")
st.write(f"Estimated Fare: ₹{fare:.2f}")

route_map = create_map(shortest_path)
if route_map:
    st.subheader("Route Map")
    st_folium(route_map, width=700, height=450)

# Save favorites in session state
if 'favorites' not in st.session_state:
    st.session_state.favorites = []

if st.button("Save this route to favorites"):
    st.session_state.favorites.append({
        "source": source,
        "destination": destination,
        "route": shortest_path,
        "distance": distance,
        "time": time_min,
        "fare": fare,
        "preference": route_type
    })
    st.success("Route saved!")

if st.session_state.favorites:
    st.subheader("Saved Favorite Routes")
    for i, fav in enumerate(st.session_state.favorites):
        st.markdown(f"*Route {i+1}:* {fav['source']} -> {fav['destination']} ({fav['preference']})")
        if st.button(f"Show Route {i+1}", key=f"show_{i}"):
            fav_map = create_map(fav['route'])
            st_folium(fav_map, width=700, height=450)

# Export current route details
def generate_export():
    output = io.StringIO()
    output.write("Metro Route Details\n")
    output.write(f"Source: {source}\n")
    output.write(f"Destination: {destination}\n")
    output.write(f"Route Preference: {route_type}\n")
    output.write(f"Route: {' -> '.join(shortest_path)}\n")
    output.write(f"Total Distance: {distance:.2f} km\n")
    output.write(f"Estimated Travel Time: {time_min} minutes\n")
    output.write(f"Estimated Fare: ₹{fare:.2f}\n")
    return output.getvalue()

st.download_button(
    label="Download Route Details as Text",
    data=generate_export(),
    file_name="metro_route.txt",
    mime="text/plain"
)
