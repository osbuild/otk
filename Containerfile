FROM registry.access.redhat.com/ubi9/ubi-minimal AS build

RUN \
    microdnf install -y \
        python3-pip && \
        microdnf clean all

WORKDIR /src

COPY pyproject.toml /src/
COPY src /src/src

RUN pip install .
RUN rm -rf src/*

CMD ["otk"]
