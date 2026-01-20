import requests
import json
import urllib.parse

def get_location_by_address(address, key, city=None):
    """
    调用高德地图地理编码 API，将地址转换为经纬度。
    
    :param address: 结构化地址信息（必填）
    :param key: 高德 Web 服务 Key（必填）
    :param city: 指定查询的城市（可选）
    :return: 成功返回 (lng, lat) 元组，失败返回 None
    """
    base_url = "https://restapi.amap.com/v3/geocode/geo"
    
    # 构造参数
    params = {
        "key": key,
        "address": address,
        "output": "JSON"
    }
    if city:
        params["city"] = city
        
    try:
        # 发送请求
        response = requests.get(base_url, params=params)
        response.raise_for_status() # 检查 HTTP 状态码
        
        data = response.json()
        
        # 检查 API 返回状态
        if data.get("status") == "1":
            geocodes = data.get("geocodes")
            if geocodes and len(geocodes) > 0:
                # 获取第一个匹配结果的 location
                location_str = geocodes[0].get("location")
                if location_str:
                    lng, lat = location_str.split(",")
                    return float(lng), float(lat)
            else:
                print(f"未找到地址 '{address}' 的编码信息。")
        else:
            print(f"API 请求失败: {data.get('info')}")
            
    except requests.exceptions.RequestException as e:
        print(f"网络请求错误: {e}")
    except Exception as e:
        print(f"处理错误: {e}")
        
    return None

if __name__ == "__main__":
    # ================= 配置区域 =================
    # 请替换为你自己的高德 Web 服务 Key
    AMAP_KEY = "51e748084f28af808466fd0c42a37302" 
    
    # 要转换的地址列表
    addresses = [
        "北京市朝阳区阜通东大街6号",
        "清华大学",
        "上海市东方明珠",
        "深圳市南山区粤海街道"
    ]
    # ===========================================

    if AMAP_KEY == "你的高德Key":
        print("请先在代码中填入你的高德 Key！")
        exit(1)

    print(f"{'地址':<20} | {'经度':<10} | {'纬度':<10}")
    print("-" * 50)
    
    for addr in addresses:
        result = get_location_by_address(addr, AMAP_KEY)
        if result:
            lng, lat = result
            print(f"{addr:<20} | {lng:<10.6f} | {lat:<10.6f}")
        else:
            print(f"{addr:<20} | {'获取失败':<10} | {'获取失败':<10}")
