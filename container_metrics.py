"""
容器资源指标收集模块（轻量级版本）

收集参赛者容器的 CPU、内存使用情况
"""

import docker
import time
import threading
from typing import Dict, List, Optional
import os

# 检查是否启用调试模式
DEBUG_MODE = os.environ.get('METRICS_DEBUG', '').lower() == 'true'


class ContainerMetricsCollector:
    """容器资源指标收集器"""
    
    def __init__(self, container_id: str, collection_interval: float = 0.5):
        """
        初始化收集器
        
        Args:
            container_id: Docker 容器 ID
            collection_interval: 数据收集间隔（秒），默认 0.5 秒
        """
        self.container_id = container_id
        self.collection_interval = collection_interval
        self.metrics: List[Dict] = []
        self.running = False
        self.lock = threading.Lock()
        self.client = docker.from_env()
        
    def start_collection(self):
        """启动后台指标收集线程"""
        self.running = True
        self.thread = threading.Thread(target=self._collect_metrics_loop, daemon=True)
        self.thread.start()
        # 给收集器一点时间启动
        time.sleep(0.1)
        return self.thread
    
    def stop_collection(self):
        """停止指标收集"""
        self.running = False
        # 等待线程结束，给它时间完成最后的采样
        if hasattr(self, 'thread'):
            self.thread.join(timeout=2)
    
    def _collect_metrics_loop(self):
        """后台循环收集指标"""
        try:
            container = self.client.containers.get(self.container_id)
            first_stats = None
            sample_count = 0
            
            if DEBUG_MODE:
                print(f"[METRICS] 开始采集容器 {self.container_id[:12]}")
            
            while self.running:
                try:
                    # 获取容器统计信息
                    stats = container.stats(stream=False)
                    
                    # 对于快速完成的容器，尽量采集第一个有效样本
                    # 只在获取到足够的 CPU 增量时才跳过
                    if first_stats is None:
                        first_cpu = stats.get('cpu_stats', {}).get('cpu_usage', {}).get('total_usage', 0)
                        
                        # 如果第一次采样就有 CPU 使用，直接使用
                        if first_cpu > 0:
                            if DEBUG_MODE:
                                print(f"[METRICS] 第一次采样有效，直接记录 (CPU usage: {first_cpu})")
                            first_stats = stats
                            # 继续处理这个样本
                        else:
                            # 如果第一次采样没有 CPU 使用，保存并等待下一次
                            if DEBUG_MODE:
                                print(f"[METRICS] 第一次采样 CPU 为 0，等待下一次采样")
                            first_stats = stats
                            time.sleep(self.collection_interval)
                            continue
                    
                    # 解析 CPU 使用率
                    cpu_percent = self._calculate_cpu_percent(stats)
                    
                    # 解析内存使用量（单位：MB）
                    memory_usage = stats['memory_stats'].get('usage', 0)
                    memory_usage_mb = memory_usage / 1024 / 1024
                    
                    # 记录指标
                    metric_data = {
                        'cpu_percent': cpu_percent,
                        'memory_mb': memory_usage_mb,
                    }
                    
                    if DEBUG_MODE:
                        print(f"[METRICS] 采样 {sample_count+1}: CPU={cpu_percent:.2f}%, MEM={memory_usage_mb:.2f}MB")
                    
                    with self.lock:
                        self.metrics.append(metric_data)
                    
                    sample_count += 1
                    time.sleep(self.collection_interval)
                    
                except docker.errors.NotFound:
                    if DEBUG_MODE:
                        print(f"[METRICS] 容器已删除")
                    break
                except Exception as e:
                    if DEBUG_MODE:
                        print(f"[METRICS] 采集异常: {type(e).__name__}: {e}")
                    time.sleep(self.collection_interval)
                    
        except Exception as e:
            if DEBUG_MODE:
                print(f"[METRICS] 采集线程异常: {e}")
            pass
    
    def _calculate_cpu_percent(self, stats: Dict) -> float:
        """
        计算 CPU 使用百分比
        
        Args:
            stats: 容器统计数据
            
        Returns:
            CPU 使用百分比
        """
        try:
            cpu_stats = stats.get('cpu_stats', {})
            precpu_stats = stats.get('precpu_stats', {})
            
            # 获取 CPU 相关数据
            cpu_usage = cpu_stats.get('cpu_usage', {}).get('total_usage', 0)
            precpu_usage = precpu_stats.get('cpu_usage', {}).get('total_usage', 0)
            system_cpu = cpu_stats.get('system_cpu_usage', 0)
            presystem_cpu = precpu_stats.get('system_cpu_usage', 0)
            
            cpu_delta = cpu_usage - precpu_usage
            system_delta = system_cpu - presystem_cpu
            
            if system_delta == 0 or cpu_delta == 0:
                return 0.0
            
            # 获取 CPU 核心数
            cpu_count = len(cpu_stats.get('cpus', []))
            if cpu_count == 0:
                # 尝试从其他字段获取
                cpu_count = cpu_stats.get('online_cpus', 1)
                if cpu_count == 0:
                    cpu_count = 1
            
            # 计算百分比
            cpu_percent = (cpu_delta / system_delta) * cpu_count * 100.0
            return max(0, min(cpu_percent, 100 * cpu_count))  # 限制范围
            
        except Exception as e:
            return 0.0
    
    def get_summary(self) -> Dict:
        """
        获取收集到的指标统计摘要
        
        Returns:
            包含峰值的统计数据字典
        """
        with self.lock:
            if DEBUG_MODE:
                print(f"[METRICS] 总共采集到 {len(self.metrics)} 个样本")
                if self.metrics:
                    print(f"[METRICS] 样本数据: {self.metrics[:5]}")  # 打印前5个样本
            
            if not self.metrics:
                if DEBUG_MODE:
                    print(f"[METRICS] 没有采集到任何数据，返回默认值")
                return {
                    'cpu_peak': 0,
                    'memory_peak': 0,
                }
            
            # 提取 CPU 和内存数据
            cpu_data = [m['cpu_percent'] for m in self.metrics]
            mem_data = [m['memory_mb'] for m in self.metrics]
            
            # 对于容器运行时间很短的情况，不过滤数据
            # 因为即使是 0 也是有效的结果
            if len(self.metrics) < 2:
                # 样本少于 2 个，直接返回采集到的数据
                cpu_peak = max(cpu_data) if cpu_data else 0
                mem_peak = max(mem_data) if mem_data else 0
            else:
                # 样本充足，可以过滤掉初始化阶段的 0 值
                cpu_data_filtered = [c for c in cpu_data if c > 0]
                mem_data_filtered = [m for m in mem_data if m > 0]
                
                # 返回峰值，如果过滤后有数据则用过滤后的，否则用原始数据
                cpu_peak = max(cpu_data_filtered) if cpu_data_filtered else max(cpu_data)
                mem_peak = max(mem_data_filtered) if mem_data_filtered else max(mem_data)
            
            if DEBUG_MODE:
                print(f"[METRICS] 样本数: {len(self.metrics)}")
                print(f"[METRICS] CPU数据: {cpu_data}")
                print(f"[METRICS] CPU峰值: {cpu_peak}")
                print(f"[METRICS] 内存数据: {mem_data}")
                print(f"[METRICS] 内存峰值: {mem_peak}")
            
            return {
                'cpu_peak': round(cpu_peak, 2),
                'memory_peak': round(mem_peak, 2),
            }
