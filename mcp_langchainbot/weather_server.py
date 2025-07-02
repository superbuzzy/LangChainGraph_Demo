import httpx
from typing import Any, Optional
from mcp.server.fastmcp import FastMCP
from datetime import datetime, timezone, timedelta

import os 
from dotenv import load_dotenv
load_dotenv()

# 初始化 MCP 服务器
mcp = FastMCP("WeatherServer")

# OpenWeather API 配置
GEOCODING_API_BASE = "https://api.openweathermap.org/geo/1.0/direct"
ONECALL_API_BASE = "https://api.openweathermap.org/data/3.0/onecall"
ONECALL_HISTORY_API_BASE = "https://api.openweathermap.org/data/3.0/onecall/timemachine"
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
USER_AGENT = "weather-app/1.0"


async def get_coordinates(city: str) -> dict[str, Any] | None:
    """
    通过城市名称获取经纬度坐标。
    :param city: 城市名称
    :return: 包含经纬度的字典或错误信息
    """
    params = {
        "q": city,
        "limit": 1,
        "appid": OPENWEATHER_API_KEY
    }
    headers = {"User-Agent": USER_AGENT}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(GEOCODING_API_BASE, params=params, headers=headers, timeout=30.0)
            response.raise_for_status()
            data = response.json()
            
            if not data:
                return {"error": f"未找到城市: {city}"}
            
            location = data[0]
            return {
                "lat": location["lat"],
                "lon": location["lon"],
                "name": location["name"],
                "country": location.get("country", "")
            }
        except httpx.HTTPStatusError as e:
            return {"error": f"HTTP 错误: {e.response.status_code}"}
        except Exception as e:
            return {"error": f"请求失败: {str(e)}"}

async def fetch_weather_data(
    lat: float, 
    lon: float, 
    timestamp: Optional[int] = None, 
    exclude: Optional[str] = None
) -> dict[str, Any] | None:
    """
    获取天气数据的统一函数，支持当前天气、预报和历史数据。
    """
    params = {
        "lat": lat,
        "lon": lon,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",
        "lang": "zh_cn"
    }
    
    if timestamp is not None:
        api_url = ONECALL_HISTORY_API_BASE
        params["dt"] = timestamp
    else:
        api_url = ONECALL_API_BASE
        if exclude:
            params["exclude"] = exclude
    
    headers = {"User-Agent": USER_AGENT}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(api_url, params=params, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            return {"error": f"HTTP 错误: {e.response.status_code}"}
        except Exception as e:
            return {"error": f"请求失败: {str(e)}"}

@mcp.tool()
async def query_weather(
    city: str,
    query_type: str = "current",
    days: int = 3,
    days_ago: int = 1
) -> dict[str, Any]:
    """
    统一的天气查询工具，支持当前天气、预报和历史数据查询。
    
    :param city: 城市名称（支持中英文）
    :param query_type: 查询类型，可选值：
        - "current": 当前天气
        - "forecast": 天气预报
        - "historical": 历史天气
    :param days: 预报天数（1-8天，默认3天），仅在 query_type="forecast" 时生效
    :param days_ago: 历史天数（1-5天前，默认1天前），仅在 query_type="historical" 时生效
    :return: 天气数据，包含城市信息和查询类型
    """
    
    # 参数验证
    if query_type not in ["current", "forecast", "historical"]:
        return {"error": "query_type 必须是 'current', 'forecast', 或 'historical'"}
    
    if query_type == "forecast" and (days < 1 or days > 8):
        return {"error": "预报天数必须在 1-8 天之间"}
    
    if query_type == "historical" and (days_ago < 1 or days_ago > 5):
        return {"error": "历史天数必须在 1-5 天之间（免费版限制）"}
    
    # 获取经纬度
    coord_data = await get_coordinates(city)
    if "error" in coord_data:
        return {"error": coord_data["error"]}
    
    # 根据查询类型设置参数
    timestamp = None
    exclude = None
    
    if query_type == "current":
        exclude = "minutely,hourly,daily,alerts"
    elif query_type == "forecast":
        exclude = "minutely,hourly,alerts"
    elif query_type == "historical":
        # 计算历史时间戳
        now = datetime.now(timezone.utc)
        target_dt = now - timedelta(days=days_ago)
        timestamp = int(target_dt.timestamp())
    
    # 获取天气数据
    weather_data = await fetch_weather_data(
        coord_data["lat"],
        coord_data["lon"],
        timestamp=timestamp,
        exclude=exclude
    )
    
    # 处理返回数据
    if weather_data and "error" not in weather_data:
        # 添加城市信息
        weather_data["city_info"] = {
            "name": coord_data["name"],
            "country": coord_data["country"],
            "coordinates": {
                "lat": coord_data["lat"],
                "lon": coord_data["lon"]
            }
        }
        
        # 添加查询相关信息
        weather_data["query_info"] = {
            "type": query_type,
            "city": city
        }
        
        # 根据查询类型添加特定信息
        if query_type == "forecast":
            weather_data["query_info"]["requested_days"] = days
            # 限制返回的天数
            if "daily" in weather_data:
                weather_data["daily"] = weather_data["daily"][:days]
        elif query_type == "historical":
            weather_data["query_info"]["days_ago"] = days_ago
    
    return weather_data

@mcp.tool()
async def get_current_date() -> str:
    """
    获取当前日期和时间信息。
    :return: 当前的日期时间信息
    """
    now = datetime.now(timezone.utc)
    local_now = datetime.now()
    
    return (
        f"🕐 当前UTC时间: {now.strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
        f"🕐 当前本地时间: {local_now.strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"📅 今天日期: {local_now.strftime('%Y-%m-%d')}\n"
        f"📅 星期: {local_now.strftime('%A')}\n"
        f"🌍 时区信息: 本地时区"
    )

if __name__ == "__main__":
    mcp.run(transport='stdio')