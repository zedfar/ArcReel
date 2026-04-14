"""
Project file manager.

Manage project directory structure, script read/write, and status tracking.
"""

import fcntl
import json
import logging
import os
import re
import secrets
import tempfile
import unicodedata
from collections.abc import Callable
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from lib.project_change_hints import emit_project_change_hint

logger = logging.getLogger(__name__)

PROJECT_NAME_PATTERN = re.compile(r"^[A-Za-z0-9-]+$")
PROJECT_SLUG_SANITIZER = re.compile(r"[^a-zA-Z0-9]+")

# ==================== Data models ====================


class ProjectOverview(BaseModel):
    """Project overview data model for Gemini Structured Outputs."""

    synopsis: str = Field(description="Story synopsis, 200-300 characters, summarizing the main plot")
    genre: str = Field(description="Content genre, e.g., period costume court intrigue, modern mystery, fantasy cultivation")
    theme: str = Field(description="Core theme, e.g., revenge and redemption, growth and transformation")
    world_setting: str = Field(description="Time period and world setting, 100-200 characters")


class ProjectManager:
    """Video project manager."""

    # Project subdirectory structure
    SUBDIRS = [
        "source",
        "scripts",
        "drafts",
        "characters",
        "clues",
        "storyboards",
        "videos",
        "thumbnails",
        "output",
    ]

    # Project metadata filename
    PROJECT_FILE = "project.json"

    @staticmethod
    def normalize_project_name(name: str) -> str:
        """Validate and normalize a project identifier."""
        normalized = str(name).strip()
        if not normalized:
            raise ValueError("Project identifier cannot be empty")
        if not PROJECT_NAME_PATTERN.fullmatch(normalized):
            raise ValueError("Project identifier only allows English letters, numbers, and hyphens")
        return normalized

    @staticmethod
    def _slugify_project_title(title: str) -> str:
        """Build a filesystem-safe slug prefix from the project title."""
        ascii_text = unicodedata.normalize("NFKD", str(title).strip()).encode("ascii", "ignore").decode("ascii")
        slug = PROJECT_SLUG_SANITIZER.sub("-", ascii_text).strip("-_").lower()
        return slug[:24] or "project"

    def generate_project_name(self, title: str | None = None) -> str:
        """Generate a unique internal project identifier."""
        prefix = self._slugify_project_title(title or "")
        while True:
            candidate = f"{prefix}-{secrets.token_hex(4)}"
            if not (self.projects_root / candidate).exists():
                return candidate

    @classmethod
    def from_cwd(cls) -> tuple["ProjectManager", str]:
        """Infer ProjectManager and project name from current working directory.

        Assumes cwd is in the format ``projects/{project_name}/``.
        Returns a ``(ProjectManager, project_name)`` tuple.
        """
        cwd = Path.cwd().resolve()
        project_name = cwd.name
        projects_root = cwd.parent
        pm = cls(projects_root)
        if not (projects_root / project_name / cls.PROJECT_FILE).exists():
            raise FileNotFoundError(f"Current directory is not a valid project directory: {cwd}")
        return pm, project_name

    def __init__(self, projects_root: str | None = None):
        """
        Initialize project manager.

        Args:
            projects_root: Project root directory, defaults to projects/ in current directory.
        """
        if projects_root is None:
            # Try to get from environment variables or default path
            projects_root = os.environ.get("AI_ANIME_PROJECTS", "projects")

        self.projects_root = Path(projects_root)
        self.projects_root.mkdir(parents=True, exist_ok=True)

    def list_projects(self) -> list[str]:
        """List all projects."""
        return [d.name for d in self.projects_root.iterdir() if d.is_dir() and not d.name.startswith(".")]

    def create_project(self, name: str) -> Path:
        """
        Create a new project.

        Args:
            name: Project identifier (globally unique, used for URL and filesystem)

        Returns:
            Project directory path
        """
        name = self.normalize_project_name(name)
        project_dir = self.projects_root / name

        if project_dir.exists():
            raise FileExistsError(f"Project '{name}' already exists")

        # Create all subdirectories
        for subdir in self.SUBDIRS:
            (project_dir / subdir).mkdir(parents=True, exist_ok=True)

        self.repair_claude_symlink(project_dir)

        return project_dir

    def repair_claude_symlink(self, project_dir: Path) -> dict:
        """Repair .claude and CLAUDE.md symlinks in project directory.

        For each symlink:
        - Broken (is_symlink but not exists) → delete and recreate
        - Missing (not exists and not is_symlink) → create
        - Healthy (exists) → skip

        Returns:
            {"created": int, "repaired": int, "skipped": int, "errors": int}
        """
        project_root = self.projects_root.parent
        profile_dir = project_root / "agent_runtime_profile"

        SYMLINKS = {
            ".claude": profile_dir / ".claude",
            "CLAUDE.md": profile_dir / "CLAUDE.md",
        }
        REL_TARGETS = {
            ".claude": Path("../../agent_runtime_profile/.claude"),
            "CLAUDE.md": Path("../../agent_runtime_profile/CLAUDE.md"),
        }

        stats = {"created": 0, "repaired": 0, "skipped": 0, "errors": 0}
        for name, target_source in SYMLINKS.items():
            if not target_source.exists():
                continue
            symlink_path = project_dir / name
            if symlink_path.is_symlink() and not symlink_path.exists():
                # Broken symlink
                try:
                    symlink_path.unlink()
                    symlink_path.symlink_to(REL_TARGETS[name])
                    stats["repaired"] += 1
                except OSError as e:
                    logger.warning("Cannot fix symlink %s for project %s: %s", name, project_dir.name, e)
                    stats["errors"] += 1
            elif not symlink_path.exists() and not symlink_path.is_symlink():
                # Missing
                try:
                    symlink_path.symlink_to(REL_TARGETS[name])
                    stats["created"] += 1
                except OSError as e:
                    logger.warning("Cannot create symlink %s for project %s: %s", name, project_dir.name, e)
                    stats["errors"] += 1
            else:
                stats["skipped"] += 1
        return stats

    def repair_all_symlinks(self) -> dict:
        """Scan all project directories and repair symlinks.

        Returns:
            {"created": int, "repaired": int, "skipped": int, "errors": int}
        """
        totals = {"created": 0, "repaired": 0, "skipped": 0, "errors": 0}
        if not self.projects_root.exists():
            return totals
        for project_dir in sorted(self.projects_root.iterdir()):
            if not project_dir.is_dir() or project_dir.name.startswith("."):
                continue
            try:
                result = self.repair_claude_symlink(project_dir)
                for key in ("created", "repaired", "skipped", "errors"):
                    totals[key] += result.get(key, 0)
            except Exception as e:
                logger.warning("Error while fixing symlinks for project %s: %s", project_dir.name, e)
                totals["errors"] += 1
        return totals

    def get_project_path(self, name: str) -> Path:
        """Get project path (with path traversal protection)."""
        name = self.normalize_project_name(name)
        real = os.path.realpath(self.projects_root / name)
        base = os.path.realpath(self.projects_root) + os.sep
        if not real.startswith(base):
            raise ValueError(f"Invalid project name: '{name}'")
        project_dir = Path(real)
        if not project_dir.exists():
            raise FileNotFoundError(f"Project '{name}' does not exist")
        return project_dir

    @staticmethod
    def _safe_subpath(base_dir: Path, filename: str) -> str:
        """Validate that filename concatenation does not escape base_dir, return realpath string."""
        real = os.path.realpath(base_dir / filename)
        bound = os.path.realpath(base_dir) + os.sep
        if not real.startswith(bound):
            raise ValueError(f"Invalid filename: '{filename}'")
        return real

    def get_project_status(self, name: str) -> dict[str, Any]:
        """
        Get project status.

        Returns:
            Dictionary containing completion status of each stage
        """
        project_dir = self.get_project_path(name)

        status = {
            "name": name,
            "path": str(project_dir),
            "source_files": [],
            "scripts": [],
            "characters": [],
            "clues": [],
            "storyboards": [],
            "videos": [],
            "outputs": [],
            "current_stage": "empty",
        }

        # Check directory contents
        for subdir in self.SUBDIRS:
            subdir_path = project_dir / subdir
            if subdir_path.exists():
                files = list(subdir_path.glob("*"))
                if subdir == "source":
                    status["source_files"] = [f.name for f in files if f.is_file()]
                elif subdir == "scripts":
                    status["scripts"] = [f.name for f in files if f.suffix == ".json"]
                elif subdir == "characters":
                    status["characters"] = [f.name for f in files if f.suffix in [".png", ".jpg", ".jpeg"]]
                elif subdir == "clues":
                    status["clues"] = [f.name for f in files if f.suffix in [".png", ".jpg", ".jpeg"]]
                elif subdir == "storyboards":
                    status["storyboards"] = [f.name for f in files if f.suffix in [".png", ".jpg", ".jpeg"]]
                elif subdir == "videos":
                    status["videos"] = [f.name for f in files if f.suffix in [".mp4", ".webm"]]
                elif subdir == "output":
                    status["outputs"] = [f.name for f in files if f.suffix in [".mp4", ".webm"]]

        # Determine current stage
        if status["outputs"]:
            status["current_stage"] = "completed"
        elif status["videos"]:
            status["current_stage"] = "videos_generated"
        elif status["storyboards"]:
            status["current_stage"] = "storyboards_generated"
        elif status["characters"]:
            status["current_stage"] = "characters_generated"
        elif status["scripts"]:
            status["current_stage"] = "script_created"
        elif status["source_files"]:
            status["current_stage"] = "source_ready"
        else:
            status["current_stage"] = "empty"

        return status

    # ==================== Script operations ====================

    def create_script(self, project_name: str, title: str, chapter: str) -> dict:
        """
        Create a new script template.

        Args:
            project_name: Project name
            title: Novel title
            chapter: Chapter name

        Returns:
            Script dictionary
        """
        script = {
            "novel": {"title": title, "chapter": chapter},
            "scenes": [],
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "total_scenes": 0,
                "estimated_duration_seconds": 0,
                "status": "draft",
            },
        }

        return script

    def save_script(self, project_name: str, script: dict, filename: str | None = None) -> Path:
        """
        Save script.

        Args:
            project_name: Project name
            script: Script dictionary
            filename: Optional filename, defaults to chapter name

        Returns:
            Path of saved file
        """
        project_dir = self.get_project_path(project_name)
        scripts_dir = project_dir / "scripts"

        if filename is not None and filename.startswith("scripts/"):
            filename = filename[len("scripts/") :]

        if filename is None:
            chapter = script["novel"].get("chapter", "chapter_01")
            filename = f"{chapter.replace(' ', '_')}_script.json"

        # Update metadata (compatible with old scripts: may lack metadata, or use segments for narration)
        now = datetime.now().isoformat()
        metadata = script.get("metadata")
        if not isinstance(metadata, dict):
            metadata = {}
            script["metadata"] = metadata
        metadata.setdefault("created_at", now)
        metadata.setdefault("status", "draft")
        metadata["updated_at"] = now

        scenes = script.get("scenes", [])
        if not isinstance(scenes, list):
            scenes = []
        segments = script.get("segments", [])
        if not isinstance(segments, list):
            segments = []

        content_mode = script.get("content_mode", "narration")
        if content_mode == "narration" and segments:
            items = segments
            items_type = "segments"
        elif scenes:
            items = scenes
            items_type = "scenes"
        else:
            items = segments
            items_type = "segments"

        metadata["total_scenes"] = len(items)

        # Calculate total duration: use fallback value based on selected data structure to avoid misjudgment when content_mode is missing
        default_duration = 4 if items_type == "segments" else 8
        total_duration = sum(item.get("duration_seconds", default_duration) for item in items)
        metadata["estimated_duration_seconds"] = total_duration

        # Save file (with path traversal protection)
        real = self._safe_subpath(scripts_dir, filename)
        with open(real, "w", encoding="utf-8") as f:  # noqa: PTH123
            json.dump(script, f, ensure_ascii=False, indent=2)
        output_path = Path(real)

        emit_project_change_hint(
            project_name,
            changed_paths=[f"scripts/{output_path.name}"],
        )

        # Auto-sync to project.json
        if self.project_exists(project_name) and isinstance(script.get("episode"), int):
            self.sync_episode_from_script(project_name, filename)

        return output_path

    def sync_episode_from_script(self, project_name: str, script_filename: str) -> dict:
        """
        Sync episode information from script file to project.json.

        This method must be called after Agent writes the script to ensure WebUI displays episode list correctly.

        Args:
            project_name: Project name
            script_filename: Script filename (e.g., episode_1.json)

        Returns:
            Updated project dictionary
        """
        script = self.load_script(project_name, script_filename)
        project = self.load_project(project_name)

        episode_num = script.get("episode", 1)
        episode_title = script.get("title", "")
        script_file = f"scripts/{script_filename}"

        # Find or create episode entry
        episodes = project.setdefault("episodes", [])
        episode_entry = next((ep for ep in episodes if ep["episode"] == episode_num), None)

        if episode_entry is None:
            episode_entry = {"episode": episode_num}
            episodes.append(episode_entry)

        # Sync core metadata (excluding statistical fields, which are computed at read time by StatusCalculator)
        episode_entry["title"] = episode_title
        episode_entry["script_file"] = script_file

        # Sort and save
        episodes.sort(key=lambda x: x["episode"])
        self.save_project(project_name, project)

        logger.info("Synced episode information: Episode %d - %s", episode_num, episode_title)
        return project

    def load_script(self, project_name: str, filename: str) -> dict:
        """
        Load script.

        Args:
            project_name: Project name
            filename: Script filename

        Returns:
            Script dictionary
        """
        project_dir = self.get_project_path(project_name)
        if filename.startswith("scripts/"):
            filename = filename[len("scripts/") :]
        real = self._safe_subpath(project_dir / "scripts", filename)

        if not os.path.exists(real):
            raise FileNotFoundError(f"Script file does not exist: {real}")

        with open(real, encoding="utf-8") as f:  # noqa: PTH123
            return json.load(f)

    def list_scripts(self, project_name: str) -> list[str]:
        """List all scripts in project."""
        project_dir = self.get_project_path(project_name)
        scripts_dir = project_dir / "scripts"
        return [f.name for f in scripts_dir.glob("*.json")]

    # ==================== Character management ====================

    def update_character_sheet(self, project_name: str, script_filename: str, name: str, sheet_path: str) -> dict:
        """Update character design image path."""
        script = self.load_script(project_name, script_filename)

        if name not in script["characters"]:
            raise KeyError(f"Character '{name}' does not exist")

        script["characters"][name]["character_sheet"] = sheet_path
        self.save_script(project_name, script, script_filename)
        return script

    # ==================== Data structure normalization ====================

    @staticmethod
    def create_generated_assets(content_mode: str = "narration") -> dict:
        """
        Create standard generated_assets structure.

        Args:
            content_mode: Content mode ('narration' or 'drama')

        Returns:
            Standard generated_assets dictionary
        """
        return {
            "storyboard_image": None,
            "video_clip": None,
            "video_thumbnail": None,
            "video_uri": None,
            "status": "pending",
        }

    @staticmethod
    def create_scene_template(scene_id: str, episode: int = 1, duration_seconds: int = 8) -> dict:
        """
        Create standard scene object template

        Args:
            scene_id: Scene ID(e.g., "E1S01")
            episode: Episode number
            duration_seconds: Scene duration(seconds)

        Returns:
            Standard scene dictionary
        """
        return {
            "scene_id": scene_id,
            "episode": episode,
            "title": "",
            "scene_type": "drama",
            "duration_seconds": duration_seconds,
            "segment_break": False,
            "characters_in_scene": [],
            "clues_in_scene": [],
            "visual": {
                "description": "",
                "shot_type": "medium shot",
                "camera_movement": "static",
                "lighting": "",
                "mood": "",
            },
            "action": "",
            "dialogue": {"speaker": "", "text": "", "emotion": "neutral"},
            "audio": {"dialogue": [], "narration": "", "sound_effects": []},
            "transition_to_next": "cut",
            "generated_assets": ProjectManager.create_generated_assets(),
        }

    def normalize_scene(self, scene: dict, episode: int = 1) -> dict:
        """
        Complete missing fields in a single scene

        Args:
            scene: Scene dictionary
            episode: Episode number(for completing episode field)

        Returns:
            Completed scene dictionary
        """
        template = self.create_scene_template(
            scene_id=scene.get("scene_id", "000"),
            episode=episode,
            duration_seconds=scene.get("duration_seconds", 8),
        )

        # Merge visual fields
        if "visual" not in scene:
            scene["visual"] = template["visual"]
        else:
            for key in template["visual"]:
                if key not in scene["visual"]:
                    scene["visual"][key] = template["visual"][key]

        # Merge audio fields
        if "audio" not in scene:
            scene["audio"] = template["audio"]
        else:
            for key in template["audio"]:
                if key not in scene["audio"]:
                    scene["audio"][key] = template["audio"][key]

        # Complete generated_assets field
        if "generated_assets" not in scene:
            scene["generated_assets"] = self.create_generated_assets()
        else:
            assets_template = self.create_generated_assets()
            for key in assets_template:
                if key not in scene["generated_assets"]:
                    scene["generated_assets"][key] = assets_template[key]

        # Complete other top-level fields
        top_level_defaults = {
            "episode": episode,
            "title": "",
            "scene_type": "drama",
            "segment_break": False,
            "characters_in_scene": [],
            "clues_in_scene": [],
            "action": "",
            "dialogue": template["dialogue"],
            "transition_to_next": "cut",
        }

        for key, default_value in top_level_defaults.items():
            if key not in scene:
                scene[key] = default_value

        # Update status
        self.update_scene_status(scene)

        return scene

    def update_scene_status(self, scene: dict) -> str:
        """
        Update and return scene status based on generated_assets content

        Status values:
        - pending: not started
        - storyboard_ready: storyboard completed
        - completed: video completed

        Args:
            scene: Scene dictionary

        Returns:
            Updated status value
        """
        assets = scene.get("generated_assets", {})

        has_image = bool(assets.get("storyboard_image"))
        has_video = bool(assets.get("video_clip"))

        if has_video:
            status = "completed"
        elif has_image:
            status = "storyboard_ready"
        else:
            status = "pending"

        assets["status"] = status
        return status

    def normalize_script(self, project_name: str, script_filename: str, save: bool = True) -> dict:
        """
        Complete missing fields in existing script.json

        Args:
            project_name: Project name
            script_filename: Script filename
            save: Whether to save modified script

        Returns:
            Completed script dictionary
        """
        import re

        script = self.load_script(project_name, script_filename)

        # Infer episode from filename or existing data
        episode = script.get("episode", 1)
        if not episode:
            match = re.search(r"episode[_\s]*(\d+)", script_filename, re.IGNORECASE)
            if match:
                episode = int(match.group(1))
            else:
                episode = 1

        # Complete top-level fields
        script_defaults = {
            "episode": episode,
            "title": script.get("novel", {}).get("chapter", ""),
            "duration_seconds": 0,
            "summary": "",
        }

        for key, default_value in script_defaults.items():
            if key not in script:
                script[key] = default_value

        # Ensure necessary top-level structure exists
        if "novel" not in script:
            script["novel"] = {"title": "", "chapter": ""}
        # Strip deprecated source_file field
        if isinstance(script.get("novel"), dict):
            script["novel"].pop("source_file", None)

        # Handle old format: if characters object exists, sync to project.json
        if "characters" in script and isinstance(script["characters"], dict) and script["characters"]:
            logger.warning("Detected old format characters object, auto-syncing to project.json")
            self.sync_characters_from_script(project_name, script_filename)
            # sync_characters_from_script reloads and saves script, so reload needed
            script = self.load_script(project_name, script_filename)

        # Handle old format: if clues object exists, sync to project.json
        if "clues" in script and isinstance(script["clues"], dict) and script["clues"]:
            logger.warning("Detected old format clues object, auto-syncing to project.json")
            self.sync_clues_from_script(project_name, script_filename)
            script = self.load_script(project_name, script_filename)

        # Note:characters_in_episode and clues_in_episode now calculated at read time
        # no longer in normalize_script create these fields

        if "scenes" not in script:
            script["scenes"] = []

        if "metadata" not in script:
            script["metadata"] = {
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "total_scenes": 0,
                "estimated_duration_seconds": 0,
                "status": "draft",
            }

        # Normalize each scene
        for scene in script["scenes"]:
            self.normalize_scene(scene, episode)

        # Update statistics
        script["metadata"]["total_scenes"] = len(script["scenes"])
        script["metadata"]["estimated_duration_seconds"] = sum(s.get("duration_seconds", 8) for s in script["scenes"])
        script["duration_seconds"] = script["metadata"]["estimated_duration_seconds"]

        if save:
            self.save_script(project_name, script, script_filename)
            logger.info("Script normalized and saved: %s", script_filename)

        return script

    # ==================== Scene Management ====================

    def add_scene(self, project_name: str, script_filename: str, scene: dict) -> dict:
        """
        Add scene to script

        Args:
            project_name: Project name
            script_filename: Script filename
            scene: Scene dictionary

        Returns:
            Updated script
        """
        script = self.load_script(project_name, script_filename)

        # Auto-generate scene ID
        existing_ids = [s["scene_id"] for s in script["scenes"]]
        next_id = f"{len(existing_ids) + 1:03d}"
        scene["scene_id"] = next_id

        # Ensure generated_assets field exists
        if "generated_assets" not in scene:
            scene["generated_assets"] = {
                "storyboard_image": None,
                "video_clip": None,
                "status": "pending",
            }

        script["scenes"].append(scene)
        self.save_script(project_name, script, script_filename)
        return script

    def update_scene_asset(
        self,
        project_name: str,
        script_filename: str,
        scene_id: str,
        asset_type: str,
        asset_path: str,
    ) -> dict:
        """
        Update scene generated asset paths

        Args:
            project_name: Project name
            script_filename: Script filename
            scene_id: Scene/segment ID
            asset_type: Asset type ("storyboard_image" or "video_clip")
            asset_path: Asset path

        Returns:
            Updated script
        """
        script = self.load_script(project_name, script_filename)

        # Select correct data structure based on content mode
        content_mode = script.get("content_mode", "narration")
        if content_mode == "narration" and "segments" in script:
            items = script["segments"]
            id_field = "segment_id"
        else:
            items = script.get("scenes", [])
            id_field = "scene_id"

        for item in items:
            if str(item.get(id_field)) == str(scene_id):
                assets = item.get("generated_assets")
                if not isinstance(assets, dict):
                    assets = {}
                    item["generated_assets"] = assets

                assets_template = self.create_generated_assets(content_mode)
                for key, default_value in assets_template.items():
                    if key not in assets:
                        assets[key] = default_value

                assets[asset_type] = asset_path

                # Use update_scene_status to update status
                self.update_scene_status(item)

                self.save_script(project_name, script, script_filename)
                return script

        raise KeyError(f"Scene '{scene_id}' does not exist")

    def get_pending_scenes(self, project_name: str, script_filename: str, asset_type: str) -> list[dict]:
        """
        Get list of pending scenes/segments

        Args:
            project_name: Project name
            script_filename: Script filename
            asset_type: Asset type

        Returns:
            List of pending scenes/segments
        """
        script = self.load_script(project_name, script_filename)

        # Select correct data structure based on content mode
        content_mode = script.get("content_mode", "narration")
        if content_mode == "narration" and "segments" in script:
            items = script["segments"]
        else:
            items = script.get("scenes", [])

        return [item for item in items if not item["generated_assets"].get(asset_type)]

    # ==================== File Path Utilities ====================

    def get_source_path(self, project_name: str, filename: str) -> Path:
        """Get source file path"""
        return self.get_project_path(project_name) / "source" / filename

    def get_character_path(self, project_name: str, filename: str) -> Path:
        """Get character design image path"""
        return self.get_project_path(project_name) / "characters" / filename

    def get_storyboard_path(self, project_name: str, filename: str) -> Path:
        """Get storyboard image path"""
        return self.get_project_path(project_name) / "storyboards" / filename

    def get_video_path(self, project_name: str, filename: str) -> Path:
        """Get video path"""
        return self.get_project_path(project_name) / "videos" / filename

    def get_output_path(self, project_name: str, filename: str) -> Path:
        """Get output path"""
        return self.get_project_path(project_name) / "output" / filename

    def get_scenes_needing_storyboard(self, project_name: str, script_filename: str) -> list[dict]:
        """
        Get list of scenes/segments needing storyboard generation(unified logic for both modes)

        Args:
            project_name: Project name
            script_filename: Script filename

        Returns:
            List of scenes/segments needing storyboard generation
        """
        script = self.load_script(project_name, script_filename)

        content_mode = script.get("content_mode", "narration")
        if content_mode == "narration" and "segments" in script:
            items = script["segments"]
        else:
            items = script.get("scenes", [])

        return [item for item in items if not item.get("generated_assets", {}).get("storyboard_image")]

    # ==================== Project-Level Metadata Management ====================

    def _get_project_file_path(self, project_name: str) -> Path:
        """Get project metadata file path"""
        return self.get_project_path(project_name) / self.PROJECT_FILE

    def project_exists(self, project_name: str) -> bool:
        """Check if project metadata file exists"""
        try:
            return self._get_project_file_path(project_name).exists()
        except FileNotFoundError:
            return False

    def load_project(self, project_name: str) -> dict:
        """
        Load project metadata

        Args:
            project_name: Project name

        Returns:
            Project metadata dictionary
        """
        project_file = self._get_project_file_path(project_name)

        if not project_file.exists():
            raise FileNotFoundError(f"Project metadata file does not exist: {project_file}")

        with open(project_file, encoding="utf-8") as f:
            return json.load(f)

    @contextmanager
    def _project_lock(self, project_name: str):
        """Get exclusive lock for project metadata via dedicated lock file.

        Use independent .project.json.lock instead of data file itself, avoid os.replace
        lock becoming invalid after inode change.
        """
        lock_path = self._get_project_file_path(project_name).with_suffix(".lock")
        lock_path.touch(exist_ok=True)
        fd = open(lock_path)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX)
            yield
        finally:
            fcntl.flock(fd, fcntl.LOCK_UN)
            fd.close()

    @staticmethod
    def _atomic_write_json(path: Path, data: dict) -> None:
        """Atomically write JSON via temporary file + os.replace."""
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=str(path.parent),
                prefix=".project.",
                suffix=".tmp",
                delete=False,
            ) as tmp:
                json.dump(data, tmp, ensure_ascii=False, indent=2)
                tmp_path = Path(tmp.name)
            os.replace(tmp_path, path)
            tmp_path = None
        finally:
            if tmp_path is not None:
                try:
                    tmp_path.unlink()
                except OSError:
                    pass

    def save_project(self, project_name: str, project: dict) -> Path:
        """
        Save project metadata

        Args:
            project_name: Project name
            project: Project metadata dictionary

        Returns:
            Path to saved file
        """
        project_file = self._get_project_file_path(project_name)

        self._touch_metadata(project)

        with self._project_lock(project_name):
            self._atomic_write_json(project_file, project)

        emit_project_change_hint(
            project_name,
            changed_paths=[self.PROJECT_FILE],
        )

        return project_file

    def update_project(
        self,
        project_name: str,
        mutate_fn: Callable[[dict], None],
    ) -> Path:
        """Atomically update project.json: acquire file lock → read → modify → atomic write back.

        Avoid lost-update race conditions between concurrent tasks (e.g., simultaneous character image generation).

        Args:
            project_name: Project name
            mutate_fn: Callback function that receives project dict and modifies in place
        """
        project_file = self._get_project_file_path(project_name)

        with self._project_lock(project_name):
            with open(project_file, encoding="utf-8") as f:
                project = json.load(f)
            mutate_fn(project)
            self._touch_metadata(project)
            self._atomic_write_json(project_file, project)

        emit_project_change_hint(
            project_name,
            changed_paths=[self.PROJECT_FILE],
        )

        return project_file

    @staticmethod
    def _touch_metadata(project: dict) -> None:
        now = datetime.now().isoformat()
        if "metadata" not in project:
            project["metadata"] = {"created_at": now, "updated_at": now}
        else:
            project["metadata"]["updated_at"] = now

    def create_project_metadata(
        self,
        project_name: str,
        title: str | None = None,
        style: str | None = None,
        content_mode: str = "narration",
        aspect_ratio: str = "9:16",
        default_duration: int | None = None,
    ) -> dict:
        """
        Create new project metadata file

        Args:
            project_name: Project identifier
            title: Project title, defaults to project identifier if empty
            style: Overall visual style description
            content_mode: Content mode ("narration" or "drama")
            aspect_ratio: Video aspect ratio(Independent of content_mode)
            default_duration: Default video duration(seconds),None means use system default

        Returns:
            Project metadata dictionary
        """
        project_name = self.normalize_project_name(project_name)
        project_title = str(title).strip() if title is not None else ""

        project = {
            "title": project_title or project_name,
            "content_mode": content_mode,
            "aspect_ratio": aspect_ratio,
            "style": style or "",
            "episodes": [],
            "characters": {},
            "clues": {},
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            },
        }
        if default_duration is not None:
            project["default_duration"] = default_duration

        self.save_project(project_name, project)
        return project

    def add_episode(self, project_name: str, episode: int, title: str, script_file: str) -> dict:
        """
        Add episode to project

        Args:
            project_name: Project name
            episode: Episode number
            title: Episode title
            script_file: Relative path to script file

        Returns:
            Updated project metadata
        """
        project = self.load_project(project_name)

        # Check if already exists
        for ep in project["episodes"]:
            if ep["episode"] == episode:
                ep["title"] = title
                ep["script_file"] = script_file
                self.save_project(project_name, project)
                return project

        # Add new episode(without statistics fields, calculated by StatusCalculator at read time)
        project["episodes"].append({"episode": episode, "title": title, "script_file": script_file})

        # Sort by episode number
        project["episodes"].sort(key=lambda x: x["episode"])

        self.save_project(project_name, project)
        return project

    def sync_project_status(self, project_name: str) -> dict:
        """
        [Deprecated] Sync project status

        This method is deprecated. Statistics fields like status, progress, scenes_count
        Now calculated by StatusCalculator at read time, no longer stored in JSON file.

        Method retained only for backward compatibility, performs no actual write operation.

        Args:
            project_name: Project name

        Returns:
            Project metadata (without statistics fields, injected by StatusCalculator)
        """
        import warnings

        warnings.warn(
            "sync_project_status() is deprecated. Statistics fields like status are now calculated by StatusCalculator at read time.",
            DeprecationWarning,
            stacklevel=2,
        )
        # Only return project data, perform no write
        return self.load_project(project_name)

    # ==================== Project-Level Character Management ====================

    def add_project_character(
        self,
        project_name: str,
        name: str,
        description: str,
        voice_style: str | None = None,
        character_sheet: str | None = None,
    ) -> dict:
        """
        Add character to project (project-level)

        Args:
            project_name: Project name
            name: Character name
            description: Character description
            voice_style: Voice style
            character_sheet: Character design image path

        Returns:
            Updated project metadata
        """
        project = self.load_project(project_name)

        project["characters"][name] = {
            "description": description,
            "voice_style": voice_style or "",
            "character_sheet": character_sheet or "",
        }

        self.save_project(project_name, project)
        return project

    def update_project_character_sheet(self, project_name: str, name: str, sheet_path: str) -> dict:
        """Update project-level character design image path"""
        project = self.load_project(project_name)

        if name not in project["characters"]:
            raise KeyError(f"Character '{name}' does not exist")

        project["characters"][name]["character_sheet"] = sheet_path
        self.save_project(project_name, project)
        return project

    def update_character_reference_image(self, project_name: str, char_name: str, ref_path: str) -> dict:
        """
        Update character reference image path

        Args:
            project_name: Project name
            char_name: Character name
            ref_path: Relative path to reference image

        Returns:
            Updated project data
        """
        project = self.load_project(project_name)

        if "characters" not in project or char_name not in project["characters"]:
            raise KeyError(f"Character '{char_name}' does not exist")

        project["characters"][char_name]["reference_image"] = ref_path
        self.save_project(project_name, project)
        return project

    def get_project_character(self, project_name: str, name: str) -> dict:
        """Get project-level character definition"""
        project = self.load_project(project_name)

        if name not in project["characters"]:
            raise KeyError(f"Character '{name}' does not exist")

        return project["characters"][name]

    # ==================== Clue Management ====================

    def update_clue_sheet(self, project_name: str, name: str, sheet_path: str) -> dict:
        """
        Update clue design image path

        Args:
            project_name: Project name
            name: Clue name
            sheet_path: Design image path

        Returns:
            Updated project metadata
        """
        project = self.load_project(project_name)

        if name not in project["clues"]:
            raise KeyError(f"Clue '{name}' does not exist")

        project["clues"][name]["clue_sheet"] = sheet_path
        self.save_project(project_name, project)
        return project

    def get_clue(self, project_name: str, name: str) -> dict:
        """
        Get clue definition

        Args:
            project_name: Project name
            name: Clue name

        Returns:
            Clue definition dictionary
        """
        project = self.load_project(project_name)

        if name not in project["clues"]:
            raise KeyError(f"Clue '{name}' does not exist")

        return project["clues"][name]

    def get_pending_characters(self, project_name: str) -> list[dict]:
        """
        Get list of characters needing design image generation

        Args:
            project_name: Project name

        Returns:
            List of pending characters(missing character_sheet or file does not exist)
        """
        project = self.load_project(project_name)
        project_dir = self.get_project_path(project_name)

        pending = []
        for name, char in project.get("characters", {}).items():
            sheet = char.get("character_sheet")
            if not sheet or not (project_dir / sheet).exists():
                pending.append({"name": name, **char})

        return pending

    def get_pending_clues(self, project_name: str) -> list[dict]:
        """
        Get list of clues needing design image generation

        Args:
            project_name: Project name

        Returns:
            List of pending clues(importance='major' and missing clue_sheet)
        """
        project = self.load_project(project_name)
        project_dir = self.get_project_path(project_name)

        pending = []
        for name, clue in project["clues"].items():
            if clue.get("importance") == "major":
                sheet = clue.get("clue_sheet")
                if not sheet or not (project_dir / sheet).exists():
                    pending.append({"name": name, **clue})

        return pending

    def get_clue_path(self, project_name: str, filename: str) -> Path:
        """Get clue design image path"""
        return self.get_project_path(project_name) / "clues" / filename

    # ==================== Character/Clue Direct Write Utilities ====================

    def add_character(self, project_name: str, name: str, description: str, voice_style: str = "") -> bool:
        """
        Directly add character to project.json

        If character already exists, skip without overwriting.

        Args:
            project_name: Project name
            name: Character name
            description: Character description
            voice_style: Voice style (optional)

        Returns:
            True if successfully added, False if already exists
        """
        project = self.load_project(project_name)

        if name in project.get("characters", {}):
            logger.debug("Character '%s' already exists in project.json, skipping", name)
            return False

        if "characters" not in project:
            project["characters"] = {}

        project["characters"][name] = {
            "description": description,
            "character_sheet": "",
            "voice_style": voice_style,
        }

        self.save_project(project_name, project)
        logger.info("Add character: %s", name)
        return True

    def add_clue(
        self,
        project_name: str,
        name: str,
        clue_type: str,
        description: str,
        importance: str = "minor",
    ) -> bool:
        """
        Directly add clue to project.json

        If clue already exists, skip without overwriting.

        Args:
            project_name: Project name
            name: Clue name
            clue_type: Clue type("prop" or "location")
            description: Clue description
            importance: Importance("major" or "minor", defaults to "minor")

        Returns:
            True if successfully added, False if already exists
        """
        project = self.load_project(project_name)

        if name in project.get("clues", {}):
            logger.debug("Clue '%s' already exists in project.json, skipping", name)
            return False

        if "clues" not in project:
            project["clues"] = {}

        project["clues"][name] = {
            "type": clue_type,
            "description": description,
            "importance": importance,
            "clue_sheet": "",
        }

        self.save_project(project_name, project)
        logger.info("Add clue: %s", name)
        return True

    def add_characters_batch(self, project_name: str, characters: dict[str, dict]) -> int:
        """
        Batch add character to project.json

        Args:
            project_name: Project name
            characters: Character dict {name: {description, voice_style}}

        Returns:
            Number of newly added characters
        """
        project = self.load_project(project_name)

        if "characters" not in project:
            project["characters"] = {}

        added = 0
        for name, data in characters.items():
            if name not in project["characters"]:
                project["characters"][name] = {
                    "description": data.get("description", ""),
                    "character_sheet": data.get("character_sheet", ""),
                    "voice_style": data.get("voice_style", ""),
                }
                added += 1
                logger.info("Add character: %s", name)
            else:
                logger.debug("Character '%s' already exists, skipping", name)

        if added > 0:
            self.save_project(project_name, project)

        return added

    def add_clues_batch(self, project_name: str, clues: dict[str, dict]) -> int:
        """
        Batch add clue to project.json

        Args:
            project_name: Project name
            clues: Clue dict {name: {type, description, importance}}

        Returns:
            Number of newly added clues
        """
        project = self.load_project(project_name)

        if "clues" not in project:
            project["clues"] = {}

        added = 0
        for name, data in clues.items():
            if name not in project["clues"]:
                project["clues"][name] = {
                    "type": data.get("type", "prop"),
                    "description": data.get("description", ""),
                    "importance": data.get("importance", "minor"),
                    "clue_sheet": data.get("clue_sheet", ""),
                }
                added += 1
                logger.info("Add clue: %s", name)
            else:
                logger.debug("Clue '%s' already exists, skipping", name)

        if added > 0:
            self.save_project(project_name, project)

        return added

    # ==================== Reference Image Collection Utilities ====================

    def collect_reference_images(self, project_name: str, scene: dict) -> list[Path]:
        """
        Collect all reference images needed for a scene

        Args:
            project_name: Project name
            scene: Scene dictionary

        Returns:
            List of reference image paths
        """
        project = self.load_project(project_name)
        project_dir = self.get_project_path(project_name)
        refs = []

        # Character reference image
        for char in scene.get("characters_in_scene", []):
            char_data = project["characters"].get(char, {})
            sheet = char_data.get("character_sheet")
            if sheet:
                sheet_path = project_dir / sheet
                if sheet_path.exists():
                    refs.append(sheet_path)

        # Clue reference image
        for clue in scene.get("clues_in_scene", []):
            clue_data = project["clues"].get(clue, {})
            sheet = clue_data.get("clue_sheet")
            if sheet:
                sheet_path = project_dir / sheet
                if sheet_path.exists():
                    refs.append(sheet_path)

        return refs

    # ==================== Project Overview Generation ====================

    def _read_source_files(self, project_name: str, max_chars: int = 50000) -> str:
        """
        Read content of all text files in project source directory

        Args:
            project_name: Project name
            max_chars: Maximum characters to read(Avoid exceeding API limit)

        Returns:
            Merged text content
        """
        project_dir = self.get_project_path(project_name)
        source_dir = project_dir / "source"

        if not source_dir.exists():
            return ""

        contents = []
        total_chars = 0

        # Sort by filename, ensure consistent order
        for file_path in sorted(source_dir.glob("*")):
            if file_path.is_file() and file_path.suffix.lower() in [".txt", ".md"]:
                try:
                    with open(file_path, encoding="utf-8") as f:
                        content = f.read()
                        remaining = max_chars - total_chars
                        if remaining <= 0:
                            break
                        if len(content) > remaining:
                            content = content[:remaining]
                        contents.append(f"--- {file_path.name} ---\n{content}")
                        total_chars += len(content)
                except Exception as e:
                    logger.error("Failed to read file %s: %s", file_path.name, e)

        return "\n\n".join(contents)

    async def generate_overview(self, project_name: str) -> dict:
        """
        Asynchronously generate project overview using Gemini API

        Args:
            project_name: Project name

        Returns:
            Generated overview dict containing synopsis, genre, theme, world_setting, generated_at
        """
        from .text_backends.base import TextGenerationRequest, TextTaskType
        from .text_generator import TextGenerator

        # Read source file content
        source_content = self._read_source_files(project_name)
        if not source_content:
            raise ValueError("source directory is empty, cannot generate overview")

        # Create TextGenerator (auto-track usage)
        generator = await TextGenerator.create(TextTaskType.OVERVIEW, project_name)

        # Call TextGenerator (Structured Outputs)
        prompt = f"Please analyze the following novel content and extract key information:\n\n{source_content}"

        result = await generator.generate(
            TextGenerationRequest(
                prompt=prompt,
                response_schema=ProjectOverview,
            ),
            project_name=project_name,
        )
        response_text = result.text

        # Parse and validate response
        overview = ProjectOverview.model_validate_json(response_text)
        overview_dict = overview.model_dump()
        overview_dict["generated_at"] = datetime.now().isoformat()

        # Save to project.json
        project = self.load_project(project_name)
        project["overview"] = overview_dict
        self.save_project(project_name, project)

        logger.info("Project overview generated and saved")
        return overview_dict
