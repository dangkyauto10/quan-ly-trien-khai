from pathlib import Path
import streamlit.components.v1 as components

_component = components.declare_component(
    "tdv_report_camera_capture_v1",
    path=str(Path(__file__).parent / "frontend"),
)


def capture_report_photos(max_photos=5, existing_count=0, initial_photos=None, key=None):
    """Capture photos up to the per-report point limit."""
    safe_max = max(0, min(5, int(max_photos)))
    safe_existing = max(0, int(existing_count))
    photos = initial_photos if isinstance(initial_photos, list) else []
    return _component(
        maxPhotos=safe_max,
        existingCount=safe_existing,
        initialPhotos=photos,
        default={"photos": photos},
        key=key,
    )
