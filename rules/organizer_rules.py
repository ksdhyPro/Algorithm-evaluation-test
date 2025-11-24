"""
主办方结果校验规则

定义主办方镜像输出的校验规则
"""


class OrganizerValidationError(Exception):
    """主办方校验错误"""
    pass


def validate_organizer_results(result_json_path):
    """
    校验主办方的 results.json 文件
    
    Args:
        result_json_path (str): results.json 文件路径
        
    Returns:
        dict: 验证后的结果对象
        
    Raises:
        OrganizerValidationError: 校验失败时抛出
        FileNotFoundError: 文件不存在时抛出
    """
    import json
    import os
    
    if not os.path.exists(result_json_path):
        raise FileNotFoundError(f"主办方结果文件不存在: {result_json_path}")
    
    try:
        with open(result_json_path, 'r', encoding='utf-8') as f:
            results = json.load(f)
    except json.JSONDecodeError as e:
        raise OrganizerValidationError(f"主办方 results.json 格式错误: {str(e)}")
    
    # 校验规则
    # 1. 必须是字典
    if not isinstance(results, dict):
        raise OrganizerValidationError("主办方输出必须是 JSON 对象")
    
    # 2. 必须包含 indicator 键（可选，根据实际需求调整）
    if 'indicator' not in results:
        raise OrganizerValidationError("主办方结果必须包含 'indicator' 字段")
    
    # 3. 如果包含 indicator，则必须是数组
    if 'indicator' in results:
        indicator_value = results['indicator']
        if not isinstance(indicator_value, list):
            raise OrganizerValidationError(
                f"indicator 字段必须是数组，当前类型: {type(indicator_value).__name__}"
            )
    
    # 添加更多校验规则...
    # 例如: 检查必要的字段、数据类型等
    
    return results


def add_runtime_info(result_obj, participant_metrics, participant_runtime, debug=False):
    """
    为主办方结果添加运行时信息
    
    Args:
        result_obj (dict): 主办方结果对象
        participant_metrics (dict): 容器运行指标 {'cpu_peak': ..., 'memory_peak': ...}
        participant_runtime (float): 运行时间（秒）
        debug (bool): 是否启用调试输出
        
    Returns:
        dict: 添加了 runtimeInfo 的结果对象
    """
    import os
    
    # 检查环境变量是否启用调试
    if not debug:
        debug = os.environ.get('METRICS_DEBUG', '').lower() == 'true'
    
    if debug:
        print(f"[RUNTIME_INFO] 原始指标: {participant_metrics}")
        print(f"[RUNTIME_INFO] 运行时间: {participant_runtime}s")
    
    cpu_peak = float(participant_metrics.get('cpu_peak', 0))
    memory_peak = float(participant_metrics.get('memory_peak', 0))
    
    if debug:
        print(f"[RUNTIME_INFO] 提取的值 - CPU: {cpu_peak}, Memory: {memory_peak}")
    
    runtime_info = {
        'cpu': cpu_peak,
        'memory': memory_peak,
        'runtime': float(participant_runtime)
    }
    result_obj['runtimeInfo'] = runtime_info
    
    if debug:
        print(f"[RUNTIME_INFO] 最终 runtimeInfo: {runtime_info}")
    
    return result_obj
