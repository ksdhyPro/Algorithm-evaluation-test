"""
参赛者输出结果校验规则

定义参赛者镜像输出的校验规则
"""


class ParticipantValidationError(Exception):
    """参赛者校验错误"""
    pass


def validate_participant_output(result_json_path):
    """
    校验参赛者的 results.json 文件
    
    Args:
        result_json_path (str): results.json 文件路径
        
    Returns:
        dict: 验证后的结果对象
        
    Raises:
        ParticipantValidationError: 校验失败时抛出
        FileNotFoundError: 文件不存在时抛出
    """
    import json
    import os
    
    if not os.path.exists(result_json_path):
        raise FileNotFoundError(f"参赛者结果文件不存在: {result_json_path}")
    
    try:
        with open(result_json_path, 'r', encoding='utf-8') as f:
            results = json.load(f)
    except json.JSONDecodeError as e:
        raise ParticipantValidationError(f"参赛者 results.json 格式错误: {str(e)}")
    
    # 校验规则
    if not isinstance(results, dict):
        raise ParticipantValidationError("参赛者输出必须是 JSON 对象")
    
    # 添加更多校验规则...
    # 例如: 检查必要的字段、数据类型等
    
    return results


def add_runtime_info(result_obj, participant_metrics, participant_runtime):
    """
    为参赛者结果添加运行时信息
    
    Args:
        result_obj (dict): 参赛者结果对象
        participant_metrics (dict): 容器运行指标 {'cpu_peak': ..., 'memory_peak': ...}
        participant_runtime (float): 运行时间（秒）
        
    Returns:
        dict: 添加了 runtimeInfo 的结果对象
    """
    runtime_info = {
        'cpu': float(participant_metrics.get('cpu_peak', 0)),
        'memory': float(participant_metrics.get('memory_peak', 0)),
        'runtime': float(participant_runtime)
    }
    result_obj['runtimeInfo'] = runtime_info
    return result_obj
