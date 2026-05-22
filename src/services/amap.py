"""
高德地图 API 服务
用于真实商户数据搜索（美食、景点等）
"""
import httpx
from typing import Optional
from src.config import config


class AmapService:
    """高德地图 API 调用封装"""

    BASE_URL = "https://restapi.amap.com/v3"

    def __init__(self):
        self.key = config.AMAP_KEY

    def search_places(
        self,
        keywords: str,
        city: Optional[str] = None,
        types: Optional[str] = None,
        offset: int = 5,
        page: int = 1,
    ) -> list[dict]:
        """
        搜索地点/商户。

        Args:
            keywords: 搜索关键词（如"川菜"、"火锅"）
            city: 城市名（如"上海"），模糊匹配时可不传
            types: POI 类型代码，如 "050000"（餐饮）
            offset: 每页数量，默认5
            page: 页码，默认1

        Returns:
            [{name, address, location, tel, type, rating}]
        """
        if not self.key:
            return []

        params = {
            "key": self.key,
            "keywords": keywords,
            "offset": offset,
            "page": page,
            "output": "json",
        }
        if city:
            params["city"] = city
        if types:
            params["types"] = types

        try:
            with httpx.Client(timeout=10) as client:
                resp = client.get(f"{self.BASE_URL}/place/text", params=params)
                resp.raise_for_status()
                data = resp.json()

            if data.get("status") != "1" or not data.get("pois"):
                return []

            results = []
            for poi in data["pois"]:
                item = {
                    "name": poi.get("name", ""),
                    "address": poi.get("address", ""),
                    "location": poi.get("location", ""),  # "经度,纬度"
                    "tel": poi.get("tel", ""),
                    "type": poi.get("type", ""),
                    "type_code": poi.get("typecode", ""),
                }
                # 评分：高德没有直接评分字段，用团购/评价数量估算
                # 这里先用 distance 作为排序依据，实际业务中可对接点评数据
                results.append(item)

            return results

        except Exception as e:
            print(f"[AmapService] search error: {e}")
            return []

    def search_restaurants(
        self,
        keywords: str,
        city: Optional[str] = None,
        offset: int = 5,
    ) -> list[dict]:
        """
        搜索餐饮商户（类型码 050000）
        """
        # 餐饮类型码
        return self.search_places(
            keywords=keywords,
            city=city,
            types="050000",
            offset=offset,
        )

    def search_attractions(
        self,
        keywords: str,
        city: Optional[str] = None,
        offset: int = 5,
    ) -> list[dict]:
        """
        搜索景点（景区类型码 110000）
        keywords: 搜索词（景点名、或"景点""景区"等通用词）
        city: 城市名，为空时用 keywords 做全网搜索
        """
        return self.search_places(
            keywords=keywords,
            city=city,
            types="110000",
            offset=offset,
        )

    def geocode(self, address: str, city: Optional[str] = None) -> Optional[dict]:
        """
        地址 → 经纬度
        Returns: {"lng": ..., "lat": ...}
        """
        if not self.key:
            return None

        params = {"key": self.key, "address": address, "output": "json"}
        if city:
            params["city"] = city

        try:
            with httpx.Client(timeout=10) as client:
                resp = client.get(f"{self.BASE_URL}/geocode/regeo", params=params)
                resp.raise_for_status()
                data = resp.json()

            if data.get("status") == "1" and data.get("regeocode"):
                loc = data["regeocode"]["addressComponent"]
                # 返回结构化地址信息
                return {
                    "province": loc.get("province", ""),
                    "city": loc.get("city", ""),
                    "district": loc.get("district", ""),
                }
            return None
        except Exception as e:
            print(f"[AmapService] geocode error: {e}")
            return None
    def resolve_city(self, city_name: str) -> tuple[Optional[str], Optional[str]]:
        """
        将任意城市名解析为(城市名, adcode)。
        优先用 geocode（地址→坐标），失败后用 place/text（关键词→POI的adcode）。
        Returns: (resolved_city_name, adcode) 或 (None, None)
        """
        if not self.key or not city_name:
            return None, None

        # 策略1：geocode（适合有明确行政区划结构的城市）
        try:
            params = {"key": self.key, "address": city_name, "output": "json"}
            with httpx.Client(timeout=10) as client:
                resp = client.get(f"{self.BASE_URL}/geocode/regeo", params=params)
                resp.raise_for_status()
                data = resp.json()
            if data.get("status") == "1" and data.get("regeocode"):
                comp = data["regeocode"].get("addressComponent", {})
                resolved_city = comp.get("province", "")
                city_list = comp.get("city", [])
                if city_list:
                    resolved_city = city_list[0]
                elif comp.get("province"):
                    resolved_city = comp.get("province", "")
                adcode = data["regeocode"].get("adcode", "")
                if resolved_city and adcode:
                    return resolved_city, adcode
        except Exception as e:
            print(f"[AmapService] resolve_city geocode error: {e}")

        # 策略2：place/text 搜索城市名本身（返回POI的adcode）
        try:
            params = {
                "key": self.key,
                "keywords": city_name,
                "types": "150000",  # 城市级别 type
                "offset": 1,
                "page": 1,
                "output": "json",
            }
            with httpx.Client(timeout=10) as client:
                resp = client.get(f"{self.BASE_URL}/place/text", params=params)
                resp.raise_for_status()
                data = resp.json()
            if data.get("status") == "1" and data.get("pois"):
                first = data["pois"][0]
                adcode = first.get("adcode", "")
                name = first.get("name", "")
                # 取 city 字段作为城市名
                return name, adcode
        except Exception as e:
            print(f"[AmapService] resolve_city place error: {e}")

        return None, None

    def get_route(
        self,
        origin: str,  # "lng,lat" 或 地址
        destination: str,  # "lng,lat" 或 地址
        city: Optional[str] = None,
        mode: str = "walking",  # walking | transit | driving
    ) -> Optional[dict]:
        """
        路线规划：步行/公交/驾车
        mode: walking / transit / driving
        Returns: 路线描述文本，失败返回 None
        """
        if not self.key:
            return None

        if mode == "transit":
            path = "/v3/direction/transit"
            params = {
                "key": self.key,
                "origin": origin,
                "destination": destination,
                "city": city or "全国",
            }
        elif mode == "driving":
            path = "/v3/direction/driving"
            params = {
                "key": self.key,
                "origin": origin,
                "destination": destination,
            }
        else:  # walking
            path = "/v3/direction/walking"
            params = {
                "key": self.key,
                "origin": origin,
                "destination": destination,
            }

        try:
            with httpx.Client(timeout=10) as client:
                resp = client.get(f"{self.BASE_URL}{path}", params=params)
                resp.raise_for_status()
                data = resp.json()

            if data.get("status") != "1":
                return None

            if mode == "transit":
                return self._parse_transit(data)
            elif mode == "driving":
                return self._parse_driving(data)
            else:
                return self._parse_walking(data)

        except Exception as e:
            print(f"[AmapService] route error ({mode}): {e}")
            return None

    def _parse_walking(self, data: dict) -> Optional[dict]:
        # v3 API: 结构是 {"route": {"paths": [...]}}
        route = data.get("route", {})
        paths = route.get("paths", [])
        if not paths:
            return None
        step = paths[0]
        distance = int(step.get("distance", 0))
        duration = int(step.get("duration", 0))
        return {
            "distance": f"{distance}米",
            "duration": f"{int(duration // 60)}分钟",
            "strategy": "步行",
        }

    def _parse_driving(self, data: dict) -> Optional[dict]:
        route = data.get("route", {})
        paths = route.get("paths", [])
        if not paths:
            return None
        step = paths[0]
        distance = int(step.get("distance", 0))
        duration = int(step.get("duration", 0))
        steps = step.get("steps", [])
        first_advice = steps[0].get("instruction", "") if steps else ""
        return {
            "distance": f"{distance // 1000}公里",
            "duration": f"{int(duration // 60)}分钟",
            "strategy": "驾车",
            "first_advice": first_advice,
        }

    def _parse_transit(self, data: dict) -> Optional[dict]:
        route = data.get("route", {})
        transits = route.get("transits", [])
        if not transits:
            return None

        best = transits[0]
        total_duration = int(best.get("duration", 0))
        total_distance = int(best.get("distance", 0))
        segments = best.get("segments", [])

        parts = []
        for seg in segments:
            w = seg.get("walking", {})
            if w:
                w_dist = int(w.get("distance", 0))
                if w_dist > 30:
                    parts.append(f"步行{w_dist}米")
            bus = seg.get("bus", {})
            if bus:
                lines = bus.get("buslines", [])
                if lines:
                    line = lines[0]
                    seg_name = line.get("name", "")
                    stops = line.get("stop_num", "")
                    parts.append(f"乘坐{seg_name}（{stops}站）")

        summary = " → ".join(parts) if parts else str(best.get("first_line", ""))
        return {
            "distance": f"{total_distance // 1000}公里",
            "duration": f"{int(total_duration // 60)}分钟",
            "strategy": "公交/地铁",
            "route": summary,
        }
