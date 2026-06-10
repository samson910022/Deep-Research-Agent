import urllib.request
import base64
import json
import os


class MermaidGenerationError(Exception):
    """Raised when Mermaid PNG generation fails."""
    pass


SAFE_BASES = [
    "D:\\",
    os.path.expanduser("~/Documents/Obsidian Vault/Hermes/"),
    os.getcwd(),
]


def safe_path(dest: str) -> bool:
    """Validate that *dest* resolves to a path under an allowed base directory.

    Prevents path-traversal writes to arbitrary filesystem locations.
    """
    abs_dest = os.path.abspath(dest)
    return any(abs_dest.startswith(os.path.abspath(base)) for base in SAFE_BASES)


def generate_mermaid_png(mermaid_code: str, output_path: str, theme: str = "default"):
    """
    Generates a PNG from Mermaid code using the reliable mermaid.ink API.
    This avoids the 400 Bad Request errors often seen with Kroki for complex graphs.

    Parameters:
        mermaid_code: The Mermaid diagram definition string.
        output_path: Filesystem path where the PNG will be saved.
        theme: Mermaid theme name (default: 'default').
               Common values: 'default', 'dark', 'neutral', 'forest', 'base'.
    """
    state = {
        "code": mermaid_code,
        "mermaid": {
            "theme": theme,
            "securityLevel": "loose"  # Allows HTML tags like <b> and <br>
        }
    }
    b64_str = base64.urlsafe_b64encode(
        json.dumps(state).encode('utf-8')
    ).decode('utf-8')
    url = f"https://mermaid.ink/img/{b64_str}"

    if not safe_path(output_path):
        print(f"[WARN] Unsafe path '{output_path}', redirecting to current directory")
        output_path = os.path.basename(output_path)

    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req) as response, \
                open(output_path, 'wb') as out_file:
            out_file.write(response.read())
        print(f"Successfully saved Mermaid diagram to {output_path}")
    except Exception as e:
        msg = f"Failed to generate Mermaid PNG: {e}"
        print(msg)
        raise MermaidGenerationError(msg) from e


if __name__ == "__main__":
    # Example usage
    sample_mermaid = "graph TD\n A[Start] --> B[End]"
    generate_mermaid_png(sample_mermaid, "output.png")
