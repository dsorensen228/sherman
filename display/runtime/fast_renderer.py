"""ctypes adapter for the dependency-free target procedural-eye renderer."""

from __future__ import annotations

import ctypes
import os
from pathlib import Path
from typing import Protocol


PARAMETER_COUNT = 43
DEFAULT_FRAME_BYTES = 320 * 170 * 2


class FacePose(Protocol):
    params: list[float]


def _default_library_candidates() -> tuple[Path, ...]:
    install_root = Path(__file__).resolve().parents[2]
    name = "libsherman_procedural_eyes_c.so"
    return (
        install_root / "lib" / name,
        Path("/opt/sherman/lib") / name,
    )


class FastProceduralEyesRenderer:
    """Render interpolated 43-value poses into one reused RGB565 buffer."""

    backend_name = "cpp-ctypes"

    def __init__(self, library_path: str | os.PathLike[str] | None = None) -> None:
        requested = Path(library_path) if library_path else None
        environment = os.environ.get("SHERMAN_EYES_LIBRARY")
        if requested is not None:
            candidates = (requested,)
        elif environment:
            candidates = (Path(environment),)
        else:
            candidates = _default_library_candidates()
        selected = next((path for path in candidates if path.is_file()), None)
        if selected is None:
            joined = ", ".join(str(path) for path in candidates)
            raise FileNotFoundError(f"fast eye renderer library not found: {joined}")

        self.library_path = selected
        self._library = ctypes.CDLL(str(selected))
        self._configure_api()
        self._renderer = self._library.sherman_eye_renderer_create()
        if not self._renderer:
            raise RuntimeError("fast eye renderer creation failed")
        self._byte_size = int(
            self._library.sherman_eye_renderer_byte_size(self._renderer)
        )
        if self._byte_size != DEFAULT_FRAME_BYTES:
            self.close()
            raise RuntimeError(
                f"fast eye renderer returned unexpected frame size {self._byte_size}"
            )
        self._pose = (ctypes.c_float * PARAMETER_COUNT)()
        self._output = (ctypes.c_uint8 * self._byte_size)()
        self._view = memoryview(self._output).cast("B")

    def _configure_api(self) -> None:
        library = self._library
        library.sherman_eye_renderer_create.argtypes = []
        library.sherman_eye_renderer_create.restype = ctypes.c_void_p
        library.sherman_eye_renderer_destroy.argtypes = [ctypes.c_void_p]
        library.sherman_eye_renderer_destroy.restype = None
        library.sherman_eye_renderer_byte_size.argtypes = [ctypes.c_void_p]
        library.sherman_eye_renderer_byte_size.restype = ctypes.c_size_t
        library.sherman_eye_renderer_render_pose_rgb565_be.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_float),
            ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
        ]
        library.sherman_eye_renderer_render_pose_rgb565_be.restype = ctypes.c_int

    def render_rgb565(self, face: FacePose) -> memoryview:
        if not self._renderer:
            raise RuntimeError("fast eye renderer is closed")
        if len(face.params) != PARAMETER_COUNT:
            raise ValueError("procedural face requires exactly 43 parameters")
        for index, value in enumerate(face.params):
            self._pose[index] = value
        result = self._library.sherman_eye_renderer_render_pose_rgb565_be(
            self._renderer,
            self._pose,
            PARAMETER_COUNT,
            self._output,
            self._byte_size,
        )
        if result != 0:
            raise RuntimeError(f"fast eye render failed with status {result}")
        return self._view

    def close(self) -> None:
        renderer = getattr(self, "_renderer", None)
        if renderer:
            self._library.sherman_eye_renderer_destroy(renderer)
            self._renderer = None

    def __enter__(self) -> "FastProceduralEyesRenderer":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def __del__(self) -> None:
        self.close()
