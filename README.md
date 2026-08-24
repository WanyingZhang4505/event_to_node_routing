# 1. Clone Repo to Scratch/alicezh

在 Trillium 集群上把 GitHub 仓库克隆到自己的 scratch 目录,并配置好认证、提交、推送。

## 1.1 进入 scratch 目录并克隆仓库

```bash
cd /scratch/alicezh
git clone https://github.com/WanyingZhang4505/event_to_node_routing.git routing
cd routing
```

## 1.2 配置 git 身份(提交时显示的作者信息)

```bash
git config --global user.name "alicezh"
git config --global user.email "wanying.zhang@mail.utoronto.ca"
```

> 注意:这里只影响提交记录里显示的作者,和推送时用哪个 GitHub 账号认证无关。
> `--global` 只写入你自己家目录的 `~/.gitconfig`,不会影响集群上其他用户。

## 1.3 认证(关键)

GitHub 从 2021 年起不再支持用登录密码做 git 操作,必须用 **Personal Access Token (PAT)**。

**生成 token:**

1. 用有该仓库写权限的账号(`WanyingZhang4505`)登录 GitHub
2. 打开 [https://github.com/settings/tokens](https://github.com/settings/tokens) → Generate new token (classic)
3. 勾选 `repo` 权限,生成后复制 token(形如 `ghp_xxx`,只显示一次)

**确认远程地址带上正确的用户名:**

```bash
git remote set-url origin https://WanyingZhang4505@github.com/WanyingZhang4505/event_to_node_routing.git
```

> 踩过的坑:如果机器上缓存/填成了别的账号(如 `alice330000`),而它对仓库没有写权限,push 会报 `403 Permission denied`。用上面的命令指定正确用户名即可。

## 1.4 让机器记住 token(一劳永逸)

Trillium 是远程共享集群,没有浏览器 SSO / 系统钥匙串,默认每次 push 都要输 token。开启凭据存储只需一次:

```bash
git config --global credential.helper store
```

下次 push 时输入一次用户名 + token,凭据会保存在 `~/.git-credentials`,以后自动认证。

> 更安全的替代方案是用 SSH 密钥:`ssh-keygen -t ed25519` 生成后,把 `~/.ssh/id_ed25519.pub` 加到 [https://github.com/settings/keys](https://github.com/settings/keys),再把 remote 换成 `git@github.com:WanyingZhang4505/event_to_node_routing.git`,之后完全免 token。

## 1.5 提交并推送改动

```bash
git status                      # 查看改动
git add <file>                  # 暂存
git commit -m "your message"    # 提交(注意是 commit,不是 command)
git push                        # 推送
```

首次 push 输入用户名(`WanyingZhang4505`)和 token(当密码);之后因为已开启 `credential.helper store`,会自动认证。

## 1.6 以后手动切换账号 / 更新 token

**换成别的账号:**

```bash
git remote set-url origin https://新账号名@github.com/仓库拥有者/仓库名.git
rm ~/.git-credentials
git push
```

**只换 token(账号不变):**

```bash
rm ~/.git-credentials
git push
```

## 常见报错速查

| 报错 | 原因 | 解决 |
| --- | --- | --- |
| `Permission ... denied to <account>` (403) | 认证账号对仓库无写权限 | `git remote set-url` 指定正确账号,或让 owner 加你为 collaborator |
| `Password authentication is not supported` | 密码框里填了登录密码 | 改填 Personal Access Token |
| `could not read Password ... No such device` | 在非交互终端里 push 需要输密码 | 在自己的交互终端里执行,或先设置 `credential.helper store` |
| `git: 'command' is not a git command` | 命令打错了 | 是 `git commit`,不是 `git command` |
