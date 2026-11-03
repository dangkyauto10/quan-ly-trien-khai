from pathlib import Path
import streamlit.components.v1 as components

_component = components.declare_component(
    "tdv_report_camera_capture_v1",
    path=str(Path(__file__).parent / "frontend"),
)


def capture_report_photos(max_photos=10, initial_photos=None, key=None):
    """Capture multiple mobile photos in one compact camera area."""
    safe_max = max(0, min(10, int(max_photos)))
    photos = initial_photos if isinstance(initial_photos, list) else []
    return _component(
        maxPhotos=safe_max,
        initialPhotos=photos,
        default={"photos": photos},
        key=key,
    )
