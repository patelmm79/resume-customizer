"""Markdown rendering utilities."""


def render_markdown_with_html(streamlit_obj, content: str, **kwargs):
    """
    Render markdown content in Streamlit.

    Streamlit natively supports markdown formatting including:
    - ***text*** for bold-italic
    - **text** for bold
    - *text* for italic

    Args:
        streamlit_obj: st object (Streamlit context)
        content: Markdown content to render
        **kwargs: Additional arguments to pass to st.markdown

    Example:
        render_markdown_with_html(st, "This is ***bold italic*** text")
    """
    streamlit_obj.markdown(content, **kwargs)
