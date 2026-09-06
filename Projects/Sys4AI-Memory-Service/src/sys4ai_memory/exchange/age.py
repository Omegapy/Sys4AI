"""Small non-shell bridge to the approved age X25519 envelope tool."""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

_RECIPIENT = re.compile(r"^age1[0-9a-z]{20,100}$")


class AgeToolError(RuntimeError):
    """The local age executable could not complete a bounded operation."""


class AgeTool:
    """Encrypt and decrypt bytes without exposing key material or command shells."""

    def __init__(self, executable: str | Path | None = None, *, timeout_seconds: int = 120) -> None:
        selected = str(executable) if executable is not None else shutil.which("age")
        if selected is None:
            raise AgeToolError("age executable is unavailable")
        path = Path(selected)
        if not path.is_absolute():
            raise AgeToolError("age executable is not a regular absolute path")
        try:
            resolved = path.resolve(strict=True)
        except OSError as error:
            raise AgeToolError("age executable is unavailable") from error
        if not resolved.is_file():
            raise AgeToolError("age executable is not a regular absolute path")
        if timeout_seconds <= 0:
            raise ValueError("age timeout must be positive")
        self.executable = resolved
        self.timeout_seconds = timeout_seconds

    def version(self) -> str:
        result = self._run(("--version",), b"")
        try:
            return result.decode("utf-8").strip()
        except UnicodeDecodeError as error:
            raise AgeToolError("age version output is invalid") from error

    def encrypt(self, plaintext: bytes, *, recipient: str) -> bytes:
        if _RECIPIENT.fullmatch(recipient) is None:
            raise AgeToolError("age recipient is invalid")
        encrypted = self._run(("--encrypt", "--recipient", recipient), plaintext)
        if not encrypted:
            raise AgeToolError("age encryption produced no envelope")
        return encrypted

    def decrypt(
        self,
        envelope: bytes,
        *,
        identity_file: Path,
        max_output_bytes: int,
    ) -> bytes:
        if max_output_bytes <= 0:
            raise ValueError("age output bound must be positive")
        if identity_file.is_symlink() or not identity_file.is_file():
            raise AgeToolError("age identity file is unavailable")
        identity = identity_file.resolve(strict=True)
        plaintext = self._run(("--decrypt", "--identity", str(identity)), envelope)
        if len(plaintext) > max_output_bytes:
            raise AgeToolError("age plaintext exceeds the configured package bound")
        return plaintext

    def _run(self, arguments: tuple[str, ...], content: bytes) -> bytes:
        try:
            result = subprocess.run(  # noqa: S603 - resolved executable and non-shell argv
                (str(self.executable), *arguments),
                input=content,
                capture_output=True,
                check=False,
                timeout=self.timeout_seconds,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            raise AgeToolError("age operation did not complete") from error
        if result.returncode != 0:
            raise AgeToolError("age operation failed")
        return result.stdout


__all__ = ["AgeTool", "AgeToolError"]
