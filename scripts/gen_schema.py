import json

from soc_agent.config import Settings

print(json.dumps(Settings.model_json_schema(), indent=2))
