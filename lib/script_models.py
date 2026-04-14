"""
script_models.py - Script data models

Define script data structures using Pydantic for:
1. Gemini API response_schema (Structured Outputs)
2. Output validation
"""

from typing import Literal

from pydantic import BaseModel, Field

# ============ Enumeration type definitions ============

ShotType = Literal[
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

CameraMotion = Literal[
    "Static",
    "Pan Left",
    "Pan Right",
    "Tilt Up",
    "Tilt Down",
    "Zoom In",
    "Zoom Out",
    "Tracking Shot",
]


class Dialogue(BaseModel):
    """Dialogue entry"""

    speaker: str = Field(description="Speaker name")
    line: str = Field(description="Dialogue content")


class Composition(BaseModel):
    """Composition information"""

    shot_type: ShotType = Field(description="Shot type")
    lighting: str = Field(description="Lighting description, including light source, direction, and ambiance")
    ambiance: str = Field(description="Overall ambiance, matching the emotional tone")


class ImagePrompt(BaseModel):
    """Storyboard image generation prompt"""

    scene: str = Field(description="Scene description: character position, expression, action, environmental details")
    composition: Composition = Field(description="Composition information")


class VideoPrompt(BaseModel):
    """Video generation prompt"""

    action: str = Field(description="Action description: specific action of characters in this segment")
    camera_motion: CameraMotion = Field(description="Camera motion")
    ambiance_audio: str = Field(description="Ambient sound: only describe sounds within the scene, no BGM")
    dialogue: list[Dialogue] = Field(default_factory=list, description="Dialogue list, fill only when original text has quoted dialogue")


class GeneratedAssets(BaseModel):
    """Generated resource status (initialized empty)"""

    storyboard_image: str | None = Field(default=None, description="Storyboard image path")
    video_clip: str | None = Field(default=None, description="Video clip path")
    video_uri: str | None = Field(default=None, description="Video URI")
    status: Literal["pending", "storyboard_ready", "completed"] = Field(default="pending", description="Generation status")


# ============ Narration mode ============


class NarrationSegment(BaseModel):
    """Narration mode segment"""

    segment_id: str = Field(description="Segment ID, format E{episode}S{index} or E{episode}S{index}_{sub-index}")
    episode: int = Field(description="Belonging episode")
    duration_seconds: int = Field(ge=1, le=60, description="Segment duration (seconds)")
    segment_break: bool = Field(default=False, description="Whether it is a scene transition point")
    novel_text: str = Field(description="Original novel text (must be preserved as-is for later voice-over)")
    characters_in_segment: list[str] = Field(description="List of character names appearing in segment")
    clues_in_segment: list[str] = Field(default_factory=list, description="List of clue names appearing in segment")
    image_prompt: ImagePrompt = Field(description="Storyboard image generation prompt")
    video_prompt: VideoPrompt = Field(description="Video generation prompt")
    transition_to_next: Literal["cut", "fade", "dissolve"] = Field(default="cut", description="Transition type")
    note: str | None = Field(default=None, description="User notes (not involved in generation)")
    generated_assets: GeneratedAssets = Field(default_factory=GeneratedAssets, description="Generated resource status")


class NovelInfo(BaseModel):
    """Novel source information"""

    title: str = Field(description="Novel Title")
    chapter: str = Field(description="Chapter Name")


class NarrationEpisodeScript(BaseModel):
    """Narration Pattern Episode Script"""

    episode: int = Field(description="Episode Number")
    title: str = Field(description="Episode Title")
    content_mode: Literal["narration"] = Field(default="narration", description="contentpattern")
    duration_seconds: int = Field(default=0, description="Total Duration (seconds)")
    summary: str = Field(description="Episode Summary")
    novel: NovelInfo = Field(description="Novel Source Information")
    segments: list[NarrationSegment] = Field(description="Segment List")


# ============ Episode Animation Pattern (Drama) ============


class DramaScene(BaseModel):
    """Scene of Episode Animation Pattern"""

    scene_id: str = Field(description="Scene ID, format E{episode}S{number} or E{episode}S{number}_{subscript}")
    duration_seconds: int = Field(default=8, ge=1, le=60, description="Scene Duration (seconds)")
    segment_break: bool = Field(default=False, description="Whether it is a scene transition point")
    scene_type: str = Field(default="drama", description="Scene Type")
    characters_in_scene: list[str] = Field(description="Character Name List")
    clues_in_scene: list[str] = Field(default_factory=list, description="Clue Name List")
    image_prompt: ImagePrompt = Field(description="Storyboard Image Generation Prompt")
    video_prompt: VideoPrompt = Field(description="Video Generation Prompt")
    transition_to_next: Literal["cut", "fade", "dissolve"] = Field(default="cut", description="Transition Typee")
    note: str | None = Field(default=None, description="User Notes (not involved in generation)")
    generated_assets: GeneratedAssets = Field(default_factory=GeneratedAssets, description="generateresourcestatus")


class DramaEpisodeScript(BaseModel):
    """Episode Animation Pattern Episode Script"""

    episode: int = Field(description="Episode Number")
    title: str = Field(description="Episode Title")
    content_mode: Literal["drama"] = Field(default="drama", description="contentpattern")
    duration_seconds: int = Field(default=0, description="Total Duration (seconds)")
    summary: str = Field(description="Episode Summary")
    novel: NovelInfo = Field(description="Novel Source Information")
    scenes: list[DramaScene] = Field(description="Scene List")
