#!/usr/bin/env bash
set -e

pip install -r requirements.txt

# Chromium 시스템 의존성 수동 설치 (Render 등 Debian 계열)
if command -v apt-get &> /dev/null; then
  apt-get update -qq
  apt-get install -y --no-install-recommends \
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libxkbcommon0 libxcomposite1 \
    libxdamage1 libxrandr2 libgbm1 libpango-1.0-0 \
    libcairo2 libasound2 libxshmfence1 libx11-xcb1 \
    libxfixes3 fonts-noto-cjk \
    2>/dev/null || echo "Warning: some apt packages failed, continuing..."
fi

# Playwright Chromium 설치
python -m playwright install chromium --with-deps 2>/dev/null \
  || python -m playwright install chromium \
  || { echo "ERROR: Playwright Chromium 설치 실패"; exit 1; }
