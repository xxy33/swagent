"""
城市固废智能监测系统 - 命令行入口
"""
import argparse
import asyncio
import sys
from pathlib import Path

from .state import RunMode
from .runner import run_waste_monitoring, MonitoringResult


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="城市固废智能监测系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:

  # 测试模式 - 切割大图后处理
  python -m swagent.waste_monitoring --mode test --input /path/to/large_image.tif --city "北京市" --tile-size 512

  # 生产模式 - 处理已切割的小图
  python -m swagent.waste_monitoring --mode prod --input /path/to/tiles_dir/ --city "北京市"

更多信息请访问项目文档。
        """
    )

    parser.add_argument(
        "--mode", "-m",
        type=str,
        choices=["test", "prod"],
        required=True,
        help="运行模式: test (测试模式-大图切割) 或 prod (生产模式-小图目录)"
    )

    parser.add_argument(
        "--input", "-i",
        type=str,
        required=True,
        help="输入路径: 测试模式为大图路径，生产模式为小图目录"
    )

    parser.add_argument(
        "--city", "-c",
        type=str,
        required=True,
        help="城市名称，如: 北京市、上海市"
    )

    parser.add_argument(
        "--output", "-o",
        type=str,
        default="./output",
        help="输出目录 (默认: ./output)"
    )

    parser.add_argument(
        "--tile-size",
        type=int,
        default=512,
        help="切割尺寸，仅测试模式有效 (默认: 512)"
    )

    parser.add_argument(
        "--tile-overlap",
        type=int,
        default=64,
        help="切割重叠像素，仅测试模式有效 (默认: 64)"
    )

    parser.add_argument(
        "--max-iterations",
        type=int,
        default=10000,
        help="最大迭代次数 (默认: 10000)"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="输出详细日志"
    )

    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="静默模式，只输出最终结果"
    )

    # 视觉模型配置 (用于图像检测)
    parser.add_argument(
        "--vl-base-url",
        type=str,
        default=None,
        help="视觉模型API地址 (用于图像检测)"
    )

    parser.add_argument(
        "--vl-api-key",
        type=str,
        default=None,
        help="视觉模型API密钥"
    )

    parser.add_argument(
        "--vl-model",
        type=str,
        default=None,
        help="视觉模型名称 (如 wuyu-vl-8b)"
    )

    # 文本模型配置 (用于报告生成)
    parser.add_argument(
        "--llm-base-url",
        type=str,
        default=None,
        help="文本模型API地址 (用于报告生成)"
    )

    parser.add_argument(
        "--llm-api-key",
        type=str,
        default=None,
        help="文本模型API密钥"
    )

    parser.add_argument(
        "--llm-model",
        type=str,
        default=None,
        help="文本模型名称 (如 wuyu-30b)"
    )

    # 小模型配置
    parser.add_argument(
        "--small-model-url",
        type=str,
        default=None,
        help="小模型API地址"
    )

    parser.add_argument(
        "--small-model-key",
        type=str,
        default=None,
        help="小模型API密钥"
    )

    parser.add_argument(
        "--small-model-name",
        type=str,
        default=None,
        help="小模型名称"
    )

    return parser.parse_args()


def print_result(result: MonitoringResult):
    """打印执行结果"""
    print("\n" + "=" * 60)
    print("固废监测执行结果")
    print("=" * 60)

    status = "✓ 成功" if result.success else "✗ 失败"
    print(f"\n状态: {status}")
    print(f"城市: {result.city_name}")
    print(f"模式: {result.mode}")

    print(f"\n--- 检测统计 ---")
    print(f"总图块数:     {result.total_tiles}")
    print(f"垃圾堆存点:   {result.waste_count}")
    print(f"清洁区域:     {result.clean_count}")
    print(f"检测失败:     {result.error_count}")
    print(f"检出率:       {result.detection_rate:.2%}")

    if result.report_path:
        print(f"\n报告路径: {result.report_path}")

    if result.errors:
        print(f"\n--- 错误信息 ({len(result.errors)}) ---")
        for err in result.errors[:5]:
            print(f"  - {err}")
        if len(result.errors) > 5:
            print(f"  ... 共 {len(result.errors)} 个错误")

    print("\n" + "=" * 60)


async def main_async(args):
    """异步主函数"""
    # 验证输入
    input_path = Path(args.input)

    if args.mode == "test":
        if not input_path.is_file():
            print(f"错误: 测试模式需要大图文件，但未找到: {args.input}")
            sys.exit(1)
    else:
        if not input_path.is_dir():
            print(f"错误: 生产模式需要小图目录，但未找到: {args.input}")
            sys.exit(1)

    # 执行监测
    if not args.quiet:
        print(f"开始固废监测...")
        print(f"  模式: {args.mode}")
        print(f"  城市: {args.city}")
        print(f"  输入: {args.input}")
        print(f"  输出: {args.output}")
        if args.mode == "test":
            print(f"  切割尺寸: {args.tile_size}x{args.tile_size}")
            print(f"  重叠像素: {args.tile_overlap}")
        if args.vl_model:
            print(f"  视觉模型: {args.vl_model}")
        if args.llm_model:
            print(f"  文本模型: {args.llm_model}")
        print()

    result = await run_waste_monitoring(
        mode=RunMode(args.mode),
        input_path=args.input,
        city_name=args.city,
        output_dir=args.output,
        tile_size=args.tile_size,
        tile_overlap=args.tile_overlap,
        max_iterations=args.max_iterations,
        verbose=args.verbose,
        # 视觉模型配置
        vl_base_url=args.vl_base_url,
        vl_api_key=args.vl_api_key,
        vl_model=args.vl_model,
        # 文本模型配置
        llm_base_url=args.llm_base_url,
        llm_api_key=args.llm_api_key,
        llm_model=args.llm_model,
        # 小模型配置
        small_model_api_url=args.small_model_url,
        small_model_api_key=args.small_model_key,
        small_model_name=args.small_model_name
    )

    print_result(result)

    return 0 if result.success else 1


def main():
    """主入口"""
    args = parse_args()

    try:
        exit_code = asyncio.run(main_async(args))
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n用户中断")
        sys.exit(130)
    except Exception as e:
        print(f"\n执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
