#!/usr/bin/env python3
"""天气查询 MCP 服务器（Stdio 模式，简化版）"""

import requests
from datetime import datetime
from typing import Dict, Any
import logging
import sys
from fastmcp import FastMCP

# 配置日志（输出到标准错误，不干扰Stdio通信）
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)

# 初始化FastMCP（Stdio模式默认启用，补充元数据）
app = FastMCP(
    name="weather-server",
    description="真实天气查询服务（Stdio模式）",
    dependencies={
        "requests": ">=2.25.0",
        "python": ">=3.8",
        "fastmcp": ">=0.1.0"
    }
)

# 城市映射表
CITY_MAP = {
    "北京": "Beijing", "上海": "Shanghai", "广州": "Guangzhou",
    "深圳": "Shenzhen", "杭州": "Hangzhou", "成都": "Chengdu",
    "重庆": "Chongqing", "武汉": "Wuhan", "西安": "Xi'an",
    "南京": "Nanjing", "天津": "Tianjin", "苏州": "Suzhou"
}


def get_weather_data(city: str) -> Dict[str, Any]:
    """获取天气原始数据（辅助函数）"""
    city_en = CITY_MAP.get(city, city)
    url = f"https://wttr.in/{city_en}?format=j1"
    headers = {"User-Agent": "Weather-MCP-Stdio/1.0"}
    
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    current = response.json()["current_condition"][0]
    
    return {
        "city": city,
        "temperature": float(current["temp_C"]),
        "feels_like": float(current["FeelsLikeC"]),
        "humidity": int(current["humidity"]),
        "condition": current["weatherDesc"][0]["value"],
        "wind_speed": round(float(current["windspeedKmph"]) / 3.6, 1),  # 转换为m/s
        "visibility": float(current["visibility"]),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


# 注册工具（绑定到app实例）
@app.tool(name="get_weather", description="获取指定中文城市的当前天气")
def get_weather(city: str) -> Dict[str, Any]:
    try:
        return get_weather_data(city)
    except Exception as e:
        return {"error": str(e), "city": city}


@app.tool(name="list_supported_cities", description="列出所有支持的中文城市")
def list_supported_cities() -> Dict[str, Any]:
    return {
        "cities": list(CITY_MAP.keys()),
        "count": len(CITY_MAP)
    }


@app.tool(name="get_server_info", description="获取服务器元信息")
def get_server_info() -> Dict[str, Any]:
    return {
        "name": app.name,
        "description": app.description,
        "version": "1.0.0",
        "mode": "stdio",  # 明确标注为Stdio模式
        "dependencies": app.dependencies
    }


if __name__ == "__main__":
    logging.info(f"🌤️  Starting Weather MCP Server (Stdio模式)")
    logging.info(f"📡  通过标准输入输出通信，无需网络端口")
    
    # Stdio模式默认启用，直接运行（无需host/port/transport参数）
    app.run()