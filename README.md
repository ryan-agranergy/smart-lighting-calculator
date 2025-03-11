# Agranergy Energy Savings Calculator

## 项目简介

这是一个能源节省计算器应用，用于帮助用户计算和优化照明系统的能源消耗。

## 功能特点

- 照明能耗计算
- 照明系统优化建议
- 节能方案比较
- 投资回报期分析

## 安装说明

1. 克隆项目到本地：

```bash
git clone https://github.com/ryan-agranergy/agranergy-energy-savings-calculator.git
cd agranergy-energy-savings-calculator
```

1. 安装依赖：

```bash
pip install -r requirements.txt
```

## 使用方法

1. 运行应用：

```bash
streamlit run app.py 
```

1. 在浏览器中访问：

```text
http://localhost:8501/
```

## 技术栈

- Python
- Streamlit
- SQLite

## 自动部署

本项目使用 GitHub Actions 自动部署到服务器。要启用自动部署，需要在 GitHub 仓库设置以下 Secrets：

- `SERVER_HOST`: 服务器的公共 IP 或域名
- `SERVER_USERNAME`: 服务器的用户名（通常是 'ubuntu'）
- `SERVER_SSH_KEY`: 服务器的 SSH 私钥

### 服务器配置

部署脚本会自动完成以下操作：

1. 将应用部署到 `/opt/calculator` 目录
2. 保留最近 5 个备份版本
3. 自动重启服务

你可以通过以下命令检查服务状态：

```bash
sudo systemctl status agranergy-calculator
```

如果需要查看应用日志：

```bash
sudo journalctl -u agranergy-calculator -f
```

## 贡献指南

欢迎提交问题和改进建议！请遵循以下步骤：

1. Fork 本仓库
2. 创建您的特性分支 (git checkout -b feature/AmazingFeature)
3. 提交您的更改 (git commit -m 'Add some AmazingFeature')
4. 推送到分支 (git push origin feature/AmazingFeature)
5. 开启一个 Pull Request

## 许可证

MIT License

## 联系方式

如有任何问题，请联系项目维护者。