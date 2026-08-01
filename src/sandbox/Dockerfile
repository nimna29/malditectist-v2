# Docker container for Opcode Tracer
# This container includes followings
# Ubuntu 22.04 with OpenJDK 17, Intel PIN 3.30, Xvfb

# Intel PIN - Dynamic Binary Instrumentation framework by Intel
# Connected to a running process and instruments every instruction at runtime
# Official Docs: https://www.intel.com/content/www/us/en/developer/articles/tool/pin-a-dynamic-binary-instrumentation-tool.html

FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Required system packages install
RUN apt-get update && apt-get install -y \
    # Java runtime jdk
    openjdk-17-jdk \
    # Building tools for Pintool compilation
    g++ \
    make \
    wget \
    ca-certificates \
    # 
    xvfb \
    unzip \
    && rm -rf /var/lib/apt/lists/*


# Intel PIN Installation
ENV PIN_ROOT=/pin
ENV PIN_VERSION=3.30-98830-g1d7b601b3
ENV PIN_ARCHIVE=pin-${PIN_VERSION}-gcc-linux.tar.gz
ENV PIN_URL=https://software.intel.com/sites/landingpage/pintool/downloads/${PIN_ARCHIVE}


# Download and extract Intel PIN
RUN wget -q ${PIN_URL} -O /tmp/${PIN_ARCHIVE} \
    # Create the PIN_ROOT directory and extract the downloaded archive into it
    && mkdir -p ${PIN_ROOT} \
    # Extract the contents of the archive into the PIN_ROOT directory by removing the top-level directory from the archive structure
    && tar -xzf /tmp/${PIN_ARCHIVE} -C ${PIN_ROOT} --strip-components=1 \
    # Remove the downloaded archive to free up space
    && rm /tmp/${PIN_ARCHIVE}


# Pintool Build
# Here, the Pintool source code and the makefile.rules are copied into the PIN's tools directory
# Next, build using PIN's own makefile framework
COPY pintool/opcode_tracer.cpp ${PIN_ROOT}/source/tools/MalDitectist/opcode_tracer.cpp
COPY pintool/makefile.rules ${PIN_ROOT}/source/tools/MalDitectist/makefile.rules

# Create the makefile using the exact template that Inetl provides in the kit
# Following command verified by directly inspecting the /pin/source/tools/ManualExamples/makefile
RUN printf '%s\n' \
    'ifdef PIN_ROOT' \
    'CONFIG_ROOT := $(PIN_ROOT)/source/tools/Config' \
    'else' \
    'CONFIG_ROOT := ../Config' \
    'endif' \
    'include $(CONFIG_ROOT)/makefile.config' \
    'include makefile.rules' \
    'include $(TOOLS_ROOT)/Config/makefile.default.rules' \
    > ${PIN_ROOT}/source/tools/MalDitectist/makefile

# Build the Pintool
# Changes the working directory to the Pintool's source directory
# Next runs the make command to compile the Pintool 
# The output of this build process create a shared object file (opcode_tracer.so) 
# located in the obj-intel64 directory
RUN cd ${PIN_ROOT}/source/tools/MalDitectist \
    && make PIN_ROOT=${PIN_ROOT} obj-intel64/opcode_tracer.so

# Copy the compiled Pintool to a new clean location
RUN mkdir -p /pintool \
    && cp ${PIN_ROOT}/source/tools/MalDitectist/obj-intel64/opcode_tracer.so \
    /pintool/opcode_tracer.so


# Scripts for execute the trace
COPY scripts/run_trace.sh /run_trace.sh
RUN chmod +x /run_trace.sh


# Working directory and the entrypoint
WORKDIR /trace
ENTRYPOINT ["/run_trace.sh"]
