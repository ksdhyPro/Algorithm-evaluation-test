"""
校验规则模块使用指南

此模块包含参赛者和主办方的结果校验规则，方便后续维护和调整。
"""

## 目录结构

```
rules/
├── __init__.py                 # 模块入口
├── participant_rules.py        # 参赛者输出结果校验规则
├── organizer_rules.py          # 主办方输出结果校验规则
└── README.md                   # 本文件
```

## 使用方法

### 参赛者结果校验

```python
from rules.participant_rules import validate_participant_output, add_runtime_info

# 校验参赛者的 results.json
try:
    results = validate_participant_output('/path/to/results.json')

    # 添加运行时信息
    metrics = {'cpu_peak': 0.5, 'memory_peak': 256}
    results = add_runtime_info(results, metrics, runtime=2.5)

except FileNotFoundError:
    print("结果文件不存在")
except ParticipantValidationError as e:
    print(f"校验失败: {str(e)}")
```

### 主办方结果校验

```python
from rules.organizer_rules import validate_organizer_results, add_runtime_info

# 校验主办方的 results.json
try:
    results = validate_organizer_results('/path/to/results.json')

    # 添加运行时信息
    metrics = {'cpu_peak': 0.5, 'memory_peak': 256}
    results = add_runtime_info(results, metrics, runtime=5.0)

except FileNotFoundError:
    print("结果文件不存在")
except OrganizerValidationError as e:
    print(f"校验失败: {str(e)}")
```

## 修改校验规则

### 参赛者结果校验规则

编辑 `participant_rules.py` 中的 `validate_participant_output()` 函数：

```python
def validate_participant_output(result_json_path):
    # ... 读取文件 ...

    # 添加你的校验逻辑
    if not some_condition:
        raise ParticipantValidationError("错误描述")

    return results
```

### 主办方结果校验规则

编辑 `organizer_rules.py` 中的 `validate_organizer_results()` 函数：

```python
def validate_organizer_results(result_json_path):
    # ... 读取文件 ...

    # 添加你的校验逻辑
    if not some_condition:
        raise OrganizerValidationError("错误描述")

    return results
```

## 默认校验规则

### 参赛者规则

1. results.json 必须是有效的 JSON 格式
2. 必须是一个 JSON 对象（dict）
3. 可以包含任意字段（灵活设计）

### 主办方规则

1. results.json 必须是有效的 JSON 格式
2. 必须是一个 JSON 对象（dict）
3. 如果包含 `indicator` 字段，则必须是数组
4. 其他字段灵活处理

## 添加自定义校验

如需添加特定的校验规则，只需在对应的函数中添加条件即可：

```python
# 在 validate_organizer_results 中添加
if 'score' in results:
    score = results['score']
    if not (0 <= score <= 100):
        raise OrganizerValidationError("score 必须在 0-100 之间")
```

## 异常处理

- `ParticipantValidationError`: 参赛者结果校验异常
- `OrganizerValidationError`: 主办方结果校验异常
- `FileNotFoundError`: 结果文件不存在异常

## 运行时信息字段

`add_runtime_info()` 会为结果添加 `runtimeInfo` 字段，包含：

```json
{
  "score": 100,
  "runtimeInfo": {
    "cpu": 0.5, // CPU 峰值使用率 (%)
    "memory": 256, // 内存峰值使用 (MB)
    "runtime": 2.5 // 运行时间 (秒)
  }
}
```
