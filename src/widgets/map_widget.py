"""
Map Widget - OpenStreetMap display with drone position marker.
Uses Folium for map generation and QtWebEngine for display.
"""

import os
import tempfile
import folium
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSizePolicy
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl


class MapWidget(QWidget):
    """
    Interactive map widget showing drone position.
    Uses OpenStreetMap via Folium + QtWebEngine.
    """
    
    # Toronto coordinates as default
    DEFAULT_LAT = 43.6532
    DEFAULT_LON = -79.3832
    DEFAULT_ZOOM = 15
    
    def __init__(self, message_broker, parent=None):
        super().__init__(parent)
        self.message_broker = message_broker
        
        self.lat = self.DEFAULT_LAT
        self.lon = self.DEFAULT_LON
        self.heading = 0.0
        self.has_position = False
        
        # Make widget expand to fill available space
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        self._setup_ui()
        self._subscribe_to_messages()
        self._create_map()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.web_view = QWebEngineView()
        self.web_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.web_view)
    
    def _subscribe_to_messages(self):
        """Subscribe to position messages."""
        self.message_broker.subscribe('GLOBAL_POSITION_INT', self._on_global_position)
    
    def _create_map(self):
        """Create initial map centered on Toronto."""
        # Create HTML directly with Leaflet for better control
        map_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        * {{ margin: 0; padding: 0; }}
        html, body {{ height: 100%; width: 100%; overflow: hidden; }}
        #map {{ height: 100%; width: 100%; }}
    </style>
</head>
<body>
    <div id="map"></div>
    <script>
        var map = L.map('map', {{
            center: [{self.lat}, {self.lon}],
            zoom: {self.DEFAULT_ZOOM},
            zoomControl: true
        }});
        
        L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
            attribution: '&copy; OpenStreetMap &copy; CARTO',
            subdomains: 'abcd',
            maxZoom: 20
        }}).addTo(map);
        
        var droneMarker = null;
        
        function createDroneIcon(heading) {{
            return L.divIcon({{
                className: 'drone-marker',
                html: '<div style="transform: rotate(' + heading + 'deg); font-size: 28px; color: #6c63ff; text-shadow: 0 0 8px rgba(108,99,255,0.8), 0 0 2px #000;">▲</div>',
                iconSize: [30, 30],
                iconAnchor: [15, 15]
            }});
        }}
        
        function updateDronePosition(lat, lon, heading) {{
            if (droneMarker) {{
                droneMarker.setLatLng([lat, lon]);
                droneMarker.setIcon(createDroneIcon(heading));
            }} else {{
                droneMarker = L.marker([lat, lon], {{
                    icon: createDroneIcon(heading)
                }}).addTo(map);
            }}
            map.panTo([lat, lon]);
        }}
        
        window.updateDronePosition = updateDronePosition;
    </script>
</body>
</html>
"""
        
        # Save to temp file and load
        self.temp_file = tempfile.NamedTemporaryFile(
            mode='w', suffix='.html', delete=False, encoding='utf-8'
        )
        self.temp_file.write(map_html)
        self.temp_file.close()
        
        self.web_view.setUrl(QUrl.fromLocalFile(self.temp_file.name))
    
    def _on_global_position(self, msg):
        """Handle GLOBAL_POSITION_INT message."""
        self.lat = msg.lat / 1e7
        self.lon = msg.lon / 1e7
        self.heading = msg.hdg / 100.0 if hasattr(msg, 'hdg') and msg.hdg != 65535 else 0
        
        # Update marker via JavaScript
        js = f"if(window.updateDronePosition) updateDronePosition({self.lat}, {self.lon}, {self.heading});"
        self.web_view.page().runJavaScript(js)
        
        self.has_position = True
    
    def cleanup(self):
        """Clean up temp files."""
        if hasattr(self, 'temp_file') and os.path.exists(self.temp_file.name):
            try:
                os.unlink(self.temp_file.name)
            except:
                pass
