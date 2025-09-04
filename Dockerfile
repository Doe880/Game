FROM python:3.10

# Базовые зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
    xvfb x11vnc fluxbox websockify novnc tini \
    locales fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Локаль для кириллицы
RUN sed -i 's/# ru_RU.UTF-8 UTF-8/ru_RU.UTF-8 UTF-8/' /etc/locale.gen && locale-gen

# Устанавливем зависимости Python
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Игра и стартовый скрипт
COPY game.py /app/game.py
COPY start.sh /usr/local/bin/start.sh
RUN chmod +x /usr/local/bin/start.sh

EXPOSE 8080
ENTRYPOINT ["/usr/bin/tini","--"]
CMD ["/usr/local/bin/start.sh"]
