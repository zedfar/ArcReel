"""
Prompt utility functions

Provide conversion functionality from structured prompts to YAML format.
"""

import yaml

# Preset option definitions
STYLES = ["Photographic", "Anime", "3D Animation"]

SHOT_TYPES = [
    "Extreme Close-up",
    "Close-up",
    "Medium Close-up",
    "Medium Shot",
    "Medium Long Shot",
    "Long Shot",
    "Extreme Long Shot",
    "Over-the-shoulder",
    "Point-of-view",
]

CAMERA_MOTIONS = [
    "Static",
    "Pan Left",
    "Pan Right",
    "Tilt Up",
    "Tilt Down",
    "Zoom In",
    "Zoom Out",
    "Tracking Shot",
]


def image_prompt_to_yaml(image_prompt: dict, project_style: str) -> str:
    """
    Convert imagePrompt structure to YAML format string.

    Args:
        image_prompt: image_prompt object from segment, structure:
            {
                "scene": "scene description",
                "composition": {
                    "shot_type": "shot type",
                    "lighting": "lighting description",
                    "ambiance": "ambiance description"
                }
            }
        project_style: Project-level style setting (read from project.json)

    Returns:
        YAML format string for Gemini API call
    """
    ordered = {
        "Style": project_style,
        "Scene": image_prompt["scene"],
        "Composition": {
            "shot_type": image_prompt["composition"]["shot_type"],
            "lighting": image_prompt["composition"]["lighting"],
            "ambiance": image_prompt["composition"]["ambiance"],
        },
    }
    return yaml.dump(ordered, allow_unicode=True, default_flow_style=False, sort_keys=False)


def video_prompt_to_yaml(video_prompt: dict) -> str:
    """
    Convert videoPrompt structure to YAML format string.

    Args:
        video_prompt: video_prompt object from segment, structure:
            {
                "action": "action description",
                "camera_motion": "camera motion",
                "ambiance_audio": "ambiance audio description",
                "dialogue": [{"speaker": "character name", "line": "dialogue"}]
            }

    Returns:
        YAML format string for Veo API call
    """
    dialogue = [{"Speaker": d["speaker"], "Line": d["line"]} for d in video_prompt.get("dialogue", [])]

    ordered = {
        "Action": video_prompt["action"],
        "Camera_Motion": video_prompt["camera_motion"],
        "Ambiance_Audio": video_prompt.get("ambiance_audio", ""),
    }

    # Add Dialogue field only if there is dialogue
    if dialogue:
        ordered["Dialogue"] = dialogue

    return yaml.dump(ordered, allow_unicode=True, default_flow_style=False, sort_keys=False)


def is_structured_image_prompt(image_prompt) -> bool:
    """
    Check if image_prompt is in structured format.

    Args:
        image_prompt: image_prompt field value

    Returns:
        True if structured format (dict), False if old string format
    """
    return isinstance(image_prompt, dict) and "scene" in image_prompt


def is_structured_video_prompt(video_prompt) -> bool:
    """
    Check if video_prompt is in structured format.

    Args:
        video_prompt: video_prompt field value

    Returns:
        True if structured format (dict), False if old string format
    """
    return isinstance(video_prompt, dict) and "action" in video_prompt


def validate_style(style: str) -> bool:
    """Validate if style is a preset option."""
    return style in STYLES


def validate_shot_type(shot_type: str) -> bool:
    """Validate if shot type is a preset option."""
    return shot_type in SHOT_TYPES


def validate_camera_motion(camera_motion: str) -> bool:
    """Validate if camera motion is a preset option."""
    return camera_motion in CAMERA_MOTIONS
