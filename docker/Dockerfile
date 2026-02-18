# ============================================================
# Stage 1: Builder - Python依存関係のインストールとパッケージビルド
# ============================================================
FROM python:3.12-slim AS builder

WORKDIR /build

# uvのインストール
COPY --from=ghcr.io/astral-sh/uv:0.10.4 /uv /usr/local/bin/uv

# 依存関係ファイルのコピー（キャッシュ最適化のため先にコピー）
COPY pyproject.toml uv.lock ./

# 依存関係のインストール（開発依存を除く）
RUN uv sync --frozen --no-dev --no-install-project

# アプリケーションソースのコピーとインストール
COPY src/ src/
COPY config/ config/
RUN uv sync --frozen --no-dev

# ============================================================
# Stage 2: Runtime - ツールのインストールとアプリケーション配置
# ============================================================
FROM python:3.12-slim AS runtime

# ビルド引数
ARG TERRAFORM_VERSION=1.9.8
ARG KUBECTL_VERSION=1.30.7
ARG TARGETARCH

WORKDIR /app

# 共通の依存パッケージをインストール
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        unzip \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Terraformのインストール
RUN ARCH=$(case "${TARGETARCH}" in "arm64") echo "arm64" ;; *) echo "amd64" ;; esac) && \
    curl -fsSL "https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_${ARCH}.zip" \
        -o /tmp/terraform.zip && \
    unzip /tmp/terraform.zip -d /usr/local/bin/ && \
    rm /tmp/terraform.zip && \
    terraform version

# kubectlのインストール
RUN ARCH=$(case "${TARGETARCH}" in "arm64") echo "arm64" ;; *) echo "amd64" ;; esac) && \
    curl -fsSL "https://dl.k8s.io/release/v${KUBECTL_VERSION}/bin/linux/${ARCH}/kubectl" \
        -o /usr/local/bin/kubectl && \
    chmod +x /usr/local/bin/kubectl && \
    kubectl version --client

# 不要パッケージの削除
RUN apt-get purge -y --auto-remove curl unzip && \
    rm -rf /var/lib/apt/lists/*

# 非rootユーザーの作成
RUN groupadd --gid 1000 galley && \
    useradd --uid 1000 --gid galley --create-home galley

# Python仮想環境とアプリケーションのコピー
COPY --from=builder /build/.venv /app/.venv
COPY --from=builder /build/config /app/config

# OCI CLIのインストール（仮想環境内にpipで追加）
RUN /app/.venv/bin/pip install --no-cache-dir oci-cli

# 環境変数の設定
ENV PATH="/app/.venv/bin:${PATH}" \
    VIRTUAL_ENV="/app/.venv" \
    GALLEY_DATA_DIR="/data" \
    GALLEY_CONFIG_DIR="/app/config" \
    GALLEY_HOST="0.0.0.0" \
    GALLEY_PORT="8000"

# データディレクトリの作成と権限設定
RUN mkdir -p /data && chown galley:galley /data

# 非rootユーザーに切り替え
USER galley

# ポート公開
EXPOSE 8000

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# エントリポイント
ENTRYPOINT ["python", "-m", "galley"]
