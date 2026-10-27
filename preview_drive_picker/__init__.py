from pathlib import Path
import streamlit.components.v1 as components

_component = components.declare_component(
    "preview_drive_folder_picker_v3",
    path=str(Path(__file__).parent / "frontend"),
)

def pick_folder(api_key, access_token, app_id, key=None, open_picker=False):
    """Let an ADMIN explicitly authorize one Drive folder with Google Picker."""
    return _component(
        apiKey=api_key,
        appId=str(app_id),
        accessToken=access_token,
        openPicker=bool(open_picker),
        default=None,
        key=key,
    )
