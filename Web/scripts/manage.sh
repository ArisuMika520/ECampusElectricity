#!/bin/bash
# 统一脚本管理工具 - 整合所有快速操作

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

# 打印标题
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

# 打印成功消息
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# 打印警告消息
print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# 打印错误消息
print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# 检查命令是否存在
check_command() {
    if ! command -v "$1" &> /dev/null; then
        print_error "未找到 $1"
        return 1
    fi
    return 0
}

# 检查系统依赖
check_dependencies() {
    print_header "检查系统依赖"
    
    local missing=0
    
    if ! check_command python3; then
        missing=1
    else
        print_success "Python: $(python3 --version)"
    fi
    
    if ! check_command node; then
        missing=1
    else
        print_success "Node.js: $(node --version)"
    fi
    
    if ! check_command npm; then
        missing=1
    else
        print_success "npm: $(npm --version)"
    fi
    
    if [ $missing -eq 1 ]; then
        print_error "缺少必要的系统依赖，请先安装"
        exit 1
    fi
    
    if ! python3 -m venv --help &> /dev/null; then
        print_error "缺少 python3-venv，请运行: sudo apt install python3-venv python3-pip"
        exit 1
    fi
}

# 设置后端环境
setup_backend() {
    print_header "设置后端环境"
    
    if [ ! -d "backend/venv" ] || [ ! -f "backend/venv/bin/activate" ]; then
        if [ -d "backend/venv" ]; then
            print_warning "检测到不完整的虚拟环境，正在删除..."
            rm -rf backend/venv
        fi
        
        cd backend
        bash setup.sh
        cd ..
        print_success "后端环境设置完成"
    else
        print_success "后端虚拟环境已存在"
    fi
}

# 设置前端环境
setup_frontend() {
    print_header "设置前端环境"
    
    if [ ! -d "frontend/node_modules" ]; then
        cd frontend
        npm install
        cd ..
        print_success "前端依赖安装完成"
    else
        print_success "前端依赖已安装"
    fi
}

# 安装开发工具
setup_tools() {
    print_header "安装开发工具"
    
    if [ ! -f "node_modules/.bin/concurrently" ]; then
        npm install
        print_success "开发工具安装完成"
    else
        print_success "开发工具已安装"
    fi
}

# 完整环境设置
setup_all() {
    print_header "完整环境设置"
    
    check_dependencies
    setup_backend
    setup_frontend
    setup_tools
    
    print_header "环境设置完成"
    echo -e "\n使用以下命令："
    echo -e "  ${CYAN}./scripts/manage.sh dev${NC}      # 启动开发模式"
    echo -e "  ${CYAN}./scripts/manage.sh start${NC}    # 启动生产模式"
    echo -e "  ${CYAN}./scripts/manage.sh db init${NC}  # 初始化数据库"
}

# 启动开发模式
start_dev() {
    print_header "启动开发模式"
    
    # 检查环境
    if [ ! -d "backend/venv" ]; then
        print_warning "后端环境未设置，正在设置..."
        setup_backend
    fi
    
    if [ ! -d "frontend/node_modules" ]; then
        print_warning "前端依赖未安装，正在安装..."
        setup_frontend
    fi
    
    # 检查数据库
    if [ -d "backend/venv" ]; then
        cd backend
        source venv/bin/activate
        python scripts/check_db.py 2>/dev/null || print_warning "数据库检查失败，请确保数据库已配置"
        cd ..
    fi
    
    echo -e "\n${GREEN}启动服务...${NC}"
    echo -e "${CYAN}后端:${NC} http://localhost:8000"
    echo -e "${CYAN}前端:${NC} http://localhost:3000"
    echo -e "${CYAN}API 文档:${NC} http://localhost:8000/docs"
    echo -e "\n${YELLOW}按 Ctrl+C 停止所有服务${NC}\n"
    
    npx concurrently \
        --names "后端,前端" \
        --prefix-colors "blue,green" \
        "bash -lc 'cd backend && source venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000'" \
        "cd frontend && npm run dev"
}

# 启动生产模式
start_prod() {
    print_header "启动生产模式"
    
    # 检查前端是否已构建
    if [ ! -d "frontend/.next" ]; then
        print_warning "前端未构建，正在构建..."
        cd frontend
        npm run build
        cd ..
        print_success "前端构建完成"
    fi
    
    echo -e "\n${GREEN}启动服务...${NC}"
    
    npx concurrently \
        --names "后端,前端" \
        --prefix-colors "blue,green" \
        "bash -lc 'cd backend && source venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000'" \
        "cd frontend && npm start"
}

# 数据库操作
db_operation() {
    local operation=$1
    
    if [ ! -d "backend/venv" ]; then
        print_error "后端环境未设置，请先运行: ./scripts/manage.sh setup"
        exit 1
    fi
    
    cd backend
    source venv/bin/activate
    
    case "$operation" in
        init)
            print_header "初始化数据库"
            python scripts/init_database.py
            ;;
        check)
            print_header "检查数据库状态"
            python scripts/check_db.py
            ;;
        migrate)
            print_header "数据库迁移（添加管理员字段）"
            python scripts/migrate_add_admin.py
            ;;
        migrate-mode2)
            print_header "从 Bot 版本迁移数据"
            python scripts/migrate_from_mode2.py
            ;;
        *)
            print_error "未知的数据库操作: $operation"
            echo -e "\n可用的数据库操作："
            echo -e "  ${CYAN}init${NC}          # 初始化数据库"
            echo -e "  ${CYAN}check${NC}         # 检查数据库状态"
            echo -e "  ${CYAN}migrate${NC}       # 数据库迁移"
            echo -e "  ${CYAN}migrate-mode2${NC} # 从 Bot 版本迁移数据"
            exit 1
            ;;
    esac
    
    cd ..
}

# 清理操作
clean_operation() {
    local target=$1
    
    case "$target" in
        backend)
            print_header "清理后端环境"
            if [ -d "backend/venv" ]; then
                rm -rf backend/venv
                print_success "后端虚拟环境已删除"
            else
                print_warning "后端虚拟环境不存在"
            fi
            ;;
        frontend)
            print_header "清理前端环境"
            if [ -d "frontend/node_modules" ]; then
                rm -rf frontend/node_modules
                print_success "前端依赖已删除"
            else
                print_warning "前端依赖不存在"
            fi
            if [ -d "frontend/.next" ]; then
                rm -rf frontend/.next
                print_success "前端构建文件已删除"
            fi
            ;;
        all)
            print_header "清理所有环境"
            clean_operation backend
            clean_operation frontend
            if [ -d "node_modules" ]; then
                rm -rf node_modules
                print_success "根目录依赖已删除"
            fi
            ;;
        *)
            print_error "未知的清理目标: $target"
            echo -e "\n可用的清理目标："
            echo -e "  ${CYAN}backend${NC}  # 清理后端环境"
            echo -e "  ${CYAN}frontend${NC} # 清理前端环境"
            echo -e "  ${CYAN}all${NC}      # 清理所有环境"
            exit 1
            ;;
    esac
}

# 显示帮助信息
show_help() {
    print_header "ECampus Electricity - 脚本管理工具"
    
    echo -e "\n${CYAN}使用方法:${NC}"
    echo -e "  ./scripts/manage.sh [命令] [选项]"
    
    echo -e "\n${CYAN}可用命令:${NC}"
    echo -e "  ${GREEN}setup${NC}              # 完整环境设置"
    echo -e "  ${GREEN}dev${NC}                # 启动开发模式（前后端）"
    echo -e "  ${GREEN}start${NC}              # 启动生产模式（前后端）"
    echo -e "  ${GREEN}db <操作>${NC}          # 数据库操作"
    echo -e "  ${GREEN}clean <目标>${NC}       # 清理环境"
    echo -e "  ${GREEN}help${NC}               # 显示帮助信息"
    
    echo -e "\n${CYAN}数据库操作:${NC}"
    echo -e "  ${YELLOW}init${NC}          # 初始化数据库"
    echo -e "  ${YELLOW}check${NC}         # 检查数据库状态"
    echo -e "  ${YELLOW}migrate${NC}       # 数据库迁移（添加管理员字段）"
    echo -e "  ${YELLOW}migrate-mode2${NC} # 从 Bot 版本迁移数据"
    
    echo -e "\n${CYAN}清理目标:${NC}"
    echo -e "  ${YELLOW}backend${NC}  # 清理后端环境"
    echo -e "  ${YELLOW}frontend${NC} # 清理前端环境"
    echo -e "  ${YELLOW}all${NC}      # 清理所有环境"
    
    echo -e "\n${CYAN}示例:${NC}"
    echo -e "  ./scripts/manage.sh setup"
    echo -e "  ./scripts/manage.sh dev"
    echo -e "  ./scripts/manage.sh db init"
    echo -e "  ./scripts/manage.sh clean all"
}

# 主函数
main() {
    local command=$1
    local option=$2
    
    case "$command" in
        setup)
            setup_all
            ;;
        dev)
            start_dev
            ;;
        start)
            start_prod
            ;;
        db)
            if [ -z "$option" ]; then
                print_error "请指定数据库操作"
                db_operation ""
            else
                db_operation "$option"
            fi
            ;;
        clean)
            if [ -z "$option" ]; then
                print_error "请指定清理目标"
                clean_operation ""
            else
                clean_operation "$option"
            fi
            ;;
        help|--help|-h|"")
            show_help
            ;;
        *)
            print_error "未知命令: $command"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# 运行主函数
main "$@"

