from pathlib import Path
import streamlit.components.v1 as components

_component = components.declare_component(
    "tdv_assigned_site_search",
    path=str(Path(__file__).parent / "frontend"),
)


def search_assigned_site(options, selected_id="", key=None):
    """Render a mobile-friendly, live-filtering dropdown for assigned sites."""
    return _component(
        options=options,
        selectedId=str(selected_id or ""),
        default=None,
        key=key,
    )
