#!/usr/bin/env python3
"""天气查询 MCP 服务器"""

import json
import requests
import os
from datetime import datetime
from typing import Dict, Any
from hello_agents.protocols import MCPServer
import logging
import sys

# 显式配置日志输出到 Stderr (标准错误)
# 这样可以保证日志会被记录，但不会干扰 Smithery 的 Stdout 扫描
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr 
)


# 创建 MCP 服务器
weather_server = MCPServer(name="weather-server", description="真实天气查询服务")

CITY_MAP = {
    "北京": "Beijing", "上海": "Shanghai", "广州": "Guangzhou",
    "深圳": "Shenzhen", "杭州": "Hangzhou", "成都": "Chengdu",
    "重庆": "Chongqing", "武汉": "Wuhan", "西安": "Xi'an",
    "南京": "Nanjing", "天津": "Tianjin", "苏州": "Suzhou"
}


def get_weather_data(city: str) -> Dict[str, Any]:
    """从 wttr.in 获取天气数据"""
    city_en = CITY_MAP.get(city, city)
    url = f"https://wttr.in/{city_en}?format=j1"
    # 添加 User-Agent
    headers = {"User-Agent": "Weather-MCP-Server/1.0"}
    
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    data = response.json()
    current = data["current_condition"][0]

    return {
        "city": city,
        "temperature": float(current["temp_C"]),
        "feels_like": float(current["FeelsLikeC"]),
        "humidity": int(current["humidity"]),
        "condition": current["weatherDesc"][0]["value"],
        "wind_speed": round(float(current["windspeedKmph"]) / 3.6, 1),
        "visibility": float(current["visibility"]),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


# 定义工具函数
def get_weather(city: str) -> str:
    """获取指定城市的当前天气"""
    try:
        weather_data = get_weather_data(city)
        return json.dumps(weather_data, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "city": city}, ensure_ascii=False)


def list_supported_cities() -> str:
    """列出所有支持的中文城市"""
    result = {"cities": list(CITY_MAP.keys()), "count": len(CITY_MAP)}
    return json.dumps(result, ensure_ascii=False, indent=2)


def get_server_info() -> str:
    """获取服务器信息"""
    info = {
        "name": "Weather MCP Server",
        "version": "1.0.0",
        "framework": "HelloAgents",
        "status": "running"
    }
    return json.dumps(info, ensure_ascii=False, indent=2)


# 注册工具到服务器
weather_server.add_tool(get_weather)
weather_server.add_tool(list_supported_cities)
weather_server.add_tool(get_server_info)


if __name__ == "__main__":
    # 获取端口配置
    port = int(os.getenv("PORT", 8081))
    host = "0.0.0.0"

    logging.info(f"🌤️  Starting Weather MCP Server (HelloAgents)")
    logging.info(f"🔌 Port: {port}")
    
    # -----------------------------------------------------------
    # 关键修改：使用 transport="sse"
    # -----------------------------------------------------------
    # Smithery 和大多数 HTTP MCP 客户端需要 SSE (Server-Sent Events)
    # HelloAgents (通过 FastMCP) 会在 /sse 路径提供服务
    weather_server.mcp.run(transport="sse", host=host, port=port)