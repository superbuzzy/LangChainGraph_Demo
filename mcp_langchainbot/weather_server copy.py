import httpx
from typing import Any, Optional
from mcp.server.fastmcp import FastMCP
from datetime import datetime, timezone
import time

import os 
from dotenv import load_dotenv
load_dotenv()

# 全局变量用于传递预报天数
_forecast_days = 3

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
    
    :param lat: 纬度
    :param lon: 经度
    :param timestamp: Unix时间戳，如果提供则获取历史数据，否则获取当前/预报数据
    :param exclude: 要排除的数据部分，用逗号分隔 (minutely,hourly,daily,alerts)
                   仅对当前/预报数据有效
    :return: 天气数据字典
    """
    # 基础参数
    params = {
        "lat": lat,
        "lon": lon,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",
        "lang": "zh_cn"
    }
    
    # 根据是否提供时间戳决定API端点和参数
    if timestamp is not None:
        # 历史数据请求
        api_url = ONECALL_HISTORY_API_BASE
        params["dt"] = timestamp
    else:
        # 当前/预报数据请求
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


# 为了保持向后兼容性，可以创建包装函数
# async def fetch_current_weather(lat: float, lon: float, exclude: Optional[str] = None) -> dict[str, Any] | None:
#     """获取当前天气和预报信息的包装函数"""
#     return await fetch_weather_data(lat, lon, exclude=exclude)


# async def fetch_historical_weather(lat: float, lon: float, timestamp: int) -> dict[str, Any] | None:
#     """获取历史天气数据的包装函数"""
#     return await fetch_weather_data(lat, lon, timestamp=timestamp)

def format_weather_data(data: dict[str, Any], city_name: str = "", format_type: str = "current") -> str:
    """
    通用天气数据格式化函数。
    :param data: 天气数据
    :param city_name: 城市名称
    :param format_type: 格式类型 ("current", "forecast", "historical")
    :return: 格式化的天气信息
    """
    if "error" in data:
        return f"⚠️ {data['error']}"
    
    result = f"🌍 {city_name}\n" if city_name else ""
    
    if format_type == "current":
        return result + _format_current_section(data.get("current", {}))
    elif format_type == "forecast":
        current_result = result + _format_current_section(data.get("current", {}))
        forecast_result = _format_forecast_section(data.get("daily", []))
        return f"{current_result}\n\n{forecast_result}"
    elif format_type == "historical":
        historical_data = data.get("data", [{}])[0] if data.get("data") else {}
        return result + _format_historical_section(historical_data)
    
    return "⚠️ 未知的格式类型"

def _format_current_section(current: dict[str, Any]) -> str:
    """格式化当前天气部分"""
    temp = current.get("temp", "N/A")
    feels_like = current.get("feels_like", "N/A")
    humidity = current.get("humidity", "N/A")
    pressure = current.get("pressure", "N/A")
    wind_speed = current.get("wind_speed", "N/A")
    wind_deg = current.get("wind_deg", "N/A")
    visibility = current.get("visibility", "N/A")
    uvi = current.get("uvi", "N/A")
    
    weather_list = current.get("weather", [{}])
    description = weather_list[0].get("description", "未知")
    
    dt = current.get("dt", 0)
    update_time = datetime.fromtimestamp(dt, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    
    result = (
        f"🕐 更新时间: {update_time}\n"
        f"🌡 当前温度: {temp}°C (体感 {feels_like}°C)\n"
        f"💧 湿度: {humidity}%\n"
        f"🌬 风速: {wind_speed} m/s, 风向: {wind_deg}°\n"
        f"🌤 天气: {description}\n"
        f"📊 气压: {pressure} hPa\n"
        f"☀️ 紫外线指数: {uvi}\n"
    )
    
    if visibility != "N/A":
        result += f"👁 能见度: {visibility/1000:.1f} km\n"
    
    return result

def _format_forecast_section(daily: list[dict[str, Any]]) -> str:
    """格式化预报部分"""
    if not daily:
        return "📅 暂无每日预报数据"
    
    # 获取全局变量中的天数，如果没有则默认为3
    days = globals().get('_forecast_days', 3)
    
    result = f"📅 未来{min(days, len(daily))}天预报:\n\n"
    
    for day in daily[:days]:
        dt = day.get("dt", 0)
        date = datetime.fromtimestamp(dt, tz=timezone.utc).strftime("%m-%d")
        
        temp_day = day.get("temp", {}).get("day", "N/A")
        temp_night = day.get("temp", {}).get("night", "N/A")
        temp_max = day.get("temp", {}).get("max", "N/A")
        temp_min = day.get("temp", {}).get("min", "N/A")
        
        weather_list = day.get("weather", [{}])
        description = weather_list[0].get("description", "未知")
        
        humidity = day.get("humidity", "N/A")
        wind_speed = day.get("wind_speed", "N/A")
        pop = day.get("pop", 0)
        
        result += (
            f"📆 {date}: {description}\n"
            f"   🌡 {temp_min}°C ~ {temp_max}°C (白天{temp_day}°C, 夜间{temp_night}°C)\n"
            f"   💧 湿度{humidity}% | 🌬风速{wind_speed}m/s | 🌧降水概率{pop*100:.0f}%\n\n"
        )
    
    return result

def _format_historical_section(historical: dict[str, Any]) -> str:
    """格式化历史天气部分"""
    temp = historical.get("temp", "N/A")
    humidity = historical.get("humidity", "N/A")
    pressure = historical.get("pressure", "N/A")
    wind_speed = historical.get("wind_speed", "N/A")
    
    weather_list = historical.get("weather", [{}])
    description = weather_list[0].get("description", "未知")
    
    dt = historical.get("dt", 0)
    date_time = datetime.fromtimestamp(dt, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    
    return (
        f"🕐 时间: {date_time}\n"
        f"🌡 温度: {temp}°C\n"
        f"💧 湿度: {humidity}%\n"
        f"🌬 风速: {wind_speed} m/s\n"
        f"🌤 天气: {description}\n"
        f"📊 气压: {pressure} hPa\n"
    )

@mcp.tool()
async def query_current_weather(city: str) -> str:
    """
    查询指定城市的当前天气信息。
    :param city: 城市名称（支持中英文）
    :return: 格式化后的当前天气信息
    """
    # 获取经纬度
    coord_data = await get_coordinates(city)
    if "error" in coord_data:
        return f"⚠️ {coord_data['error']}"
    
    # 获取天气数据（排除小时和每日预报以减少数据量）
    weather_data = await fetch_weather_data(
        coord_data["lat"], 
        coord_data["lon"], 
        exclude="minutely,hourly,daily,alerts"
    )
    
    city_display = f"{coord_data['name']}, {coord_data['country']}"
    return format_weather_data(weather_data, city_display, "current")

@mcp.tool()
async def query_weather_forecast(city: str, days: int = 3) -> str:
    """
    查询指定城市的天气预报。
    :param city: 城市名称（支持中英文）
    :param days: 预报天数（1-8天，默认3天）
    :return: 格式化后的天气预报信息
    """
    if days < 1 or days > 8:
        return "⚠️ 预报天数必须在 1-8 天之间"
    
    # 获取经纬度
    coord_data = await get_coordinates(city)
    if "error" in coord_data:
        return f"⚠️ {coord_data['error']}"
    
    # 获取天气数据（只保留每日预报）
    weather_data = await fetch_weather_data(
        coord_data["lat"], 
        coord_data["lon"], 
        exclude="minutely,hourly,alerts"
    )
    
    city_display = f"{coord_data['name']}, {coord_data['country']}"
    
    # 使用通用格式化函数，预报天数通过修改_format_forecast_section传递
    # 临时保存天数到全局变量或通过其他方式传递
    global _forecast_days
    _forecast_days = days
    
    return format_weather_data(weather_data, city_display, "forecast")

@mcp.tool()
async def query_historical_weather(city: str, date: str) -> str:
    """
    查询指定城市的历史天气信息。
    :param city: 城市名称（支持中英文）
    :param date: 日期，格式为 YYYY-MM-DD（例如：2024-01-15）
    :return: 格式化后的历史天气信息
    """
    try:
        # 解析日期并转换为时间戳
        date_obj = datetime.strptime(date, "%Y-%m-%d")
        timestamp = int(date_obj.replace(tzinfo=timezone.utc).timestamp())
        
        # 检查日期是否在允许范围内（过去5天内的数据免费）
        current_time = int(time.time())
        if timestamp > current_time:
            return "⚠️ 不能查询未来的天气数据"
        
        # One Call API 3.0 历史数据有时间限制，免费版只能查询过去5天
        days_ago = (current_time - timestamp) / (24 * 3600)
        if days_ago > 5:
            return f"⚠️ 免费版本只能查询过去5天的历史天气数据，无法查询 {date} 的数据"
        
    except ValueError:
        return "⚠️ 日期格式错误，请使用 YYYY-MM-DD 格式（例如：2024-01-15）"
    
    # 获取经纬度
    coord_data = await get_coordinates(city)
    if "error" in coord_data:
        return f"⚠️ {coord_data['error']}"
    
    # 获取历史天气数据
    weather_data = await fetch_weather_data(
        coord_data["lat"], 
        coord_data["lon"], 
        timestamp
    )
    
    city_display = f"{coord_data['name']}, {coord_data['country']}"
    return format_weather_data(weather_data, city_display, "historical")

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
    # 以标准 I/O 方式运行 MCP 服务器
    mcp.run(transport='stdio')