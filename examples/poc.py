# poc.py
# Compile Agent · Minimal Deterministic Runtime Demo
# Author: Yuer
# Date: 2025-11-18
# License: MIT

import re
import json
from typing import Dict, Callable, Any

# ============================
# 1. TOOL REGISTRY (Whitelisted)
# ============================

TOOL_REGISTRY: Dict[str, Callable] = {}

def tool(name: str):
    """Register deterministic tools."""
    def decorator(fn):
        TOOL_REGISTRY[name] = fn
        return fn
    return decorator


# ============================
# 2. Deterministic Tools
# ============================

@tool("WeatherAPI")
def weather_api(city: str) -> Dict[str, Any]:
    # mock: no randomness, no network
    data = {
        "Beijing": {"temp_c": 28, "desc": "Sunny"},
        "Shanghai": {"temp_c": 22, "desc": "Cloudy"},
    }
    return data.get(city, {"temp_c": 0, "desc": "Unknown"})


@tool("UnitConverter")
def convert_temperature_c_to_f(celsius: float) -> Dict[str, Any]:
    f = celsius * 9/5 + 32
    return {"fahrenheit": round(f, 2)}


# ============================
# 3. SIMPLE IR PARSER
# ============================

def compile_intent(intent: str) -> Dict[str, Any]:
    """
    Convert natural language to a static execution plan.
    (Minimal POC, not a real compiler)
    """
    plan = {"nodes": []}

    lines = [line.strip() for line in intent.split("\n") if line.strip()]
    for line in lines:
        if line.startswith("get weather"):
            city = re.findall(r"weather from (.*)", line)[0]
            plan["nodes"].append({
                "id": "fetch_weather",
                "tool": "WeatherAPI",
                "input": {"city": city}
            })

        if line.startswith("convert temperature"):
            plan["nodes"].append({
                "id": "convert_units",
                "tool": "UnitConverter",
                "input": {"temp_c": "@fetch_weather.temp_c"}
            })

    return plan


# ============================
# 4. STATIC VALIDATOR
# ============================

def validate_plan(plan: Dict[str, Any]):
    for node in plan["nodes"]:
        tool_name = node["tool"]
        if tool_name not in TOOL_REGISTRY:
            raise ValueError(f"Tool not allowed: {tool_name}")


# ============================
# 5. EXECUTION RUNTIME
# ============================

def run(plan: Dict[str, Any]) -> Dict[str, Any]:
    ctx = {}
    logs = []

    for node in plan["nodes"]:
        tool_name = node["tool"]
        fn = TOOL_REGISTRY[tool_name]

        # Resolve inputs
        resolved_input = {}
        for k, v in node["input"].items():
            if isinstance(v, str) and v.startswith("@"):
                ref_node, ref_field = v[1:].split(".")
                resolved_input[k] = ctx[ref_node][ref_field]
            else:
                resolved_input[k] = v

        # Execute tool deterministically
        result = fn(**resolved_input)

        ctx[node["id"]] = result
        logs.append({
            "node": node["id"],
            "tool": tool_name,
            "input": resolved_input,
            "output": result
        })

    return {"result": ctx, "logs": logs}


# ============================
# 6. RUN POC
# ============================

if __name__ == "__main__":
    intent = """
    get weather from Beijing
    convert temperature to Fahrenheit
    """

    print("=== COMPILE AGENT: COMPILE INTENT ===")
    plan = compile_intent(intent)
    print(json.dumps(plan, indent=2, ensure_ascii=False))

    print("\n=== VALIDATING PLAN ===")
    validate_plan(plan)
    print("OK")

    print("\n=== EXECUTING DETERMINISTIC RUNTIME ===")
    output = run(plan)
    print(json.dumps(output, indent=2, ensure_ascii=False))

    print("\n=== DONE ===")
