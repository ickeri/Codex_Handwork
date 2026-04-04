# Codex Handwork

一个基于 PySide6 的桌面工具，用于串联邮箱生成、认证 URL 获取、验证码轮询、认证状态查询和账号数量统计流程。

## 项目结构

```text
Codex_Handwork/
├── data/                     # 运行时数据
│   └── email_counter.json
├── gui.py                    # 主启动入口
├── pyproject.toml            # 项目元数据
├── requirements.txt          # 依赖列表
├── settings.json             # 项目配置（包含敏感信息，不应提交）
└── src/
    └── codex_handwork/
        ├── app.py            # 应用启动逻辑
        ├── gui.py            # 主窗口实现
        ├── settings.py       # settings.json 加载逻辑
        ├── assets/           # 静态资源
        └── services/         # 业务模块
```

## 安装依赖

```bash
python3 -m pip install -r requirements.txt
```

## 启动方式

```bash
python3 gui.py
```

## 主要模块

- `src/codex_handwork/gui.py`：主窗口与流程控制
- `src/codex_handwork/services/email_store.py`：邮箱编号持久化
- `src/codex_handwork/services/mail.py`：邮件与验证码查询
- `src/codex_handwork/services/oauth.py`：认证 URL 获取
- `src/codex_handwork/services/status.py`：认证状态查询
- `src/codex_handwork/services/count.py`：账号数量统计

## 数据说明

- `data/email_counter.json`：记录已分配到的邮箱编号
- `src/codex_handwork/assets/background.png`：主界面背景图
- `src/codex_handwork/assets/app_icon.png`：程序图标，同时也作为当前配置弹窗背景图
- `settings.json`：统一配置文件，包含 GUI 参数、邮件接口、本地管理接口、邮箱生成规则，以及认证信息

## 页面展示

### 主页

![主页](src/codex_handwork/assets/homepage.png)

### 配置页

![配置页](src/codex_handwork/assets/deploy.png)

## 配置按钮

主界面底部与账号数量同一行新增了 `配置` 按钮。

点击后会弹出配置表单，可直接修改以下内容：

- 默认密码
- 邮件列表接口地址
- 邮件接口 `authorization`
- CPA 接口基础地址（只填 `127.0.0.1:8317` 这种 `host:port`）
- CPA 接口 `Authorization` 的 `Bearer ` 后半段
- 邮箱前缀
- 邮箱域名

保存后会立即写回 `settings.json`，后续再次点击 `开始` 时会直接使用新配置，不需要重启程序。

## 自动复制说明

程序会自动把关键内容写入剪贴板：

- 成功获取认证 URL 后，会自动复制 URL
- 成功监听到当前邮箱的验证码后，会自动复制验证码

这样可以减少手动复制操作。

## settings.json 说明

首次使用时，可以先把 `settings_example.json` 复制成 `settings.json`：

```bash
cp settings_example.json settings.json
```

复制后，把 `settings_example.json` 里标注“需要你自己填写”的内容改成你自己的真实配置即可。

`settings.json` 主要分为四组。

示例：

```json
{
  "gui": {
    "window_title": "Codex Handwork",
    "default_password": "qwe123123123",
    "callback_port": 1455,
    "nickname_length": 6,
    "status_message_timeout_ms": 2000,
    "auth_poll_interval_ms": 3000,
    "code_poll_interval_seconds": 7,
    "account_count_refresh_delay_ms": 3000,
    "next_round_delay_ms": 5000
  },
  "mail": {
    "url": "https://example.com/api/allEmail/list",
    "authorization": "eyJ....",
    "request_timeout_seconds": 30,
    "params": {
      "emailId": 0,
      "size": 50,
      "timeSort": 0,
      "type": "receive",
      "searchType": "name"
    },
    "headers": {
      "accept": "application/json, text/plain, */*",
      "referer": "https://example.com/all-mail",
      "user-agent": "Mozilla/5.0"
    }
  },
  "oauth": {
    "base_address": "127.0.0.1:8317",
    "authorization_suffix": "CPA密码",
    "request_timeout_seconds": 30,
    "auth_url_params": {
      "is_webui": "true"
    },
    "headers": {
      "Accept": "application/json, text/plain, */*",
      "User-Agent": "Mozilla/5.0"
    }
  },
  "email": {
    "prefix": "test",
    "domain": "@example.com",
    "min_index": 1,
    "max_index": 99999
  }
}
```

实际项目中的 `settings.json` 还包含若干 `*_comment` 字段，用来说明每个配置项的作用；上面的示例只保留核心字段，便于快速理解结构。

### 1. `gui`

界面行为相关配置：

- `window_title`：主窗口标题
- `default_password`：主界面默认填入的密码
- `callback_port`：开始流程前会尝试释放的本地端口
- `nickname_length`：自动生成昵称的长度
- `status_message_timeout_ms`：短提示显示时长
- `auth_poll_interval_ms`：认证状态轮询间隔
- `code_poll_interval_seconds`：验证码轮询间隔
- `account_count_refresh_delay_ms`：注册成功后刷新账号数量前的等待时间
- `next_round_delay_ms`：循环执行模式下下一轮开始前的等待时间

### 2. `mail`

邮件接口相关配置：

- `url`：邮件列表接口地址
- `authorization`：邮件接口请求头中的 `authorization` 值
- `request_timeout_seconds`：请求超时秒数
- `params`：请求邮件列表时附带的查询参数
- `headers`：除 `authorization` 外的静态请求头

说明：程序运行时会把 `mail.authorization` 动态写入请求头，不需要手动再去 `headers` 里改。

### 3. `oauth`

本地 CPA 管理接口相关配置：

- `base_address`：接口基础地址，只填写 `host:port`
- `authorization_suffix`：`Authorization: Bearer xxx` 中 `xxx` 的部分
- `request_timeout_seconds`：请求超时秒数
- `auth_url_params`：获取认证 URL 时附带的查询参数
- `headers`：通用静态请求头

说明：程序运行时会根据 `base_address` 自动拼出以下接口地址：

- `http://{base_address}/v0/management/codex-auth-url`
- `http://{base_address}/v0/management/get-auth-status`
- `http://{base_address}/v0/management/auth-files`

同时会自动生成：

- `Authorization: Bearer {authorization_suffix}`
- `Referer: http://{base_address}/management.html`

当前配置结构里已经不再使用 Cookie。

### 4. `email`

邮箱生成规则：

- `prefix`：邮箱前缀
- `domain`：邮箱域名
- `min_index`：最小编号
- `max_index`：最大编号

生成邮箱时格式为：`{prefix}{5位编号}{domain}`。

## 注意

- `settings.json` 包含敏感信息，不要提交到仓库
- 当前程序会直接读取这个文件，缺少关键字段会导致启动失败
- GUI 配置表单只暴露常用字段，其他高级字段仍可直接手动编辑 `settings.json`
