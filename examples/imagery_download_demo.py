"""
影像下载示例：将卫星影像保存到本地文件夹

演示如何使用 ImageryTool 下载并保存卫星影像到本地
"""
import asyncio
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from swagent.tools.domain import ImageryTool


async def example_save_google_earth():
    """示例 1: 下载 Google Earth 影像并保存"""
    print("\n" + "="*60)
    print("示例 1: 下载 Google Earth 影像到本地")
    print("="*60)

    imagery = ImageryTool()

    # 北京天安门坐标
    location = [116.397, 39.908]

    print(f"\n下载位置: 北京天安门 {location}")
    print("数据源: Google Earth")
    print("分辨率: Zoom 18 (约 0.6米/像素)")
    print("大小: 1000x1000 像素\n")

    result = await imagery.safe_execute(
        location=location,
        source="google",
        zoom_level=18,
        point_size=1000,
        return_format="file",  # 保存到文件
        output_path="./satellite_images",
        filename="beijing_tiananmen_google.png"
    )

    if result.success:
        print(f"✅ 成功!")
        print(f"   保存路径: {result.data['saved_path']}")
        print(f"   影像尺寸: {result.data['shape'][0]}x{result.data['shape'][1]} 像素")
    else:
        print(f"❌ 失败: {result.error}")


async def example_save_jilin():
    """示例 2: 下载吉林一号影像并保存"""
    print("\n" + "="*60)
    print("示例 2: 下载吉林一号影像到本地")
    print("="*60)

    imagery = ImageryTool()

    # 北京区域
    location = [116.35, 39.85, 116.45, 39.95]

    print(f"\n下载区域: 北京 {location}")
    print("数据源: 吉林一号")
    print("年份: 2024")
    print("分辨率: Zoom 17\n")

    result = await imagery.safe_execute(
        location=location,
        source="jilin",
        zoom_level=17,
        year=2024,
        return_format="file",
        output_path="./satellite_images",
        filename="beijing_area_jilin_2024.png"
    )

    if result.success:
        print(f"✅ 成功!")
        print(f"   保存路径: {result.data['saved_path']}")
        print(f"   影像尺寸: {result.data['shape'][0]}x{result.data['shape'][1]} 像素")
    else:
        print(f"❌ 失败: {result.error}")


async def example_auto_filename():
    """示例 3: 自动生成文件名"""
    print("\n" + "="*60)
    print("示例 3: 自动生成文件名")
    print("="*60)

    imagery = ImageryTool()

    location = [121.473, 31.230]  # 上海

    print(f"\n下载位置: 上海 {location}")
    print("文件名: 自动生成\n")

    result = await imagery.safe_execute(
        location=location,
        source="google",
        zoom_level=18,
        point_size=1000,
        return_format="file",
        output_path="./satellite_images"
        # 未指定 filename，将自动生成
    )

    if result.success:
        print(f"✅ 成功!")
        print(f"   自动生成的文件名: {result.data['filename']}")
        print(f"   完整路径: {result.data['saved_path']}")
    else:
        print(f"❌ 失败: {result.error}")


async def example_batch_download():
    """示例 4: 批量下载多个位置"""
    print("\n" + "="*60)
    print("示例 4: 批量下载多个城市的卫星影像")
    print("="*60)

    imagery = ImageryTool()

    # 定义多个城市坐标
    cities = [
        {"name": "北京", "location": [116.397, 39.908]},
        {"name": "上海", "location": [121.473, 31.230]},
        {"name": "广州", "location": [113.264, 23.129]},
        {"name": "深圳", "location": [114.057, 22.543]}
    ]

    print(f"\n准备下载 {len(cities)} 个城市的影像...\n")

    for city in cities:
        print(f"正在下载: {city['name']}...")

        result = await imagery.safe_execute(
            location=city['location'],
            source="google",
            zoom_level=18,
            point_size=800,
            return_format="file",
            output_path="./satellite_images/cities",
            filename=f"{city['name']}_satellite.png"
        )

        if result.success:
            print(f"  ✅ {city['name']} 下载成功")
        else:
            print(f"  ❌ {city['name']} 下载失败: {result.error}")

    print(f"\n所有城市下载完成!")
    print(f"保存目录: ./satellite_images/cities/")


async def example_different_formats():
    """示例 5: 保存为不同格式"""
    print("\n" + "="*60)
    print("示例 5: 保存为不同图像格式")
    print("="*60)

    imagery = ImageryTool()

    location = [116.397, 39.908]  # 北京
    formats = ["png", "jpg", "tiff"]

    print(f"\n将同一影像保存为不同格式...\n")

    for fmt in formats:
        print(f"保存为 {fmt.upper()} 格式...")

        result = await imagery.safe_execute(
            location=location,
            source="google",
            zoom_level=18,
            point_size=500,
            return_format="file",
            output_path="./satellite_images/formats",
            filename=f"beijing_satellite.{fmt}"
        )

        if result.success:
            # 获取文件大小
            file_size = os.path.getsize(result.data['saved_path'])
            print(f"  ✅ 保存成功 - 文件大小: {file_size / 1024:.1f} KB")
        else:
            print(f"  ❌ 失败: {result.error}")


async def main():
    """运行所有示例"""
    print("\n" + "🛰️ "*30)
    print(" 卫星影像下载示例")
    print("🛰️ "*30)

    print("\n提示: 影像下载需要网络连接和依赖包支持")
    print("      如果遇到错误，请检查:")
    print("      1. 网络连接")
    print("      2. 依赖包: pip install mercantile")
    print("      3. 数据接口文件是否存在\n")

    # 运行所有示例
    await example_save_google_earth()
    await example_save_jilin()
    await example_auto_filename()
    await example_batch_download()
    await example_different_formats()

    print("\n" + "="*60)
    print("所有示例完成!")
    print("="*60)

    # 检查并显示已下载的文件
    if os.path.exists("./satellite_images"):
        print("\n已下载的文件:")
        for root, dirs, files in os.walk("./satellite_images"):
            for file in files:
                filepath = os.path.join(root, file)
                size = os.path.getsize(filepath)
                print(f"  📄 {filepath} ({size / 1024:.1f} KB)")


if __name__ == "__main__":
    asyncio.run(main())
