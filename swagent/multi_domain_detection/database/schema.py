"""
数据库Schema定义
"""

SCHEMA_SQL = """
-- 检测会话表
CREATE TABLE IF NOT EXISTS detection_sessions (
    session_id TEXT PRIMARY KEY,
    region_name TEXT NOT NULL,
    selected_tasks TEXT NOT NULL,  -- JSON格式: ["aerial_waste", "cwld"]
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_images INTEGER DEFAULT 0,
    status TEXT DEFAULT 'running',  -- running, completed, failed
    weather_data TEXT,  -- JSON格式
    completed_at TIMESTAMP
);

-- 图像检测结果表
CREATE TABLE IF NOT EXISTS image_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    image_name TEXT NOT NULL,
    image_path TEXT NOT NULL,
    detection_results TEXT NOT NULL,  -- JSON格式的完整检测结果
    has_target BOOLEAN DEFAULT 0,
    processed_image_path TEXT,  -- SAM2处理后的图像路径
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES detection_sessions(session_id)
);

-- 任务统计表
CREATE TABLE IF NOT EXISTS task_statistics (
    session_id TEXT NOT NULL,
    task_name TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    metric_value TEXT NOT NULL,  -- JSON格式
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (session_id, task_name, metric_name)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_image_results_session
    ON image_results(session_id);

CREATE INDEX IF NOT EXISTS idx_image_results_target
    ON image_results(session_id, has_target);

CREATE INDEX IF NOT EXISTS idx_task_statistics_session
    ON task_statistics(session_id);
"""
