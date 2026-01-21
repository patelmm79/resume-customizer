"""Markdown rendering utilities with enhanced format support."""
import re


def process_markdown_for_streamlit(content: str) -> str:
    """
    Process markdown content to fix formatting issues with Streamlit's renderer.

    Streamlit has limited support for combined formatting like ***text***.
    This function converts unsupported syntax to inline HTML for proper rendering.

    Args:
        content: Markdown content

    Returns:
        Processed markdown with HTML fallbacks
    """
    # Fix bold+italic (***text*** or ___text___)
    # Convert ***text*** to <b><i>text</i></b>
    content = re.sub(
        r'\*\*\*([^\*]+)\*\*\*',
        r'<b><i>\1</i></b>',
        content
    )

    # Convert ___text___ to <b><i>text</i></b>
    content = re.sub(
        r'___([^_]+)___',
        r'<b><i>\1</i></b>',
        content
    )

    return content


def render_markdown_with_html(streamlit_obj, content: str, **kwargs):
    """
    Render markdown content in Streamlit with HTML support for better formatting.

    Args:
        streamlit_obj: st object (Streamlit context)
        content: Markdown content to render
        **kwargs: Additional arguments to pass to st.markdown

    Example:
        render_markdown_with_html(st, "This is ***bold italic*** text")
    """
    processed = process_markdown_for_streamlit(content)
    streamlit_obj.markdown(processed, unsafe_allow_html=True, **kwargs)
