FROM --platform=linux/amd64 python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# RUN apt-get install -y wget

# RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb

# RUN apt-get install -y ./google-chrome-stable_current_amd64.deb

# RUN rm -rf ./google-chrome-stable_current_amd64.deb

COPY requirements.txt .

RUN pip config set global.index-url https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
