# MPD/Snapcast Web Control

一个用于管理MPD和Snapcast的Web工具，可以实现音乐广播的上传、播放、定时等操作。

## 功能特点
- **Web界面控制：**
  - 支持添加、删除音乐到播放列表。
  - 定时播放功能。
  - 多客户端同步播放。
- **基于 Python 和 Flask：**
  - 使用MPD和Snapcast实现音乐广播。
  - 通过管道输出音频到Snapserver。

![截图描述](static/images/04.PNG)

## 环境要求

- Linux 服务器或 Armbian 系统（推荐）
- Python 3.7+ 
- MPD（Music Player Daemon）
- Snapserver（多房间音频同步工具）

   安装依赖
使用 pip 安装项目所需的 Python 模块
pip install -r requirements.txt

安装 MPD
-sudo apt update
-sudo apt install -y mpd
-编辑 MPD 配置文件
-sudo nano /etc/mpd.conf
-配置信息已同步/conf/mpd.conf
-重启 MPD 服务
-bash
-复制代码
-sudo systemctl restart mpd

-安装 Snapserver
-sudo apt install -y snapserver
-编辑 Snapserver 配置文件
-sudo nano /etc/snapserver.conf
-配置信息已同步/conf/snapserver.conf
-重启 Snapserver 服务
-sudo systemctl restart snapserver

-重点配置信息都指定了管道文件夹，需要为文件夹配置权限
-权限配置信息同步到/重点/权限配置.word

运行项目
在项目根目录下运行以下命令启动 Flask 后端服务：

python3 mpd_web.py
然后在浏览器访问：
http://<服务器IP>:5000


## 安装和运行
1. 克隆项目：
   ```bash
   git clone https://github.com/your-username/mpd-snapcast-web-control.git
   cd mpd-snapcast-web-control
