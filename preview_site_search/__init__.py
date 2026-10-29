from pathlib import Path
import streamlit.components.v1 as components

_component = components.declare_component(
    "tdv_assigned_site_search_20261029",
    path=str(Path(__file__).parent / "frontend"),
)


def search_assigned_site(options, selected_id="", selected_label="", query="",
                         selection_token="", key=None):
    """Render a mobile-friendly, live-filtering dropdown for assigned sites."""
    return _component(
        options=options,
        selectedId=str(selected_id or ""),
        selectedLabel=str(selected_label or ""),
        query=str(query or ""),
        selectionToken=str(selection_token or ""),
        default=None,
        key=key,
    )
