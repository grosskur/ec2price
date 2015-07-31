FROM ubuntu:14.04
MAINTAINER Alan Grosskurth <code@alan.grosskurth.ca>

RUN \
  locale-gen en_US.UTF-8 && \
  apt-get update && \
  env DEBIAN_FRONTEND=noninteractive apt-get -q -y install --no-install-recommends \
    build-essential \
    ca-certificates \
    curl \
    git-core \
    libbz2-dev \
    libcurl4-openssl-dev \
    liblzma-dev \
    libncurses5-dev \
    libpq-dev \
    libreadline-dev \
    libssl-dev \
    libxml2-dev \
    libxslt1-dev \
    pkg-config \
    zlib1g-dev && \
  apt-get clean && \
  rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

ENV \
  PATH=/opt/local/python/bin:"$PATH"

RUN \
  mkdir -p /tmp/src /opt/local/python && \
  cd /tmp/src && \
  curl -fsLS -O https://www.python.org/ftp/python/2.7.10/Python-2.7.10.tar.xz && \
  curl -fsLS -O https://bootstrap.pypa.io/get-pip.py && \
  echo '1cd3730781b91caf0fa1c4d472dc29274186480161a150294c42ce9b5c5effc0  Python-2.7.10.tar.xz' | sha256sum -c && \
  tar -xJf Python-2.7.10.tar.xz && \
  cd /tmp/src/Python-2.7.10 && \
  env LDFLAGS='-Wl,-rpath=/opt/local/python/lib' \
    ./configure --enable-shared --prefix=/opt/local/python && \
  make && \
  make install && \
  ldconfig && \
  cd /tmp/src && \
  /opt/local/python/bin/python get-pip.py && \
  cd /tmp && \
  rm -rf /tmp/src

WORKDIR /app
