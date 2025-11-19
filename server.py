#!/usr/bin/env python3
"""天气查询 MCP 服务器（基于 fastmcp 优化版）"""

import requests
import os
from datetime import datetime
from typing import Dict, Any
import logging
import sys
from fastmcp import FastMCP  # 导入 FastMCP 核心类

# 配置日志输出到标准错误（不干扰 SSE 输出）
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr 
)

# 创建 FastMCP 实例（补充 dependencies 元数据）
app = FastMCP(
    name="weather-server",
    description="真实天气查询服务，提供城市实时天气、支持城市列表及服务器信息查询",
    # 补充依赖信息（元数据更完善，便于客户端识别服务器依赖）
    dependencies={
        "requests": ">=2.25.0",  # 用于HTTP请求的库版本要求
        "python": ">=3.8",       # 支持的Python版本
        "fastmcp": ">=0.1.0"     # 依赖的fastmcp版本
    }
)

CITY_MAP = {
    "北京": "Beijing", "上海": "Shanghai", "广州": "Guangzhou",
    "深圳": "Shenzhen", "杭州": "Hangzhou", "成都": "Chengdu",
    "重庆": "Chongqing", "武汉": "Wuhan", "西安": "Xi'an",
    "南京": "Nanjing", "天津": "Tianjin", "苏州": "Suzhou"
}


def get_weather_data(city: str) -> Dict[str, Any]:
    """从 wttr.in 获取天气数据（辅助函数）"""
    city_en = CITY_MAP.get(city, city)
    url = f"https://wttr.in/{city_en}?format=j1"
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
        "wind_speed": round(float(current["windspeedKmph"]) / 3.6, 1),  # 转换为 m/s
        "visibility": float(current["visibility"]),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


# 工具返回 dict 类型（FastMCP 自动处理 JSON 序列化）
@app.tool(name="get_weather", description="获取指定城市的当前天气，参数为中文城市名")
def get_weather(city: str) -> Dict[str, Any]:
    try:
        weather_data = get_weather_data(city)
        return weather_data  # 直接返回字典，由框架自动序列化
    except Exception as e:
        return {"error": str(e), "city": city}  # 异常信息也返回字典


@app.tool(name="list_supported_cities", description="列出所有支持查询的中文城市")
def list_supported_cities() -> Dict[str, Any]:
    return {
        "cities": list(CITY_MAP.keys()),
        "count": len(CITY_MAP),
        "message": "支持以下城市的天气查询"
    }  # 直接返回字典


@app.tool(name="get_server_info", description="获取当前天气服务器的元数据信息")
def get_server_info() -> Dict[str, Any]:
    return {
        "name": "Weather MCP Server",
        "version": "1.0.0",
        "framework": "fastmcp",
        "status": "running",
        "dependencies": app.dependencies,  # 复用初始化时的依赖信息
        "supported_functions": ["get_weather", "list_supported_cities", "get_server_info"]
    }  # 直接返回字典


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8081))
    host = "0.0.0.0"

    logging.info(f"🌤️  Starting Weather MCP Server (fastmcp)")
    logging.info(f"🔌 SSE 路由: http://{host}:{port}/sse")
    logging.info(f"📦 依赖信息: {app.dependencies}")
    logging.info(f"📡 服务启动中...")

    # 显式启用 SSE 传输模式
    app.run(host=host, port=port, transport="sse")