# ------------------ 启动和构建 ------------------

# 构建镜像并启动服务 (后台运行)
# 这是最常用的命令，尤其是在代码更新后
docker compose up --build -d

# 仅启动服务 (如果镜像已是最新)
docker compose up -d

# ------------------ 查看状态 ------------------

# 查看当前目录下服务运行状态
docker compose ps

# 实时查看某个服务的日志
# 按 Ctrl+C 退出日志查看
docker compose logs -f <服务名>
# 示例: docker compose logs -f riichi-seer

# ------------------ 停止和清理 ------------------

# 停止正在运行的服务
docker compose stop

# 停止并移除容器、网络 (不会删除数据库卷或文件)
# 这是彻底关闭服务的标准方式
docker compose down

# ------------------ 清理系统 (谨慎使用!) ------------------

# 清理掉所有未使用的 Docker 资源 (悬空的镜像、网络、构建缓存等)
# 这可以释放大量磁盘空间
docker system prune

# 【警告】清理包括未使用的卷 (可能删除您的数据库!)
# 除非您确认不再需要这些数据，否则不要轻易使用
# docker system prune -a --volumes

# 使用 sed 手动移除 \r
sed -i 's/\r$//' your_script.sh