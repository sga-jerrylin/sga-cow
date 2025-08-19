#!/bin/bash

# SGA-CoW Docker部署脚本
# 使用方法: ./docker-deploy.sh [start|stop|restart|logs|build]

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目信息
PROJECT_NAME="sga-cow"
CONTAINER_NAME="sga-cow"
IMAGE_NAME="sga-cow:latest"

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查Docker是否安装
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装，请先安装Docker"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose未安装，请先安装Docker Compose"
        exit 1
    fi
}

# 检查配置文件
check_config() {
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            log_warning ".env文件不存在，正在从.env.example复制..."
            cp .env.example .env
            log_warning "请编辑.env文件，填入正确的配置信息"
            return 1
        else
            log_error ".env.example文件不存在，无法创建配置文件"
            exit 1
        fi
    fi
    
    # 检查必要的环境变量
    source .env
    if [ -z "$DIFY_API_KEY" ] || [ "$DIFY_API_KEY" = "your-dify-api-key-here" ]; then
        log_error "请在.env文件中设置正确的DIFY_API_KEY"
        return 1
    fi
    
    if [ -z "$WECHATCOM_CORP_ID" ] || [ "$WECHATCOM_CORP_ID" = "your-corp-id-here" ]; then
        log_error "请在.env文件中设置正确的企业微信配置"
        return 1
    fi
    
    return 0
}

# 构建镜像
build_image() {
    log_info "开始构建Docker镜像..."
    docker build -t $IMAGE_NAME .
    log_success "Docker镜像构建完成"
}

# 启动服务
start_service() {
    log_info "启动SGA-CoW服务..."
    
    # 检查配置
    if ! check_config; then
        log_error "配置检查失败，请修正配置后重试"
        exit 1
    fi
    
    # 使用docker-compose启动
    if command -v docker-compose &> /dev/null; then
        docker-compose up -d
    else
        docker compose up -d
    fi
    
    log_success "SGA-CoW服务启动成功"
    log_info "容器状态:"
    docker ps | grep $CONTAINER_NAME
    
    log_info "查看日志: ./docker-deploy.sh logs"
    log_info "Web界面: http://localhost:9899"
}

# 停止服务
stop_service() {
    log_info "停止SGA-CoW服务..."
    
    if command -v docker-compose &> /dev/null; then
        docker-compose down
    else
        docker compose down
    fi
    
    log_success "SGA-CoW服务已停止"
}

# 重启服务
restart_service() {
    log_info "重启SGA-CoW服务..."
    stop_service
    sleep 2
    start_service
}

# 查看日志
show_logs() {
    if [ -z "$2" ]; then
        # 显示最近100行日志
        docker logs --tail 100 -f $CONTAINER_NAME
    else
        # 显示指定行数的日志
        docker logs --tail $2 -f $CONTAINER_NAME
    fi
}

# 进入容器
enter_container() {
    log_info "进入SGA-CoW容器..."
    docker exec -it $CONTAINER_NAME /bin/bash
}

# 查看状态
show_status() {
    log_info "SGA-CoW服务状态:"
    docker ps | grep $CONTAINER_NAME || log_warning "容器未运行"
    
    log_info "镜像信息:"
    docker images | grep sga-cow || log_warning "镜像不存在"
    
    log_info "资源使用:"
    docker stats --no-stream $CONTAINER_NAME 2>/dev/null || log_warning "无法获取资源使用情况"
}

# 清理资源
cleanup() {
    log_info "清理SGA-CoW相关资源..."
    
    # 停止并删除容器
    docker stop $CONTAINER_NAME 2>/dev/null || true
    docker rm $CONTAINER_NAME 2>/dev/null || true
    
    # 删除镜像
    docker rmi $IMAGE_NAME 2>/dev/null || true
    
    # 清理未使用的资源
    docker system prune -f
    
    log_success "资源清理完成"
}

# 显示帮助信息
show_help() {
    echo "SGA-CoW Docker部署脚本"
    echo ""
    echo "使用方法:"
    echo "  $0 [命令]"
    echo ""
    echo "可用命令:"
    echo "  build     构建Docker镜像"
    echo "  start     启动服务"
    echo "  stop      停止服务"
    echo "  restart   重启服务"
    echo "  logs      查看日志 (可选参数: 行数)"
    echo "  status    查看服务状态"
    echo "  enter     进入容器"
    echo "  cleanup   清理所有资源"
    echo "  help      显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 start          # 启动服务"
    echo "  $0 logs 50        # 查看最近50行日志"
    echo "  $0 restart        # 重启服务"
}

# 主函数
main() {
    # 检查Docker环境
    check_docker
    
    case "${1:-help}" in
        "build")
            build_image
            ;;
        "start")
            start_service
            ;;
        "stop")
            stop_service
            ;;
        "restart")
            restart_service
            ;;
        "logs")
            show_logs $@
            ;;
        "status")
            show_status
            ;;
        "enter")
            enter_container
            ;;
        "cleanup")
            cleanup
            ;;
        "help"|*)
            show_help
            ;;
    esac
}

# 执行主函数
main $@
