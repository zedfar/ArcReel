"""
prompt_builders_script.py - Script generation prompt builder.

1. XML tags separate context
2. Clear field descriptions and constraints
3. Optional value lists constrain output
"""


def _format_character_names(characters: dict) -> str:
    """Format character list."""
    lines = []
    for name in characters.keys():
        lines.append(f"- {name}")
    return "\n".join(lines)


def _format_clue_names(clues: dict) -> str:
    """Format clue list."""
    lines = []
    for name in clues.keys():
        lines.append(f"- {name}")
    return "\n".join(lines)


def _format_duration_constraint(supported_durations: list[int], default_duration: int | None) -> str:
    """Generate duration constraint description based on parameters."""
    durations_str = ", ".join(str(d) for d in supported_durations)
    if default_duration is not None:
        return f"Duration: select from [{durations_str}] seconds, default {default_duration} seconds"
    return f"Duration: select from [{durations_str}] seconds, decide based on content pacing"


def _format_aspect_ratio_desc(aspect_ratio: str) -> str:
    """Return composition description based on aspect ratio."""
    if aspect_ratio == "9:16":
        return "Portrait composition"
    elif aspect_ratio == "16:9":
        return "Landscape composition"
    return f"{aspect_ratio} composition"


def build_narration_prompt(
    project_overview: dict,
    style: str,
    style_description: str,
    characters: dict,
    clues: dict,
    segments_md: str,
    supported_durations: list[int] | None = None,
    default_duration: int | None = None,
    aspect_ratio: str = "9:16",
) -> str:
    """
    Build narration mode prompt.

    Args:
        project_overview: Project overview (synopsis, genre, theme, world_setting)
        style: Visual style tag
        style_description: Style description
        characters: Character dictionary (used only to extract name list)
        clues: Clue dictionary (used only to extract name list)
        segments_md: Markdown content from Step 1

    Returns:
        Built prompt string
    """
    character_names = list(characters.keys())
    clue_names = list(clues.keys())

    prompt = f"""Your task is to generate a storyboard script for short videos. Please follow the instructions carefully:

**Important: All output must be in English. Only JSON keys and enum values should use English.**

1. You will receive a story overview, visual style, character list, clue list, and segmented novel passages.

2. For each segment, generate:
   - image_prompt: Image generation prompt for the first frame (English description)
   - video_prompt: Video generation prompt for actions and sound effects (English description)

<overview>
{project_overview.get("synopsis", "")}

Genre: {project_overview.get("genre", "")}
Core Theme: {project_overview.get("theme", "")}
World Setting: {project_overview.get("world_setting", "")}
</overview>

<style>
Style: {style}
Description: {style_description}
</style>

<characters>
{_format_character_names(characters)}
</characters>

<clues>
{_format_clue_names(clues)}
</clues>

<segments>
{segments_md}
</segments>

segments is a segment division table where each row is a segment containing:
- Segment ID: Format E{{episode_number}}S{{sequence_number}}
- Novel text: Must be preserved as-is in the novel_text field
- {_format_duration_constraint(supported_durations or [4, 6, 8], default_duration)}
- Has dialogue: Used to determine whether to fill in video_prompt.dialogue
- Is segment_break: Scene transition point, set segment_break to true

3. When generating for each segment, follow these rules:

a. **novel_text**: Copy the original novel text as-is without any modification.

b. **characters_in_segment**: List character names appearing in this segment.
   - Optional values: [{", ".join(character_names)}]
   - Include only explicitly mentioned or clearly implied characters

c. **clues_in_segment**: List clue names involved in this segment.
   - Optional values: [{", ".join(clue_names)}]
   - Include only explicitly mentioned or clearly implied clues

d. **image_prompt**: Generate an object with the following fields:
   - scene: Describe the specific scene visible at this moment - character positions, postures, expressions, clothing details, and visible environmental elements and objects.
     Focus on the visible image at this moment. Describe only the specific visual elements the camera can capture.
     Ensure descriptions avoid elements outside the current frame. Exclude metaphors, similes, abstract emotional words, subjective evaluations, multi-scene transitions, and other descriptions that cannot be directly rendered.
     The image should be self-contained, not implying past events or future developments.
   - composition:
     - shot_type: Shot type (Extreme Close-up, Close-up, Medium Close-up, Medium Shot, Medium Long Shot, Long Shot, Extreme Long Shot, Over-the-shoulder, Point-of-view)
     - lighting: Describe specific light source types, directions, and color temperatures (e.g., "warm yellow morning light coming through the left window")
     - ambiance: Describe visible environmental effects (e.g., "thin mist spreading", "dust flying"), avoid abstract emotional words

e. **video_prompt**: Generate an object with the following fields:
   - action: Precisely describe the specific actions of the subject during the duration - body movements, gesture changes, expression transitions.
     Focus on a single continuous action, ensuring it can be completed within the specified duration.
     Exclude multi-scene transitions, montages, quick editing, and other effects that cannot be achieved in a single generation.
     Exclude metaphorical action descriptions (e.g., "dancing like a butterfly").
   - camera_motion: Camera movement (Static, Pan Left, Pan Right, Tilt Up, Tilt Down, Zoom In, Zoom Out, Tracking Shot)
     Select only one camera movement per segment.
   - ambiance_audio: Describe diegetic sound (diegetic sound) - environmental sounds, footsteps, object sounds.
     Only describe sounds that actually exist in the scene. Exclude music, BGM, voiceover, off-screen audio.
   - dialogue: Array of {{speaker, line}}. Fill only when the original text has quoted dialogue. speaker must come from characters_in_segment.

f. **segment_break**: If marked as "yes" in the segment table, set to true.

g. **duration_seconds**: Use the duration from the segment table.

h. **transition_to_next**: Default to "cut".

Goal: Create vivid, visually consistent storyboard prompts to guide AI image and video generation. Keep it creative, specific, and faithful to the original text.
"""
    return prompt


def build_drama_prompt(
    project_overview: dict,
    style: str,
    style_description: str,
    characters: dict,
    clues: dict,
    scenes_md: str,
    supported_durations: list[int] | None = None,
    default_duration: int | None = None,
    aspect_ratio: str = "16:9",
) -> str:
    """
    Build episode animation mode prompt.

    Args:
        project_overview: Project overview
        style: Visual style tag
        style_description: Style description
        characters: Character dictionary
        clues: Clue dictionary
        scenes_md: Markdown content from Step 1

    Returns:
        Built prompt string
    """
    character_names = list(characters.keys())
    clue_names = list(clues.keys())

    prompt = f"""Your task is to generate a storyboard script for episode animation. Please follow the instructions carefully:

**Important: All output must be in English. Only JSON keys and enum values should use English.**

1. You will receive a story overview, visual style, character list, clue list, and a list of divided scenes.

2. For each scene, generate:
   - image_prompt: Image generation prompt for the first frame (English description)
   - video_prompt: Video generation prompt for actions and sound effects (English description)

<overview>
{project_overview.get("synopsis", "")}

Genre: {project_overview.get("genre", "")}
Core Theme: {project_overview.get("theme", "")}
World Setting: {project_overview.get("world_setting", "")}
</overview>

<style>
Style: {style}
Description: {style_description}
</style>

<characters>
{_format_character_names(characters)}
</characters>

<clues>
{_format_clue_names(clues)}
</clues>

<scenes>
{scenes_md}
</scenes>

scenes is a scene division table where each row is a scene containing:
- Scene ID: Format E{{episode_number}}S{{sequence_number}}
- Scene description: Scene content after script adaptation
- {_format_duration_constraint(supported_durations or [4, 6, 8], default_duration)}
- Scene type: Plot, action, dialogue, etc.
- Is segment_break: Scene transition point, set segment_break to true

3. When generating for each scene, follow these rules:

a. **characters_in_scene**: List character names appearing in this scene.
   - Optional values: [{", ".join(character_names)}]
   - Include only explicitly mentioned or clearly implied characters

b. **clues_in_scene**: List clue names involved in this scene.
   - Optional values: [{", ".join(clue_names)}]
   - Include only explicitly mentioned or clearly implied clues

c. **image_prompt**: Generate an object with the following fields:
   - scene: Describe the specific scene visible at this moment - character positions, postures, expressions, clothing details, and visible environmental elements and objects. {_format_aspect_ratio_desc(aspect_ratio)}.
     Focus on the visible image at this moment. Describe only the specific visual elements the camera can capture.
     Ensure descriptions avoid elements outside the current frame. Exclude metaphors, similes, abstract emotional words, subjective evaluations, multi-scene transitions, and other descriptions that cannot be directly rendered.
     The image should be self-contained, not implying past events or future developments.
   - composition:
     - shot_type: Shot type (Extreme Close-up, Close-up, Medium Close-up, Medium Shot, Medium Long Shot, Long Shot, Extreme Long Shot, Over-the-shoulder, Point-of-view)
     - lighting: Describe specific light source types, directions, and color temperatures (e.g., "warm yellow morning light coming through the left window")
     - ambiance: Describe visible environmental effects (e.g., "thin mist spreading", "dust flying"), avoid abstract emotional words

d. **video_prompt**: Generate an object with the following fields:
   - action: Precisely describe the specific actions of the subject during the duration - body movements, gesture changes, expression transitions.
     Focus on a single continuous action, ensuring it can be completed within the specified duration.
     Exclude multi-scene transitions, montages, quick editing, and other effects that cannot be achieved in a single generation.
     Exclude metaphorical action descriptions (e.g., "dancing like a butterfly").
   - camera_motion: Camera movement (Static, Pan Left, Pan Right, Tilt Up, Tilt Down, Zoom In, Zoom Out, Tracking Shot)
     Select only one camera movement per segment.
   - ambiance_audio: Describe diegetic sound (diegetic sound) - environmental sounds, footsteps, object sounds.
     Only describe sounds that actually exist in the scene. Exclude music, BGM, voiceover, off-screen audio.
   - dialogue: Array of {{speaker, line}}. Include character dialogue. speaker must come from characters_in_scene.

e. **segment_break**: If marked as "yes" in the scene table, set to true.

f. **duration_seconds**: Use the duration from the scene table.

g. **scene_type**: Use the scene type from the scene table, default to "plot".

h. **transition_to_next**: Default to "cut".

Goal: Create vivid, visually consistent storyboard prompts to guide AI image and video generation. Keep it creative, specific, and suitable for {_format_aspect_ratio_desc(aspect_ratio)} animation presentation.
"""
    return prompt
