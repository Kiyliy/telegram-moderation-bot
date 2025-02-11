# 使用Python官方镜像作为基础镜像
FROM python:3.10.12

# 设置工作目录为/app
WORKDIR /app

# 将requirements.txt文件复制到容器中的/app
COPY requirements.txt .

# 使用pip安装requirements.txt中列出的所有依赖
RUN pip install --no-cache-dir -r requirements.txt

# 将当前目录下的所有文件复制到容器中的/app
COPY . .

# 指定容器启动时运行的命令
CMD ["python", "./main.py"]
