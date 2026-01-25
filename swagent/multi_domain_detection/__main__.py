"""
多领域遥感检测 CLI 入口
"""
import argparse
import asyncio
import sys

from swagent.utils.logger import get_logger
from .runner import run_multi_domain_detection, print_result
from .core import TaskLoader

logger = get_logger(__name__)

# 可用任务列表
AVAILABLE_TASKS = [
    "aerial_waste",           # 航拍废物检测
    "cwld",                   # 建筑垃圾/填埋场
    "landfill",               # 垃圾填埋场
    "solar_photovoltaic_arrays",  # 太阳能光伏阵列
    "tank",                   # 储罐
    "wind_turbines"           # 风力涡轮机
]


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="多领域遥感检测系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
可用任务:
  aerial_waste              航拍废物检测
  cwld                      建筑垃圾/填埋场
  landfill                  垃圾填埋场
  solar_photovoltaic_arrays 太阳能光伏阵列
  tank                      储罐
  wind_turbines             风力涡轮机

示例:
  # 单任务检测
  python -m swagent.multi_domain_detection --mode prod --input ./images --city "北京市" --tasks "aerial_waste"

  # 多任务检测
  python -m swagent.multi_domain_detection --mode prod --input ./images --city "北京市" --tasks "aerial_waste,cwld,landfill"

  # 全部任务
  python -m swagent.multi_domain_detection --mode prod --input ./images --city "北京市" --tasks "all"
        """
    )

    # 基本参数
    parser.add_argument(
        '--mode',
        type=str,
        choices=['test', 'prod'],
        help='运行模式: test(单张图像测试) / prod(批量处理)'
    )

    parser.add_argument(
        '--input',
        type=str,
        help='输入路径: test模式为单张图像，prod模式为图像目录'
    )

    parser.add_argument(
        '--city',
        type=str,
        help='城市名称'
    )

    parser.add_argument(
        '--tasks',
        type=str,
        help='检测任务，逗号分隔。可选: aerial_waste,cwld,landfill,solar_photovoltaic_arrays,tank,wind_turbines 或 "all"'
    )

    parser.add_argument(
        '--output',
        type=str,
        default='./output',
        help='输出目录 (默认: ./output)'
    )

    # 图像处理参数
    parser.add_argument(
        '--tile-size',
        type=int,
        default=512,
        help='切割尺寸 (默认: 512)'
    )

    parser.add_argument(
        '--tile-overlap',
        type=int,
        default=64,
        help='重叠像素 (默认: 64)'
    )

    # 视觉模型参数
    parser.add_argument(
        '--vl-base-url',
        type=str,
        help='视觉模型API地址'
    )

    parser.add_argument(
        '--vl-api-key',
        type=str,
        help='视觉模型API密钥'
    )

    parser.add_argument(
        '--vl-model',
        type=str,
        default='gpt-4o-mini',
        help='视觉模型名称 (默认: gpt-4o-mini)'
    )

    # 文本模型参数
    parser.add_argument(
        '--llm-base-url',
        type=str,
        help='文本模型API地址'
    )

    parser.add_argument(
        '--llm-api-key',
        type=str,
        help='文本模型API密钥'
    )

    parser.add_argument(
        '--llm-model',
        type=str,
        default='gpt-4o-mini',
        help='文本模型名称 (默认: gpt-4o-mini)'
    )

    # 小模型参数
    parser.add_argument(
        '--small-model-url',
        type=str,
        help='小模型(SAM2)API地址'
    )

    parser.add_argument(
        '--small-model-key',
        type=str,
        help='小模型API密钥'
    )

    parser.add_argument(
        '--small-model-name',
        type=str,
        default='sam2_large',
        help='小模型名称 (默认: sam2_large)'
    )

    # 其他参数
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='详细输出'
    )

    parser.add_argument(
        '--list-tasks',
        action='store_true',
        help='列出所有可用任务'
    )

    return parser.parse_args()


def parse_tasks(tasks_str: str) -> list:
    """解析任务字符串"""
    if tasks_str.lower() == "all":
        return AVAILABLE_TASKS.copy()

    tasks = [t.strip() for t in tasks_str.split(',')]

    # 验证任务
    for task in tasks:
        if task not in AVAILABLE_TASKS:
            print(f"错误: 无效任务 '{task}'")
            print(f"可用任务: {', '.join(AVAILABLE_TASKS)}")
            sys.exit(1)

    return tasks


def list_tasks():
    """列出所有可用任务"""
    print("\n可用检测任务:")
    print("-" * 50)

    task_loader = TaskLoader()
    for task_name in AVAILABLE_TASKS:
        task_config = task_loader.get_task(task_name)
        complexity = "简单" if task_config.get("complexity") == "simple" else "复杂"
        print(f"  {task_name:30s} {task_config['name']} ({complexity})")

    print("-" * 50)
    print("\n使用示例:")
    print('  --tasks "aerial_waste"')
    print('  --tasks "aerial_waste,cwld,landfill"')
    print('  --tasks "all"')
    print()


def main():
    """主函数"""
    args = parse_args()

    # 列出任务
    if args.list_tasks:
        list_tasks()
        return

    # 检查必需参数
    if not args.mode or not args.input or not args.city or not args.tasks:
        print("错误: 必须提供 --mode, --input, --city, --tasks 参数")
        print("使用 --help 查看帮助信息")
        print("使用 --list-tasks 查看可用任务")
        sys.exit(1)

    # 解析任务
    tasks = parse_tasks(args.tasks)

    # 打印启动信息
    print("开始多领域遥感检测...")
    print(f"  模式: {args.mode}")
    print(f"  城市: {args.city}")
    print(f"  输入: {args.input}")
    print(f"  输出: {args.output}")
    print(f"  任务: {', '.join(tasks)}")
    print(f"  视觉模型: {args.vl_model}")
    print(f"  文本模型: {args.llm_model}")
    print()

    # 运行检测
    try:
        result = asyncio.run(run_multi_domain_detection(
            mode=args.mode,
            input_path=args.input,
            city=args.city,
            tasks=tasks,
            output_dir=args.output,
            vl_base_url=args.vl_base_url,
            vl_api_key=args.vl_api_key,
            vl_model=args.vl_model,
            llm_base_url=args.llm_base_url,
            llm_api_key=args.llm_api_key,
            llm_model=args.llm_model,
            small_model_url=args.small_model_url,
            small_model_key=args.small_model_key,
            small_model_name=args.small_model_name,
            tile_size=args.tile_size,
            tile_overlap=args.tile_overlap
        ))

        # 打印结果
        print_result(result, args.city, args.mode)

    except KeyboardInterrupt:
        print("\n检测已取消")
        sys.exit(1)
    except Exception as e:
        logger.error(f"检测失败: {e}")
        print(f"\n错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
