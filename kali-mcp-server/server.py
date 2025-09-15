"""Simple MCP server exposing security tools.

Use responsibly and only on systems you have permission to test.
"""

import subprocess

from flask import Flask, jsonify, request

app = Flask(__name__)


@app.route("/run", methods=["POST"])
def run_command():
    """Execute a shell command from JSON payload."""
    data = request.get_json() or {}
    cmd = data.get("cmd", "")
    if not cmd:
        return jsonify({"error": "No command supplied"}), 400

    try:
        output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, text=True)
        return jsonify({"output": output})
    except subprocess.CalledProcessError as exc:  # pragma: no cover - for brevity
        return jsonify({"error": exc.output}), 400


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
