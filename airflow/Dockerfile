FROM apache/airflow:2.9.3
USER root

# Install additional system dependencies if needed
RUN if [ -f /etc/apt/sources.list ]; then \
      sed -i 's@http://deb.debian.org/debian@https://mirrors.ustc.edu.cn/debian@g' /etc/apt/sources.list && \
      sed -i 's@http://security.debian.org/debian-security@https://mirrors.ustc.edu.cn/debian-security@g' /etc/apt/sources.list && \
      apt-get update && \
      apt-get install -y --no-install-recommends \
        curl \
        build-essential \
        libssl-dev \
        libffi-dev \
        python3-dev \
        && apt-get clean && \
        rm -rf /var/lib/apt/lists/* ; \
    fi

USER airflow

# Copy Python requirements
COPY requirements.txt /
RUN pip install --no-cache-dir -r /requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# Copy DAGs
COPY --chown=airflow:root ./dags /opt/airflow/dags
