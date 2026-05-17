import json
import datetime
from typing import List, Dict

def generate_summary(tool_name: str, findings: List[Dict], observations: str):
    report = {
        "timestamp": datetime.datetime.now().isoformat(),
        "artifact": tool_name,
        "findings": findings,
        "observation": observations
    }
    filename = f"{tool_name.lower().replace(' ', '_')}_report_{datetime.date.today()}.json"
    with open(f"reports/{filename}", "w") as f:
        json.dump(report, f, indent=4)
    return filename

if __name__ == "__main__":
    print("ReportingTool loaded.")
