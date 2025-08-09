# Fail2Ban 全球恶意扫描防御态势仪表盘

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-3.1.1-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

一个基于 Python Flask 和 Plotly.js 构建的动态Web仪表盘，用于可视化分析 `fail2ban` 的日志文件。它能将来自全球的恶意扫描（特指SSH）以一个可交互的3D地球仪形式展现出来，并提供详细的数据分析面板。

![效果图](https://i.imgur.com/8QfWj8p.png)

## ✨ 主要功能

- **🌍 动态3D地球仪**: 以可交互、可旋转的地球仪形式，实时展示从攻击来源国到您服务器的攻击路径
- **📊 数据分析面板**:
  - **Top 10 攻击来源国**: 聚合展示攻击次数最多的国家，并附带国旗Emoji
  - **Top 10 攻击来源机构 (ASN)**: 分析攻击IP主要来自哪些云服务商或ISP，帮助识别自动化攻击
- **🔄 双视图切换**: 支持一键在您自己的服务器态势图和卡巴斯基全球网络攻击地图之间切换
- **⚙️ 后台服务化**: 使用 Gunicorn 和 systemd 进行生产环境部署，确保服务稳定、高效，并能开机自启
- **🔧 高度可配置**: 通过简单的 `config.ini` 文件即可配置服务器位置、日志路径等关键参数

## 🛠️ 技术栈

- **后端**: Python 3.8+, Flask 3.1.1, Gunicorn
- **数据处理**: Pandas, GeoIP2, NumPy
- **前端**: HTML5, CSS3, JavaScript (ES6+)
- **可视化**: Plotly.js
- **部署**: systemd (Linux), Docker (可选)

## 📋 系统要求

- Python 3.8 或更高版本
- Linux 操作系统 (推荐 Ubuntu 20.04+ 或 CentOS 8+)
- 已安装并运行的 Fail2Ban 服务
- 至少 512MB 可用内存
- 网络连接 (用于下载 GeoIP 数据库)

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/ClaraCora/failban_map.git
cd failban_map
```

### 2. 下载 GeoIP 数据库

本项目需要 MaxMind 的免费 GeoLite2 数据库来将 IP 地址转换为地理位置。

1. 访问 [MaxMind 官网](https://www.maxmind.com/en/geolite2/signup) 注册一个免费账户
2. 登录后，在下载页面找到 "GeoLite2 City" 和 "GeoLite2 ASN"
3. 下载 `GeoLite2-City.mmdb` 和 `GeoLite2-ASN.mmdb` 这两个文件
4. 将这两个 `.mmdb` 文件放入项目中的 `data/` 文件夹内

```bash
# 创建数据目录
mkdir -p data

# 将下载的文件放入 data/ 目录
# GeoLite2-City.mmdb
# GeoLite2-ASN.mmdb
```

### 3. 配置项目

编辑 `config.ini` 文件，根据您的实际情况修改参数：

```ini
[Paths]
# 确认 fail2ban 日志路径正确
log_file = /var/log/fail2ban.log
geoip_city_db = ./data/GeoLite2-City.mmdb
geoip_asn_db = ./data/GeoLite2-ASN.mmdb
output_json = ./output/report_data.json

[Settings]
# 设置您服务器的地理位置 (经纬度)
# 您可以通过 https://www.latlong.net/ 查询
server_latitude = 45.5231  # 示例: 美国俄勒冈州
server_longitude = -122.6765
# 设置您服务器在地图上显示的名称
server_name = My Server (State of Oregon)
# 设置默认显示的地图视图 (native 或 kaspersky)
default_view = native
```

### 4. 安装依赖

我们使用Python虚拟环境来管理项目依赖，确保与系统环境隔离。

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装所有依赖
pip install -r requirements.txt
```

### 5. 测试运行

```bash
# 确保虚拟环境已激活
source venv/bin/activate

# 运行应用
python app.py
```

访问 `http://localhost:5000` 查看仪表盘。

### 6. 生产环境部署

#### 使用 systemd (推荐)

1. **安装 Gunicorn**:
   ```bash
   pip install gunicorn
   ```

2. **创建 systemd 服务文件**:
   ```bash
   sudo nano /etc/systemd/system/fail2ban_dashboard.service
   ```

3. **将以下内容粘贴到文件中**:
   ```ini
   [Unit]
   Description=Fail2Ban Dashboard Gunicorn Service
   After=network.target

   [Service]
   User=root
   Group=www-data
   WorkingDirectory=/opt/failban_map
   Environment="PATH=/opt/failban_map/venv/bin"
   ExecStart=/opt/failban_map/venv/bin/gunicorn --workers 3 --bind 0.0.0.0:5000 app:app
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

4. **启动并管理服务**:
   ```bash
   # 重新加载 systemd 配置
   sudo systemctl daemon-reload
   # 启动服务
   sudo systemctl start fail2ban_dashboard
   # 设置开机自启
   sudo systemctl enable fail2ban_dashboard
   ```

#### 使用 Docker (可选)

```bash
# 构建镜像
docker build -t failban-map .

# 运行容器
docker run -d -p 5000:5000 --name failban-dashboard failban-map
```

## ⚙️ 服务管理

- **查看服务状态**: `sudo systemctl status fail2ban_dashboard`
- **重启服务** (在修改代码后): `sudo systemctl restart fail2ban_dashboard`
- **停止服务**: `sudo systemctl stop fail2ban_dashboard`
- **查看实时日志**: `sudo journalctl -u fail2ban_dashboard -f`

## 📊 使用说明

### 访问仪表盘

部署完成后，打开浏览器访问 `http://<您的服务器IP>:5000` 即可看到动态仪表盘。

### 功能说明

1. **3D地球仪视图**: 
   - 鼠标拖拽可旋转地球
   - 滚轮可缩放
   - 点击攻击路径可查看详细信息

2. **数据分析面板**:
   - 实时显示攻击统计数据
   - 支持按时间范围筛选
   - 提供攻击趋势分析

3. **视图切换**:
   - 点击右上角按钮可在本地视图和卡巴斯基全球视图间切换

### 数据刷新

仪表盘会自动从 Fail2Ban 日志中解析数据。如需手动刷新，可点击页面上的刷新按钮或调用 API：

```bash
curl -X POST http://localhost:5000/refresh
```

## 🔧 配置说明

### config.ini 配置项

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `log_file` | Fail2Ban 日志文件路径 | `/var/log/fail2ban.log` |
| `geoip_city_db` | GeoLite2 City 数据库路径 | `./data/GeoLite2-City.mmdb` |
| `geoip_asn_db` | GeoLite2 ASN 数据库路径 | `./data/GeoLite2-ASN.mmdb` |
| `output_json` | 输出JSON文件路径 | `./output/report_data.json` |
| `server_latitude` | 服务器纬度 | `45.5231` |
| `server_longitude` | 服务器经度 | `-122.6765` |
| `server_name` | 服务器显示名称 | `My Server` |
| `default_view` | 默认视图 (native/kaspersky) | `native` |

## 🐛 故障排除

### 常见问题

1. **数据不显示**
   - 检查 Fail2Ban 日志文件路径是否正确
   - 确认 GeoIP 数据库文件是否存在
   - 查看应用日志: `sudo journalctl -u fail2ban_dashboard -f`

2. **服务启动失败**
   - 检查 Python 虚拟环境是否正确创建
   - 确认所有依赖已安装: `pip list`
   - 验证配置文件语法: `python -c "import configparser; configparser.ConfigParser().read('config.ini')"`

3. **地图不显示**
   - 检查网络连接
   - 确认 Plotly.js 库加载正常
   - 查看浏览器控制台错误信息

### 日志查看

```bash
# 查看应用日志
sudo journalctl -u fail2ban_dashboard -f

# 查看系统日志
sudo tail -f /var/log/syslog | grep fail2ban_dashboard
```

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

### 开发环境设置

1. Fork 本仓库
2. 克隆您的 fork: `git clone https://github.com/your-username/failban_map.git`
3. 创建功能分支: `git checkout -b feature/your-feature`
4. 提交更改: `git commit -am 'Add some feature'`
5. 推送分支: `git push origin feature/your-feature`
6. 创建 Pull Request

### 代码规范

- 遵循 PEP 8 Python 代码规范
- 添加适当的注释和文档字符串
- 确保所有测试通过

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [MaxMind](https://www.maxmind.com/) - 提供免费的 GeoLite2 数据库
- [Plotly.js](https://plotly.com/javascript/) - 强大的数据可视化库
- [Flask](https://flask.palletsprojects.com/) - 轻量级 Web 框架
- [Fail2Ban](https://www.fail2ban.org/) - 优秀的入侵检测系统

## 📞 联系方式

- 项目主页: [https://github.com/ClaraCora/failban_map](https://github.com/ClaraCora/failban_map)
- 问题反馈: [Issues](https://github.com/ClaraCora/failban_map/issues)

---

⭐ 如果这个项目对您有帮助，请给我们一个星标！