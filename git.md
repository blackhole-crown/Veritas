# Git 完全指南手册

## 📖 目录
- [快速开始](#快速开始)
- [安装与配置](#安装与配置)
- [基础操作](#基础操作)
- [分支管理](#分支管理)
- [远程仓库](#远程仓库)
- [撤销操作](#撤销操作)
- [高级功能](#高级功能)
- [团队协作](#团队协作)
- [最佳实践](#最佳实践)
- [故障排除](#故障排除)

## 🚀 快速开始

### 初始化仓库
```bash
# 初始化新仓库
git init

# 克隆现有仓库
git clone <仓库URL>

# 示例
git clone git@github.com:username/repo.git
git clone https://github.com/username/repo.git
```

### 首次提交工作流
```bash
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin <远程仓库URL>
git push -u origin main
```

## ⚙️ 安装与配置

### 安装 Git
```bash
# Ubuntu/Debian
sudo apt-get install git

# CentOS/RHEL
sudo yum install git

# macOS
brew install git

# Windows
# 下载 Git for Windows: https://git-scm.com/download/win
```

### 基础配置
```bash
# 设置用户名和邮箱
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# 设置默认编辑器
git config --global core.editor "code --wait"  # VS Code
git config --global core.editor "vim"          # Vim
git config --global core.editor "nano"         # Nano

# 设置默认分支名
git config --global init.defaultBranch main

# 启用彩色输出
git config --global color.ui auto
```

### SSH 密钥配置
```bash
# 生成 SSH 密钥
ssh-keygen -t ed25519 -C "your.email@example.com"

# 或使用 RSA
ssh-keygen -t rsa -b 4096 -C "your.email@example.com"

# 添加到 ssh-agent
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519

# 复制公钥
cat ~/.ssh/id_ed25519.pub
# 添加到 GitHub/GitLab 的 SSH Keys 设置
```

## 📝 基础操作

### 文件状态管理
```bash
# 查看状态
git status
git status -s  # 简洁模式

# 添加文件
git add <文件名>        # 添加特定文件
git add .              # 添加所有更改
git add *.py           # 添加所有 .py 文件
git add src/           # 添加目录

# 查看更改
git diff               # 查看未暂存更改
git diff --staged      # 查看已暂存更改
git diff HEAD          # 查看所有更改
```

### 提交管理
```bash
# 提交更改
git commit -m "提交信息"
git commit -am "提交信息"  # 添加并提交所有跟踪文件

# 修改上次提交
git commit --amend -m "新的提交信息"
git commit --amend --no-edit  # 只修改内容，不修改信息

# 查看提交历史
git log
git log --oneline      # 简洁模式
git log --graph        # 图形化显示
git log --stat         # 显示文件更改统计
git log -p             # 显示具体更改内容
git log --since="2 weeks ago"
```

## 🌿 分支管理

### 分支操作
```bash
# 查看分支
git branch              # 本地分支
git branch -a           # 所有分支（含远程）
git branch -v           # 带最后提交信息

# 创建分支
git branch <分支名>
git checkout -b <分支名>  # 创建并切换

# 切换分支
git checkout <分支名>
git switch <分支名>      # Git 2.23+

# 重命名分支
git branch -m <新分支名>          # 当前分支
git branch -m <旧名> <新名>       # 指定分支

# 删除分支
git branch -d <分支名>           # 安全删除
git branch -D <分支名>           # 强制删除
```

### 合并与变基
```bash
# 合并分支
git checkout main
git merge <分支名>

# 变基（保持线性历史）
git checkout feature
git rebase main
git checkout main
git merge feature

# 解决冲突后继续
git add <冲突文件>
git merge --continue   # 或 git rebase --continue

# 取消合并/变基
git merge --abort
git rebase --abort
```

## 🌐 远程仓库

### 远程操作
```bash
# 查看远程仓库
git remote -v

# 添加远程仓库
git remote add origin <URL>

# 修改远程URL
git remote set-url origin <新URL>

# 移除远程仓库
git remote remove origin

# 抓取远程更新
git fetch origin
git fetch --all

# 拉取远程分支
git pull origin main
git pull --rebase origin main  # 变基式拉取

# 推送到远程
git push origin main
git push -u origin main        # 设置上游分支
git push origin --delete <分支名>  # 删除远程分支
```

### 远程分支管理
```bash
# 跟踪远程分支
git checkout -b <本地分支名> origin/<远程分支名>
git branch -u origin/<分支名>  # 设置跟踪关系

# 清理远程分支引用
git fetch --prune

# 查看远程分支详情
git remote show origin
```

## ↩️ 撤销操作

### 工作区撤销
```bash
# 丢弃工作区更改（未暂存）
git checkout -- <文件名>
git restore <文件名>      # Git 2.23+

# 丢弃所有工作区更改
git checkout -- .
git restore .            # Git 2.23+

# 取消暂存（已add）
git reset HEAD <文件名>
git restore --staged <文件名>  # Git 2.23+
```

### 提交撤销
```bash
# 撤销上一次提交（保留更改）
git reset --soft HEAD~1

# 撤销上一次提交（不保留更改）
git reset --hard HEAD~1

# 撤销到指定提交
git reset --hard <commit-hash>

# 创建撤销提交
git revert <commit-hash>

# 查看引用日志（找回删除的提交）
git reflog
```

### 暂存区管理
```bash
# 临时保存更改
git stash
git stash push -m "保存信息"

# 查看保存列表
git stash list

# 恢复保存
git stash pop          # 恢复并删除
git stash apply        # 恢复但不删除

# 删除保存
git stash drop stash@{0}
git stash clear        # 清除所有
```

## 🔧 高级功能

### 标签管理
```bash
# 创建标签
git tag v1.0.0
git tag -a v1.0.0 -m "版本说明"

# 查看标签
git tag
git tag -l "v1.*"      # 过滤标签

# 推送标签
git push origin v1.0.0
git push origin --tags  # 推送所有标签

# 删除标签
git tag -d v1.0.0
git push origin --delete v1.0.0
```

### 子模块
```bash
# 添加子模块
git submodule add <仓库URL> <路径>

# 克隆包含子模块的仓库
git clone --recursive <仓库URL>

# 或克隆后初始化
git submodule init
git submodule update

# 更新子模块
git submodule update --remote
```

### 配置文件
```bash
# 查看配置
git config --list
git config --global --list

# 编辑配置
git config --global --edit

# 常用配置项
git config --global alias.co checkout
git config --global alias.br branch
git config --global alias.ci commit
git config --global alias.st status
git config --global alias.lg "log --oneline --graph --all"
git config --global core.autocrlf input  # Linux/Mac
git config --global core.autocrlf true   # Windows
```

## 👥 团队协作

### 协作工作流
```bash
# Fork 工作流
1. Fork 仓库
2. git clone 你的 fork
3. git remote add upstream 原始仓库URL
4. git fetch upstream
5. git merge upstream/main
6. 创建功能分支
7. 开发、提交、推送
8. 创建 Pull Request

# 功能分支工作流
git checkout -b feature/new-feature
# 开发...
git add .
git commit -m "Add new feature"
git push origin feature/new-feature
# 创建 Pull Request/Merge Request
```

### 代码审查
```bash
# 查看他人更改
git fetch origin
git checkout -b review-feature origin/feature-branch

# 比较分支
git diff main..feature-branch
git log --oneline main..feature-branch

# 整理提交历史
git rebase -i HEAD~3  # 交互式变基
```

## 📊 最佳实践

### 提交规范
```markdown
# 提交信息格式
<类型>: <描述>

# 类型说明
feat:     新功能
fix:      修复bug
docs:     文档更新
style:    代码格式调整
refactor: 代码重构
test:     测试相关
chore:    构建过程或辅助工具变动

# 示例
feat: 添加用户登录功能
fix: 修复首页加载异常
docs: 更新API文档
```

### .gitignore 模板
```gitignore
# 依赖目录
node_modules/
vendor/
__pycache__/
*.pyc

# 环境文件
.env
.env.local
.env.*.local

# 编辑器文件
.vscode/
.idea/
*.swp
*.swo

# 系统文件
.DS_Store
Thumbs.db

# 日志文件
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# 构建产物
dist/
build/
*.exe
*.dll

# 临时文件
*.tmp
*.temp
```

### 分支命名规范
```bash
# 功能分支
feature/user-auth
feature/add-payment

# 修复分支
fix/login-bug
fix/header-styling

# 发布分支
release/v1.2.0
release/2024-01-update

# 热修复分支
hotfix/critical-bug
hotfix/security-patch
```

## 🚨 故障排除

### 常见问题
```bash
# 1. 推送被拒绝
git pull --rebase origin main
git push origin main

# 2. 忘记提交信息
git commit --amend

# 3. 提交到错误分支
git reset --soft HEAD~1
git stash
git checkout correct-branch
git stash pop
git add .
git commit -m "正确的提交"

# 4. 误删分支
git reflog
git checkout -b <分支名> <commit-hash>

# 5. 大文件提交错误
git filter-branch --tree-filter 'rm -f <大文件>' HEAD
git push origin --force --all
```

### 调试命令
```bash
# 查看详细日志
git log --pretty=fuller

# 查看文件历史
git blame <文件名>

# 查找引入bug的提交
git bisect start
git bisect bad
git bisect good <之前的提交>
# 测试后标记 good/bad
git bisect reset

# 检查仓库健康
git fsck
git gc --prune=now
```

### 性能优化
```bash
# 清理仓库
git gc --aggressive --prune=now

# 压缩仓库
git repack -a -d --depth=250 --window=250

# 浅克隆（大仓库）
git clone --depth=1 <仓库URL>

# 部分克隆（Git 2.19+）
git clone --filter=blob:none <仓库URL>
```

## 📚 学习资源

### 官方文档
- [Pro Git 书籍](https://git-scm.com/book/zh/v2) - 官方中文文档
- [Git 官方文档](https://git-scm.com/docs)

### 图形化工具
- **GitHub Desktop** - 适合初学者
- **SourceTree** - 功能全面的免费工具
- **GitKraken** - 优秀的跨平台工具
- **VS Code Git 集成** - 开发者的好帮手

### 在线学习
- [Learn Git Branching](https://learngitbranching.js.org/) - 交互式学习
- [GitHub Learning Lab](https://lab.github.com/) - 实践课程

---

## 📄 许可证

本手册采用 CC BY-SA 4.0 许可证。你可以自由地：
- 分享 — 在任何媒介以任何形式复制、发行本作品
- 演绎 — 修改、转换或以本作品为基础进行创作

---

**版本:** 1.0.0  
**更新日期:** 2026年2月10日  
**维护者:** [周泽辉]

