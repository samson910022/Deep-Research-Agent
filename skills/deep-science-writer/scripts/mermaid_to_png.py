import urllib.request
import base64
import json
import sys

def generate_mermaid_png(mermaid_code: str, output_path: str):
    """
    Generates a PNG from Mermaid code using the reliable mermaid.ink API.
    This avoids the 400 Bad Request errors often seen with Kroki for complex graphs.
    """
    state = {
        "code": mermaid_code,
        "mermaid": {
            "theme": "default",
            "securityLevel": "loose" # Allows HTML tags like <b> and <br>
        }
    }
    b64_str = base64.urlsafe_b64encode(json.dumps(state).encode('utf-8')).decode('utf-8')
    url = f"https://mermaid.ink/img/{b64_str}"
    
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req) as response, open(output_path, 'wb') as out_file:
            out_file.write(response.read())
        print(f"Successfully saved Mermaid diagram to {output_path}")
    except Exception as e:
        print(f"Failed to generate Mermaid PNG: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Example usage
    sample_mermaid = "graph TD\n A[Start] --> B[End]"
    generate_mermaid_png(sample_mermaid, "output.png")