FROM registry.fedoraproject.org/fedora:latest AS build

RUN dnf install -y \
        python3-pip \
        python3-pyyaml \
        golang \
        && dnf clean all

WORKDIR /src

COPY Makefile .
COPY pyproject.toml /src/
COPY src /src/src

RUN pip install --no-dependencies .

RUN make external

# no osbuild-depsolve-dnf here:
# FROM registry.access.redhat.com/ubi9/ubi-minimal
FROM registry.fedoraproject.org/fedora:latest

RUN dnf install -y \
    python3-pyyaml \
    osbuild-depsolve-dnf \
    && dnf clean all

COPY --from=build /usr/local/bin/otk /usr/local/bin/
COPY --from=build /usr/local/bin/osbuild* /usr/libexec/otk/external/
COPY --from=build /usr/local/lib/ /usr/local/lib/

COPY --from=build /src/external/* /usr/local/libexec/otk/external/

WORKDIR /app

ENTRYPOINT ["otk"]
