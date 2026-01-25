# 多领域遥感检测系统

## 概述

多领域遥感检测系统支持6大类遥感图像检测任务，采用分层调用策略和鲁棒解析机制，确保检测的可靠性和效率。

## 支持的任务

| 任务ID | 任务名称 | 复杂度 | 描述 |
|--------|----------|--------|------|
| aerial_waste | 航拍废物检测 | 简单 | 检测航拍图像中的废物堆放情况 |
| cwld | 建筑垃圾/填埋场 | 复杂 | 检测建筑垃圾和填埋场区域 |
| landfill | 垃圾填埋场 | 简单 | 检测和分析垃圾填埋场 |
| solar_photovoltaic_arrays | 太阳能光伏阵列 | 复杂 | 检测太阳能光伏板和阵列 |
| tank | 储罐 | 复杂 | 检测各类储罐 |
| wind_turbines | 风力涡轮机 | 复杂 | 检测风力涡轮机 |

## 核心特性

### 1. 分层调用策略
- **简单任务**（aerial_waste, landfill）：合并调用，节省成本
- **复杂任务**（cwld, solar_photovoltaic_arrays, tank, wind_turbines）：单独调用，保证质量

### 2. 鲁棒解析机制
- 5种解析策略：标准JSON、代码块提取、think标签处理、文本提取、降级处理
- 容错机制：单任务失败不影响其他任务
- 自动标记需要人工审核的结果

### 3. 上下文优化
- SQLite数据库存储完整检测结果
- 内存中维护统计汇总
- LLM只接收汇总数据（~6K tokens vs 50K+）

### 4. 完整报告
- 多任务检测结果汇总
- 天气信息集成
- 10张样例图片前后对比
- LLM智能分析

## 使用方法

### 查看可用任务
```bash
python -m swagent.multi_domain_detection --list-tasks
```

### 单任务检测
```bash
python -m swagent.multi_domain_detection \
    --mode prod \
    --input /path/to/images \
    --city "北京市" \
    --tasks "aerial_waste" \
    --vl-base-url "https://api.example.com/v1" \
    --vl-api-key "sk-xxx" \
    --vl-model "gpt-4o-mini" \
    --llm-base-url "https://api.example.com/v1" \
    --llm-api-key "sk-xxx" \
    --llm-model "gpt-4o-mini" \
    --small-model-url "https://sam2.example.com" \
    --small-model-name "sam2_large"
```

### 多任务检测
```bash
python -m swagent.multi_domain_detection \
    --mode prod \
    --input /path/to/images \
    --city "北京市" \
    --tasks "aerial_waste,cwld,landfill" \
    ...
```

### 全部任务检测
```bash
python -m swagent.multi_domain_detection \
    --mode prod \
    --input /path/to/images \
    --city "北京市" \
    --tasks "all" \
    ...
```

## 文件结构

```
swagent/multi_domain_detection/
├── __init__.py              # 模块初始化
├── __main__.py              # CLI入口
├── runner.py                # 主运行器
├── workflow.py              # 工作流（检测+SAM2处理）
├── config/
│   └── task_prompts.yaml    # 6大类任务prompt配置
├── core/
│   ├── __init__.py
│   ├── task_loader.py       # 任务配置加载器
│   └── prompt_builder.py    # Prompt动态构建器
├── database/
│   ├── __init__.py
│   ├── schema.py            # 数据库表结构
│   └── db_manager.py        # 数据库管理器
├── report/
│   ├── __init__.py
│   └── generator.py         # 报告生成器
└── utils/
    ├── __init__.py
    └── result_parser.py     # 鲁棒结果解析器
```

## 数据流

```
图片输入
    ↓
┌─────────────────────────────────┐
│  分层调用VL模型                  │
│  - 简单任务合并调用              │
│  - 复杂任务单独调用              │
└─────────────────────────────────┘
    ↓
┌─────────────────────────────────┐
│  鲁棒解析                        │
│  - 5种解析策略                   │
│  - 容错处理                      │
└─────────────────────────────────┘
    ↓
┌─────────────────────────────────┐
│  SAM2处理                        │
│  - 提取所有boundingbox           │
│  - 生成标注图像                  │
└─────────────────────────────────┘
    ↓
┌─────────────────────────────────┐
│  数据存储                        │
│  - SQLite存储完整结果            │
│  - 内存统计汇总                  │
└─────────────────────────────────┘
    ↓
┌─────────────────────────────────┐
│  报告生成                        │
│  - 多任务结果汇总                │
│  - 天气信息                      │
│  - 10张样例展示                  │
│  - LLM智能分析                   │
└─────────────────────────────────┘
    ↓
Markdown报告输出
```

## 输出示例

### 报告结构
```markdown
# 多领域遥感检测综合报告 - 北京市

## 执行摘要
- 检测任务：航拍废物检测、建筑垃圾/填埋场
- 图像总数：100张
- 检测时间：2026-01-25

## 监测期间天气状况
| 项目 | 数值 |
|------|------|
| 温度 | 25.0 °C |
| 湿度 | 60 % |

## 航拍废物检测结果
- 检测图像数：100
- 检测到目标：15
- 检出率：15.00%

## 建筑垃圾/填埋场结果
- 检测图像数：100
- 检测到目标：8
- 检出率：8.00%

## 样例展示
（10张图片前后对比）

## 智能分析
（LLM生成的专业分析）

## 附录
（处理日志、错误记录）
```

## 依赖

- Python 3.8+
- PyYAML
- SQLite3（内置）
- swagent.waste_monitoring（复用LLM检测器和SAM2处理器）
- swagent.tools.domain（天气和位置工具）
