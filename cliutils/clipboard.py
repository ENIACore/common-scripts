import shutil
import subprocess


def copy_to_clipboard(text: str) -> str:
    """Copy text to the system clipboard and return the tool used, or empty string."""
    commands = (
        ("pbcopy", ["pbcopy"]),
        ("xclip", ["xclip", "-selection", "clipboard"]),
        ("xsel", ["xsel", "--clipboard", "--input"]),
        ("wl-copy", ["wl-copy"]),
    )
    for executable, command in commands:
        if shutil.which(executable):
            subprocess.run(command, input=text.encode(), check=True)
            return executable
    return ""
