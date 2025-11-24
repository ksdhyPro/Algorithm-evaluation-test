"""
Docker 资源清理工具

定期清理孤立的 Docker 镜像和容器，防止资源泄漏
"""

import docker
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def cleanup_old_images(max_age_hours=24):
    """
    清理超过指定时间的孤立镜像
    
    Args:
        max_age_hours: 镜像年龄阈值（小时）
    """
    try:
        client = docker.from_env()
        now = datetime.utcnow()
        cutoff = now - timedelta(hours=max_age_hours)
        
        removed_count = 0
        for image in client.images.list():
            try:
                # 检查镜像创建时间
                created_str = image.attrs.get('Created', '')
                if created_str:
                    # 处理时间格式
                    created = datetime.fromisoformat(
                        created_str.replace('Z', '+00:00')
                    )
                    
                    # 只删除超期且无标签的镜像
                    if created < cutoff and (not image.tags or '<none>' in str(image.tags)):
                        logger.info(f'Removing old image: {image.short_id}')
                        try:
                            client.images.remove(image.id, force=True)
                            removed_count += 1
                        except Exception as e:
                            logger.warning(f'Failed to remove image {image.short_id}: {e}')
            except Exception as e:
                logger.debug(f'Error processing image: {e}')
        
        if removed_count > 0:
            logger.info(f'Successfully removed {removed_count} old images')
        
    except Exception as e:
        logger.error(f'Cleanup images failed: {e}')


def cleanup_dangling_containers():
    """清理已停止的容器"""
    try:
        client = docker.from_env()
        
        removed_count = 0
        # 移除已停止的容器
        for container in client.containers.list(all=True, filters={'status': 'exited'}):
            try:
                logger.info(f'Removing exited container: {container.short_id}')
                container.remove(force=True)
                removed_count += 1
            except Exception as e:
                logger.warning(f'Failed to remove container: {e}')
        
        if removed_count > 0:
            logger.info(f'Successfully removed {removed_count} exited containers')
                
    except Exception as e:
        logger.error(f'Cleanup containers failed: {e}')


def get_docker_stats():
    """
    获取 Docker 资源统计信息
    
    Returns:
        dict: 包含镜像数、容器数等信息
    """
    try:
        client = docker.from_env()
        
        images = client.images.list()
        containers = client.containers.list(all=True)
        
        return {
            'status': 'ok',
            'images_count': len(images),
            'containers_count': len(containers),
            'running_containers': len(client.containers.list()),
            'dangling_images': len([img for img in images if not img.tags or '<none>' in str(img.tags)])
        }
    except Exception as e:
        logger.error(f'Failed to get Docker stats: {e}')
        return {
            'status': 'error',
            'error': str(e)
        }


def periodic_cleanup(interval_hours=1):
    """
    定期清理任务 - 在后台运行
    
    Args:
        interval_hours: 清理间隔（小时）
    """
    import time
    logger.info(f'Docker cleanup scheduler started (interval: {interval_hours} hours)')
    
    while True:
        try:
            logger.info('Running periodic Docker cleanup...')
            cleanup_old_images()
            cleanup_dangling_containers()
            logger.info('Periodic cleanup completed successfully')
        except Exception as e:
            logger.error(f'Periodic cleanup error: {e}')
        
        # 等待指定时间后再次执行
        time.sleep(interval_hours * 3600)


if __name__ == '__main__':
    # 测试
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    print("Docker 清理工具")
    print("=" * 50)
    
    # 获取统计信息
    stats = get_docker_stats()
    print(f"\nDocker 统计:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # 执行清理
    print("\n开始清理...")
    cleanup_old_images(max_age_hours=24)
    cleanup_dangling_containers()
    print("清理完成！")
