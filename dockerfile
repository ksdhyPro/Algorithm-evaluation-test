FROM python:3.10.18-slim

WORKDIR /app

# 先复制依赖文件
COPY requirements.txt .

# 安装依赖
RUN pip install -r requirements.txt

# 再复制代码
COPY . .

EXPOSE 5000

CMD ["python", "app.py"]