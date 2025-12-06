#!/bin/bash
# 自动分支分离脚本（非交互式）：将 mode1 和 mode2 分离为两个分支
# mode1 -> Web 分支
# mode2 -> main 分支（包含根目录文件：README, .gitignore, LICENSE）

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}分支分离：mode1 -> Web, mode2 -> main${NC}"
echo -e "${BLUE}========================================${NC}"

# 检查是否有未提交的更改
if ! git diff-index --quiet HEAD -- || [ -n "$(git ls-files --others --exclude-standard)" ]; then
    echo -e "${YELLOW}检测到未提交的更改，自动提交...${NC}"
    git add -A
    git commit -m "chore: 分离 mode1 和 mode2 为不同分支" || echo -e "${YELLOW}没有需要提交的更改${NC}"
    echo -e "${GREEN}✓ 更改已提交${NC}"
fi

# 保存当前分支
CURRENT_BRANCH=$(git branch --show-current)
echo -e "${BLUE}当前分支: ${CURRENT_BRANCH}${NC}"

# 1. 创建 Web 分支（基于当前状态）
echo -e "\n${YELLOW}[1/5] 创建 Web 分支...${NC}"
if git show-ref --verify --quiet refs/heads/Web; then
    echo -e "${YELLOW}Web 分支已存在，删除并重新创建...${NC}"
    git branch -D Web 2>/dev/null || true
    git checkout -b Web
    echo -e "${GREEN}✓ Web 分支已重新创建${NC}"
else
    git checkout -b Web
    echo -e "${GREEN}✓ Web 分支已创建${NC}"
fi

# 2. 在 Web 分支上，删除 mode2（只保留 mode1 和根目录文件）
echo -e "\n${YELLOW}[2/5] 在 Web 分支上清理 mode2...${NC}"
if [ -d "mode2" ]; then
    git rm -r mode2
    git commit -m "chore(Web): 移除 mode2，Web 分支只保留 mode1" || true
    echo -e "${GREEN}✓ mode2 已从 Web 分支移除${NC}"
else
    echo -e "${YELLOW}mode2 目录不存在，跳过${NC}"
fi

# 3. 在 Web 分支上，检查根目录文件
echo -e "\n${YELLOW}[3/5] 检查 Web 分支的根目录文件...${NC}"
ROOT_FILES=("README.md" ".gitignore" "LICENSE")
for file in "${ROOT_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓ $file 存在${NC}"
    else
        echo -e "${YELLOW}⚠ $file 不存在（可选）${NC}"
    fi
done

# 4. 切换回 main 分支
echo -e "\n${YELLOW}[4/5] 切换回 main 分支...${NC}"
git checkout main
echo -e "${GREEN}✓ 已切换到 main 分支${NC}"

# 5. 在 main 分支上，删除 mode1（只保留 mode2 和根目录文件）
echo -e "\n${YELLOW}[5/5] 在 main 分支上清理 mode1...${NC}"
if [ -d "mode1" ]; then
    git rm -r mode1
    git commit -m "chore(main): 移除 mode1，main 分支只保留 mode2" || true
    echo -e "${GREEN}✓ mode1 已从 main 分支移除${NC}"
else
    echo -e "${YELLOW}mode1 目录不存在，跳过${NC}"
fi

# 6. 确保 main 分支有根目录文件
echo -e "\n${YELLOW}[6/6] 检查 main 分支的根目录文件...${NC}"
for file in "${ROOT_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓ $file 存在${NC}"
    else
        echo -e "${YELLOW}⚠ $file 不存在${NC}"
    fi
done

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}分支分离完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "\n${CYAN}分支说明：${NC}"
echo -e "  ${BLUE}main${NC} 分支："
echo -e "    - 包含 mode2（原有功能）"
echo -e "    - 包含根目录文件（README.md, .gitignore, LICENSE）"
echo -e "  ${BLUE}Web${NC}  分支："
echo -e "    - 包含 mode1（WebUI 功能）"
echo -e "    - 可能包含根目录文件（可选）"
echo -e "\n${CYAN}切换分支：${NC}"
echo -e "  ${BLUE}git checkout main${NC}  # 切换到 mode2（main 分支）"
echo -e "  ${BLUE}git checkout Web${NC}   # 切换到 mode1（Web 分支）"
echo -e "\n${CYAN}当前分支: ${NC}$(git branch --show-current)"
echo -e "\n${YELLOW}提示：${NC}"
echo -e "  如果需要推送分支到远程："
echo -e "    ${BLUE}git push origin main${NC}"
echo -e "    ${BLUE}git push origin Web${NC}"

