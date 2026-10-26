from pathlib import Path
import streamlit.components.v1 as components

_component = components.declare_component(
    "preview_drive_folder_picker",
    path=str(Path(__file__).parent / "frontend"),
)

def pick_folder(api_key, access_token, key=None):
    """Let an ADMIN explicitly authorize one Drive folder with Google Picker."""
    return _component(
        apiKey=api_key,
        accessToken=access_token,
        default=None,
        key=key,
    )
