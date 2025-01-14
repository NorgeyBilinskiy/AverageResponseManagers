FROM python:3.12.7-slim

# Install dependencies
RUN apt-get update && \
    apt-get install -y gcc libpq-dev postgresql-client tzdata && \
    rm -rf /var/lib/apt/lists/*

# Set the timezone for the container
RUN echo "Asia/Moscow" > /etc/timezone && \
    ln -fs /usr/share/zoneinfo/Europe/Moscow /etc/localtime && \
    dpkg-reconfigure --frontend noninteractive tzdata

# Add uv binary for package management
COPY --from=ghcr.io/astral-sh/uv:0.5.2 /uv /uvx /bin/

# Install project dependencies using uv sync
COPY uv.lock pyproject.toml ./
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
RUN uv sync --frozen --no-install-project --no-dev

COPY . .

CMD ["uv", "run", "--no-dev", "-m", "main"]
