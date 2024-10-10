FROM dockerhub.yaoyy.moe/rosettacommons/rosetta:mpi

ENV HTTP_PROXY=http://a100-internal.yaoyy.moe:10089
ENV HTTPS_PROXY=http://a100-internal.yaoyy.moe:10089
ENV ALL_PROXY=http://a100-internal.yaoyy.moe:10089

ENV http_proxy=http://a100-internal.yaoyy.moe:10089
ENV https_proxy=http://a100-internal.yaoyy.moe:10089
ENV all_proxy=http://a100-internal.yaoyy.moe:10089
ENV GITHUB_ROSETTA_TEST=YES

RUN apt-get update -y && apt-get install build-essential git curl wget -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN python -m pip config set global.index-url https://mirrors.bfsu.edu.cn/pypi/web/simple \
    && python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir 'flit>=3.8.0'

ENV FLIT_ROOT_INSTALL=1

COPY pyproject.toml .
RUN touch README.md \
    && mkdir -p src/RosettaPy \
    && python -m flit install --only-deps --deps develop \
    && rm -r pyproject.toml README.md src
