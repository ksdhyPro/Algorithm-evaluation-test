"""
校验规则模块

包含参赛者结果校验和主办方结果校验的规则定义
"""

try:
    from .participant_rules import validate_participant_output, add_runtime_info as add_participant_runtime
    from .organizer_rules import validate_organizer_results, add_runtime_info as add_organizer_runtime
except ImportError:
    # 在某些环境下可能导入失败，此时直接导入
    from participant_rules import validate_participant_output, add_runtime_info as add_participant_runtime
    from organizer_rules import validate_organizer_results, add_runtime_info as add_organizer_runtime

__all__ = [
    'validate_participant_output', 
    'validate_organizer_results',
    'add_participant_runtime',
    'add_organizer_runtime'
]
