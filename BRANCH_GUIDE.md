# 分支开发维护指南

## 分支说明

- **main 分支**：包含 `mode2/`（原有功能，QQ机器人版本）
- **Web 分支**：包含 `mode1/`（WebUI 版本，FastAPI + Next.js）

两个分支完全独立，可以分别开发和维护。

## 基本操作

### 查看当前分支

```bash
git branch
# 当前分支前会有 * 标记
```

### 切换分支

```bash
# 切换到 main 分支（mode2）
git checkout main

# 切换到 Web 分支（mode1）
git checkout Web
```

### 查看分支状态

```bash
# 查看所有分支
git branch -a

# 查看分支的提交历史
git log --oneline --graph --all -10
```

## 日常开发流程

### 在 main 分支开发（mode2）

```bash
# 1. 切换到 main 分支
git checkout main

# 2. 拉取最新代码（如果有远程仓库）
git pull origin main

# 3. 创建功能分支（推荐）
git checkout -b feature/your-feature-name

# 4. 进行开发...

# 5. 提交更改
git add .
git commit -m "feat: 添加新功能"

# 6. 推送到远程（如果需要）
git push origin feature/your-feature-name

# 7. 合并到 main（或创建 Pull Request）
git checkout main
git merge feature/your-feature-name
```

### 在 Web 分支开发（mode1）

```bash
# 1. 切换到 Web 分支
git checkout Web

# 2. 拉取最新代码（如果有远程仓库）
git pull origin Web

# 3. 创建功能分支（推荐）
git checkout -b feature/web-feature-name

# 4. 进行开发...

# 5. 提交更改
git add .
git commit -m "feat: 添加 Web 功能"

# 6. 推送到远程（如果需要）
git push origin feature/web-feature-name

# 7. 合并到 Web（或创建 Pull Request）
git checkout Web
git merge feature/web-feature-name
```

## 推送分支到远程

### 首次推送

```bash
# 推送 main 分支
git checkout main
git push -u origin main

# 推送 Web 分支
git checkout Web
git push -u origin Web
```

### 后续推送

```bash
# 推送当前分支
git push

# 或指定分支
git push origin main
git push origin Web
```

## 从远程拉取更新

```bash
# 拉取 main 分支
git checkout main
git pull origin main

# 拉取 Web 分支
git checkout Web
git pull origin Web
```

## 分支间共享代码（如果需要）

### 方式一：Cherry-pick（推荐）

如果需要在两个分支间共享某个提交：

```bash
# 1. 在源分支找到提交的 hash
git log --oneline

# 2. 切换到目标分支
git checkout target-branch

# 3. Cherry-pick 提交
git cherry-pick <commit-hash>
```

### 方式二：手动复制文件

```bash
# 1. 在源分支查看文件
git checkout source-branch
cat path/to/file

# 2. 切换到目标分支
git checkout target-branch

# 3. 手动复制或创建文件
# 编辑文件...

# 4. 提交
git add .
git commit -m "chore: 从 source-branch 同步文件"
```

## 常见场景

### 场景 1：修复 bug

```bash
# 在 main 分支修复
git checkout main
git checkout -b fix/bug-name
# 修复...
git commit -m "fix: 修复 bug"
git checkout main
git merge fix/bug-name

# 如果 Web 分支也有相同 bug，使用 cherry-pick
git checkout Web
git cherry-pick <commit-hash>
```

### 场景 2：添加新功能

```bash
# 在对应分支开发
git checkout Web  # 或 main
git checkout -b feature/new-feature
# 开发...
git commit -m "feat: 新功能"
git checkout Web  # 或 main
git merge feature/new-feature
```

### 场景 3：查看两个分支的差异

```bash
# 查看文件差异
git diff main..Web -- path/to/file

# 查看提交差异
git log main..Web
git log Web..main
```

## 最佳实践

### 1. 使用功能分支

不要直接在 main 或 Web 分支上开发，创建功能分支：

```bash
git checkout -b feature/your-feature
# 开发...
git checkout main  # 或 Web
git merge feature/your-feature
```

### 2. 提交信息规范

使用清晰的提交信息：

```bash
git commit -m "feat: 添加用户认证功能"
git commit -m "fix: 修复登录问题"
git commit -m "docs: 更新 README"
git commit -m "refactor: 重构代码结构"
```

### 3. 定期同步远程

```bash
# 定期拉取远程更新
git pull origin main
git pull origin Web
```

### 4. 保持分支独立

- main 分支专注于 mode2 的开发
- Web 分支专注于 mode1 的开发
- 避免在两个分支间频繁切换

## 目录结构说明

### main 分支结构

```
ECampusElectricity/
├── README.md          # 项目主 README
├── .gitignore         # Git 忽略文件
├── LICENSE            # 许可证
├── mode2/             # mode2 代码
│   ├── src/
│   ├── scripts/
│   └── ...
├── example/           # 示例文件
└── scripts/           # 工具脚本
```

### Web 分支结构

```
ECampusElectricity/
├── README.md          # 项目主 README（可选）
├── .gitignore         # Git 忽略文件
├── LICENSE            # 许可证
├── mode1/             # mode1 代码
│   ├── backend/       # FastAPI 后端
│   ├── frontend/      # Next.js 前端
│   └── scripts/       # 脚本
└── scripts/           # 工具脚本
```

## 故障排除

### 问题 1：切换分支时提示有未提交的更改

```bash
# 方案 1：提交更改
git add .
git commit -m "WIP: 临时提交"

# 方案 2：暂存更改
git stash
git checkout other-branch
git stash pop  # 恢复更改

# 方案 3：放弃更改（谨慎使用）
git checkout -- .
```

### 问题 2：推送被拒绝

```bash
# 先拉取远程更新
git pull origin branch-name

# 解决冲突后再次推送
git push origin branch-name
```

### 问题 3：误删分支

```bash
# 恢复本地分支
git checkout -b branch-name <commit-hash>

# 从远程恢复
git checkout -b branch-name origin/branch-name
```

## 工作流示例

### 开发 mode2 新功能

```bash
# 1. 切换到 main 分支
git checkout main

# 2. 拉取最新代码
git pull origin main

# 3. 创建功能分支
git checkout -b feature/mode2-new-feature

# 4. 开发...
cd mode2
# 编辑文件...

# 5. 提交
git add .
git commit -m "feat(mode2): 添加新功能"

# 6. 推送到远程
git push origin feature/mode2-new-feature

# 7. 合并到 main（或通过 Pull Request）
git checkout main
git merge feature/mode2-new-feature
git push origin main
```

### 开发 mode1 Web 功能

```bash
# 1. 切换到 Web 分支
git checkout Web

# 2. 拉取最新代码
git pull origin Web

# 3. 创建功能分支
git checkout -b feature/web-new-feature

# 4. 开发...
cd mode1
# 编辑文件...

# 5. 提交
git add .
git commit -m "feat(web): 添加新功能"

# 6. 推送到远程
git push origin feature/web-new-feature

# 7. 合并到 Web（或通过 Pull Request）
git checkout Web
git merge feature/web-new-feature
git push origin Web
```

## 总结

- **main 分支**：独立开发 mode2，不包含 mode1
- **Web 分支**：独立开发 mode1，不包含 mode2
- 两个分支可以并行开发，互不干扰
- 使用功能分支进行开发，保持主分支稳定
- 定期同步远程仓库，保持代码最新

