"""
Unified image generation prompt builder functions.

All prompt templates are centrally managed in this file to ensure WebUI and skills use the same logic.

Module responsibilities:
- Character design image prompt building
- Clue design image prompt building (prop/location types)
- Storyboard image prompt suffix

Used by:
- webui/server/routers/generate.py
- .claude/skills/generate-characters/scripts/generate_character.py
- .claude/skills/generate-clues/scripts/generate_clue.py
"""


def build_character_prompt(name: str, description: str, style: str = "", style_description: str = "") -> str:
    """
    Build character design image prompt.

    Follow nano-banana best practices: use narrative paragraph descriptions, not keyword lists.

    Args:
        name: Character name
        description: Character appearance description (should be narrative paragraph)
        style: Project style
        style_description: Style description analyzed by AI

    Returns:
        Complete prompt string
    """
    style_part = f", {style}" if style else ""

    # Build style prefix
    style_prefix = ""
    if style_description:
        style_prefix = f"Visual style: {style_description}\n\n"

    return f"""{style_prefix}Character design reference image{style_part}.

Full-body standing illustration of "{name}".

{description}

Composition requirements: Single character full-body image, natural posture, facing the camera.
Background: Clean light gray, no decorative elements.
Lighting: Soft and even studio lighting, no strong shadows.
Image quality: High definition, clear details, accurate colors."""


def build_clue_prompt(
    name: str, description: str, clue_type: str = "prop", style: str = "", style_description: str = ""
) -> str:
    """
    Build clue design image prompt.

    Select the corresponding template based on clue type.

    Args:
        name: Clue name
        description: Clue description
        clue_type: Clue type ("prop" for props or "location" for environment)
        style: Project style
        style_description: Style description analyzed by AI

    Returns:
        Complete prompt string
    """
    if clue_type == "location":
        return build_location_prompt(name, description, style, style_description)
    else:
        return build_prop_prompt(name, description, style, style_description)


def build_prop_prompt(name: str, description: str, style: str = "", style_description: str = "") -> str:
    """
    Build prop-type clue prompt.

    Use three-view composition: front full view, 45-degree side view, detail close-up.

    Args:
        name: Prop name
        description: Prop description
        style: Project style
        style_description: Style description analyzed by AI

    Returns:
        Complete prompt string
    """
    style_suffix = f", {style}" if style else ""

    # Build style prefix
    style_prefix = ""
    if style_description:
        style_prefix = f"Visual style: {style_description}\n\n"

    return f"""{style_prefix}A professional prop design reference image{style_suffix}.

Multi-angle display of the prop "{name}". {description}

Three views arranged horizontally on a clean light gray background: front full view on the left, 45-degree side view in the middle to show dimensionality, key detail close-up on the right. Soft and even studio lighting, high-definition texture, accurate colors."""


def build_location_prompt(name: str, description: str, style: str = "", style_description: str = "") -> str:
    """
    Build location-type clue prompt.

    Use 3/4 main image + bottom-right detail close-up composition.

    Args:
        name: Scene name
        description: Scene description
        style: Project style
        style_description: Style description analyzed by AI

    Returns:
        Complete prompt string
    """
    style_suffix = f", {style}" if style else ""

    # Build style prefix
    style_prefix = ""
    if style_description:
        style_prefix = f"Visual style: {style_description}\n\n"

    return f"""{style_prefix}A professional scene design reference image{style_suffix}.

Visual reference of the iconic scene "{name}". {description}

Main image occupies three-quarters of the area to show the overall appearance and atmosphere of the environment, with a small detail close-up in the bottom-right corner. Soft natural lighting."""


def build_storyboard_suffix(content_mode: str = "narration", *, aspect_ratio: str | None = None) -> str:
    """
    Get storyboard image prompt suffix.

    Prioritize using the aspect_ratio parameter; if not provided, derive from content_mode (backward compatible).
    """
    if aspect_ratio is None:
        ratio = "9:16" if content_mode == "narration" else "16:9"
    else:
        ratio = aspect_ratio
    if ratio == "9:16":
        return "Portrait composition."
    elif ratio == "16:9":
        return "Landscape composition."
    return ""


def build_style_prompt(project_data: dict) -> str:
    """
    Build style description prompt segment.

    Merge style (manually filled by user) and style_description (AI-generated).

    Args:
        project_data: project.json data

    Returns:
        Style description string for concatenating into generation prompt
    """
    parts = []

    # Base style tag
    style = project_data.get("style", "")
    if style:
        parts.append(f"Style: {style}")

    # Style description analyzed by AI
    style_description = project_data.get("style_description", "")
    if style_description:
        parts.append(f"Visual style: {style_description}")

    return "\n".join(parts)
