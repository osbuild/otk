FROM registry.fedoraproject.org/fedora:latest AS build_python

RUN dnf install -y \
        python3-pip \
        python3-pyyaml \
        && dnf clean all

WORKDIR /src

COPY pyproject.toml /src/
COPY src /src/src

RUN pip install --no-dependencies .

# ----
FROM registry.access.redhat.com/ubi9/go-toolset:latest AS build_go

ARG CONTAINERS_STORAGE_THIN_TAGS="containers_image_openpgp exclude_graphdriver_btrfs exclude_graphdriver_devicemapper"
ENV CONTAINERS_STORAGE_THIN_TAGS=${CONTAINERS_STORAGE_THIN_TAGS}

ARG IMAGES_REF="github.com/osbuild/images"
ENV IMAGES_REF=${IMAGES_REF}

COPY Makefile .

RUN make external

# ----
# no osbuild-depsolve-dnf here:
# FROM registry.access.redhat.com/ubi9/ubi-minimal
FROM registry.fedoraproject.org/fedora:latest

RUN dnf install -y \
    python3-pyyaml \
    osbuild-depsolve-dnf \
    && dnf clean all

COPY --from=build_python /usr/local/bin/otk /usr/local/bin/
COPY --from=build_python /usr/local/bin/osbuild* /usr/libexec/otk/external/
COPY --from=build_python /usr/local/lib/ /usr/local/lib/

COPY --from=build_go /opt/app-root/src/external/* /usr/local/libexec/otk/external/

WORKDIR /app

ENTRYPOINT ["otk"]
