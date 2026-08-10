# -*- coding: utf-8 -*- 
########################################
# Docker build
########################################
#time sudo docker build -t faborobot/jetson-jp511-aicar -f Dockerfile_jetson_jp511_faborobot_aicar .

# docker push
jetson-jp51-deepstream62-triton-base:20230403

########################################
# Storage setting
########################################
#sudo service docker stop
#sudo systemctl stop docker.socket
#cd /var/lib
#sudo mv docker /mnt/ssd2t
#sudo ln -s /mnt/ssd2t/docker docker
#sudo service docker start

# https://github.com/NVIDIA/nvidia-docker/issues/1033
# cmake fails unable to find cuda library while building an image
#vi /etc/docker/daemon.json
#{
#    "runtimes": {
#        "nvidia": {
#            "path": "/usr/bin/nvidia-container-runtime",
#            "runtimeArgs": []
#        }
#    },
#    "default-runtime": "nvidia"
#}
#
#service docker stop
#systemctl stop docker.socket
#service docker start


# end of information


########################################
# Base OS repogitory
########################################
# ex. https://github.com/NVIDIA-AI-IOT/ros2_jetson/blob/main/docker/DockerFile.l4tbase.ros2.foxy
# DeepStream-l4t tags: https://catalog.ngc.nvidia.com/orgs/nvidia/containers/deepstream-l4t/tags

# JetPack 5.1.1/L4T R35.3.1
# GL4.6/Vulkan1.3.1.1
# ARG BASE_IMAGE=nvcr.io/nvidia/deepstream-l4t:6.2-triton

ARG BASE_IMAGE=nvcr.io/nvidia/deepstream-l4t:6.2-triton
FROM ${BASE_IMAGE}

########################################
# ENV
########################################
ENV DEBIAN_FRONTEND=noninteractive

########################################
# change the locale from POSIX to UTF-8
########################################
RUN locale-gen en_US en_US.UTF-8 && update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
ENV LANG=en_US.UTF-8

########################################
# apt fix
########################################
# Because sometime the repository is 404, use with --fix-missing option.
RUN rm -rf /var/lib/apt/lists/* \
    && apt-get --fix-missing update \
    && apt-get install -y apt-utils \
    && apt autoremove -y \
    && rm -rf /var/lib/apt/lists/*


########################################
# change group ids
########################################
# deepstream-l4t:6.0.1-triton
# Add gpio debug trusty crypto weston-launch colord group
# Change to the same group id as host
# systemd-timesync 101 -> 107
# systemd-journal  102 -> 108
# systemd-network  103 -> 109
# systemd-resolve  104 -> 110
# input            106 -> 101
# kvm              107 -> 102   
# messagebus       105 -> 111
# syslog           111 -> 131
# render           108 -> 103
# netdev           109 -> 106
# i2c              110 -> 113
# ls -l /dev/
# cat /etc/group
RUN groupmod -g 999 kvm \
    && groupmod -g 107 systemd-timesync \
    && groupmod -g 101 input \
    && groupmod -g 106 netdev \
    && groupmod -g 109 systemd-network \
    && groupmod -g 103 render \
    && groupmod -g 108 systemd-journal \
    && groupmod -g 102 kvm \
    && groupmod -g 113 i2c \
    && groupmod -g 110 systemd-resolve \
    && groupmod -g 131 syslog \
    && groupmod -g 111 messagebus \
    && groupadd -f -r lpadmin \
    && groupmod -g 116 lpadmin \
    && groupadd -f -r colord \
    && groupmod -g 127 colord \
    && groupadd -f -r gdm \
    && groupmod -g 139 gdm \
    && groupadd -f -r debug \
    && groupmod -g 995 debug \
    && groupadd -f -r weston-launch \
    && groupmod -g 996 weston-launch \
    && groupadd -f -r crypto \
    && groupmod -g 997 crypto \
    && groupadd -f -r trusty \
    && groupmod -g 998 trusty \
    && groupadd -f -r gpio \
    && groupmod -g 999 gpio


########################################
# XAuthority
########################################
RUN apt-get update \
    && apt-get install -y \
      sudo \
      xauth \
      xterm \
    && apt autoremove -y \
    && rm -rf /var/lib/apt/lists/*
#Add new sudo user
ARG USERNAME=jetson
RUN useradd -m $USERNAME && \
        echo "$USERNAME:$USERNAME" | chpasswd && \
        usermod --shell /bin/bash $USERNAME && \
        usermod -aG sudo,adm,cdrom,audio,dip,video,plugdev,render,i2c,lpadmin,gdm,gpio,dialout,input $USERNAME && \
        echo "$USERNAME ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers.d/$USERNAME && \
        chmod 0440 /etc/sudoers.d/$USERNAME && \
        # Replace 1000 with your user/group id
        usermod  --uid 1000 $USERNAME && \
        groupmod --gid 1000 $USERNAME


########################################
# bash setting
########################################
# sed
# escape characters \'$.*/[]^
# 1. Write the regex between single quotes.
# 2. \ -> \\
# 3. ' -> '\''
# 4. Put a backslash before $.*/[]^ and only those characters.


####################
# USER
####################
# before
# #force_color_prompt=yes
# after
# force_color_prompt=yes

# deepstream-l4t:6.0.1-triton
# before
#    PS1='${debian_chroot:+($debian_chroot)}\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ '
# after
#    PS1='${debian_chroot:+($debian_chroot)}\[\033[01;32m\]\u@\[\033[01;31m\]docker-\h\[\033[00m\]:\[\033[01;35m\]\w\[\033[00m\]\$ '

# before
# alias ls='ls --color=auto'
# after
# alias ls='ls -asiF --color=auto'

RUN sed -i 's/#force_color_prompt=yes/force_color_prompt=yes/g' /home/$USERNAME/.bashrc \
&& sed -i 's/PS1='\''\${debian_chroot:+(\$debian_chroot)}\\\[\\033\[01;32m\\\]\\u@\\h\\\[\\033\[00m\\\]:\\\[\\033\[01;34m\\\]\\w\\\[\\033\[00m\\\]\\\$ '\''/PS1='\''\${debian_chroot:+(\$debian_chroot)}\\\[\\033\[01;32m\\\]\\u@\\\[\\033\[01;31m\\\]docker-\\h\\\[\\033\[00m\\\]:\\\[\\033\[01;35m\\\]\\w\\\[\\033\[00m\\\]\\\$ '\''/g' /home/$USERNAME/.bashrc \
&& sed -i 's/alias ls='\''ls --color=auto'\''/alias ls='\''ls -asiF --color=auto'\''/g' /home/$USERNAME/.bashrc \
&& echo 'alias xterm='"'"'xterm -fa '"'"'Monospace'"'"' -fs 10 -fg white -bg black'"'"'\n' >> /home/$USERNAME/.bashrc \
&& echo 'export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/cuda-11.4/lib64:/usr/local/cuda-11.4/targets/aarch64-linux/lib:/usr/local/lib' >> /home/$USERNAME/.bashrc \
&& echo 'export LANG=en_US.UTF-8' >> /home/$USERNAME/.bashrc \
&& echo 'export NO_AT_BRIDGE=1' >> /home/$USERNAME/.bashrc \
&& echo 'export PATH=$PATH:/usr/src/tensorrt/bin' >> /home/$USERNAME/.bashrc \
&& echo 'cd' >> /home/$USERNAME/.bashrc \
&& echo "complete -d cd" >> /home/$USERNAME/.bashrc


####################
# ROOT
####################
# before
#    xterm-color) color_prompt=yes;;
# after
#    xterm-color|*-256color) color_prompt=yes;;

# before
#    PS1='${debian_chroot:+($debian_chroot)}\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ '
# after
#    PS1='${debian_chroot:+($debian_chroot)}\[\033[01;37m\]\u@\[\033[01;31m\]docker-\h\[\033[00m\]:\[\033[01;35m\]\w\[\033[00m\]\$ '

# before
# alias ls='ls --color=auto'
# after
# alias ls='ls -asiF --color=auto'

RUN sed -i 's/xterm-color) color_prompt=yes;;/xterm-color|\*-256color) color_prompt=yes;;/g' /root/.bashrc \
&& sed -i 's/#force_color_prompt=yes/force_color_prompt=yes/g' /root/.bashrc \
&& sed -i 's/PS1='\''\${debian_chroot:+(\$debian_chroot)}\\\[\\033\[01;32m\\\]\\u@\\h\\\[\\033\[00m\\\]:\\\[\\033\[01;34m\\\]\\w\\\[\\033\[00m\\\]\\\$ '\''/PS1='\''\${debian_chroot:+(\$debian_chroot)}\\\[\\033\[01;37m\\\]\\u@\\\[\\033\[01;31m\\\]docker-\\h\\\[\\033\[00m\\\]:\\\[\\033\[01;35m\\\]\\w\\\[\\033\[00m\\\]\\\$ '\''/g' /root/.bashrc \
&& sed -i 's/alias ls='\''ls --color=auto'\''/alias ls='\''ls -asiF --color=auto'\''/g' /root/.bashrc \
&& echo 'alias xterm='"'"'xterm -fa '"'"'Monospace'"'"' -fs 10 -fg white -bg black'"'"'\n' >> /root/.bashrc \
&& echo 'export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/cuda-11.4/lib64:/usr/local/cuda-11.4/targets/aarch64-linux/lib:/usr/local/lib' >> /root/.bashrc \
&& echo 'export LANG=en_US.UTF-8' >> /root/.bashrc \
&& echo 'export NO_AT_BRIDGE=1' >> /root/.bashrc \
&& echo 'export PATH=$PATH:/usr/src/tensorrt/bin' >> /root/.bashrc \
&& echo "complete -d cd" >> /root/.bashrc


#########################################
# .dircolors
########################################
# end of line: \n\
# ': '"'"'

RUN echo '# dircolors -p > ~/.dircolors\n\
# vi ~/.dircolors\n\
# man dircolors\n\
\n\
# Configuration file for dircolors, a utility to help you set the\n\
# LS_COLORS environment variable used by GNU ls with the --color option.\n\
# Copyright (C) 1996-2016 Free Software Foundation, Inc.\n\
# Copying and distribution of this file, with or without modification,\n\
# are permitted provided the copyright notice and this notice are preserved.\n\
# The keywords COLOR, OPTIONS, and EIGHTBIT (honored by the\n\
# slackware version of dircolors) are recognized but ignored.\n\
# Below are TERM entries, which can be a glob patterns, to match\n\
# against the TERM environment variable to determine if it is colorizable.\n\
TERM Eterm\n\
TERM ansi\n\
TERM color-xterm\n\
TERM con[0-9]*x[0-9]*\n\
TERM cons25\n\
TERM console\n\
TERM cygwin\n\
TERM dtterm\n\
TERM eterm-color\n\
TERM gnome\n\
TERM gnome-256color\n\
TERM hurd\n\
TERM jfbterm\n\
TERM konsole\n\
TERM kterm\n\
TERM linux\n\
TERM linux-c\n\
TERM mach-color\n\
TERM mach-gnu-color\n\
TERM mlterm\n\
TERM putty\n\
TERM putty-256color\n\
TERM rxvt*\n\
TERM screen*\n\
TERM st\n\
TERM st-256color\n\
TERM terminator\n\
TERM tmux*\n\
TERM vt100\n\
TERM xterm*\n\
# Below are the color init strings for the basic file types. A color init\n\
# string consists of one or more of the following numeric codes:\n\
# Attribute codes:\n\
# 00=none 01=bold 04=underscore 05=blink 07=reverse 08=concealed\n\
# Text color codes:\n\
# 30=black 31=red 32=green 33=yellow 34=blue 35=magenta 36=cyan 37=white\n\
# Background color codes:\n\
# 40=black 41=red 42=green 43=yellow 44=blue 45=magenta 46=cyan 47=white\n\
#NORMAL 00 # no color code at all\n\
#FILE 00 # regular file: use no color at all\n\
RESET 0 # reset to "normal" color\n\
DIR 01;35 # directory\n\
LINK 01;36 # symbolic link. (If you set this to '"'"'target'"'"' instead of a\n\
 # numerical value, the color is as for the file pointed to.)\n\
MULTIHARDLINK 00 # regular file with more than one link\n\
FIFO 40;99 # pipe\n\
SOCK 01;32 # socket\n\
DOOR 01;32 # door\n\
BLK 40;99;01 # block device driver\n\
CHR 40;99;01 # character device driver\n\
ORPHAN 40;31;01 # symlink to nonexistent file, or non-stat'"'"'able file ...\n\
MISSING 00 # ... and the files they point to\n\
SETUID 37;41 # file that is setuid (u+s)\n\
SETGID 30;43 # file that is setgid (g+s)\n\
CAPABILITY 30;41 # file with capability\n\
STICKY_OTHER_WRITABLE 30;42 # dir that is sticky and other-writable (+t,o+w)\n\
OTHER_WRITABLE 35;42 # dir that is other-writable (o+w) and not sticky\n\
STICKY 37;44 # dir with the sticky bit set (+t) and not other-writable\n\
# This is for files with execute permission:\n\
EXEC 01;31\n\
# List any file extensions like '"'"'.gz'"'"' or '"'"'.tar'"'"' that you would like ls\n\
# to colorize below. Put the extension, a space, and the color init string.\n\
# (and any comments you want to add after a '"'"'#'"'"')\n\
# If you use DOS-style suffixes, you may want to uncomment the following:\n\
#.cmd 01;31 # executables (bright green)\n\
#.exe 01;31\n\
#.com 01;31\n\
#.btm 01;31\n\
#.bat 01;31\n\
# Or if you want to colorize scripts even if they do not have the\n\
# executable bit actually set.\n\
#.sh 01;31\n\
#.csh 01;31\n\
 # archives or compressed (bright red)\n\
.tar 01;33\n\
.tgz 01;33\n\
.arc 01;33\n\
.arj 01;33\n\
.taz 01;33\n\
.lha 01;33\n\
.lz4 01;33\n\
.lzh 01;33\n\
.lzma 01;33\n\
.tlz 01;33\n\
.txz 01;33\n\
.tzo 01;33\n\
.t7z 01;33\n\
.zip 01;33\n\
.z 01;33\n\
.Z 01;33\n\
.dz 01;33\n\
.gz 01;33\n\
.lrz 01;33\n\
.lz 01;33\n\
.lzo 01;33\n\
.xz 01;33\n\
.bz2 01;33\n\
.bz 01;33\n\
.tbz 01;33\n\
.tbz2 01;33\n\
.tz 01;33\n\
.deb 01;33\n\
.rpm 01;33\n\
.jar 01;33\n\
.war 01;33\n\
.ear 01;33\n\
.sar 01;33\n\
.rar 01;33\n\
.alz 01;33\n\
.ace 01;33\n\
.zoo 01;33\n\
.cpio 01;33\n\
.7z 01;33\n\
.rz 01;33\n\
.cab 01;33\n\
# image formats\n\
.jpg 01;32\n\
.jpeg 01;32\n\
.gif 01;32\n\
.bmp 01;32\n\
.pbm 01;32\n\
.pgm 01;32\n\
.ppm 01;32\n\
.tga 01;32\n\
.xbm 01;32\n\
.xpm 01;32\n\
.tif 01;32\n\
.tiff 01;32\n\
.png 01;32\n\
.svg 01;32\n\
.svgz 01;32\n\
.mng 01;32\n\
.pcx 01;32\n\
.mov 01;32\n\
.mpg 01;32\n\
.mpeg 01;32\n\
.m2v 01;32\n\
.mkv 01;32\n\
.webm 01;32\n\
.ogm 01;32\n\
.mp4 01;32\n\
.m4v 01;32\n\
.mp4v 01;32\n\
.vob 01;32\n\
.qt 01;32\n\
.nuv 01;32\n\
.wmv 01;32\n\
.asf 01;32\n\
.rm 01;32\n\
.rmvb 01;32\n\
.flc 01;32\n\
.avi 01;32\n\
.fli 01;32\n\
.flv 01;32\n\
.gl 01;32\n\
.dl 01;32\n\
.xcf 01;32\n\
.xwd 01;32\n\
.yuv 01;32\n\
.cgm 01;32\n\
.emf 01;32\n\
# http://wiki.xiph.org/index.php/MIME_Types_and_File_Extensions\n\
.axv 01;32\n\
.anx 01;32\n\
.ogv 01;32\n\
.ogx 01;32\n\
# audio formats\n\
.aac 00;36\n\
.au 00;36\n\
.flac 00;36\n\
.m4a 00;36\n\
.mid 00;36\n\
.midi 00;36\n\
.mka 00;36\n\
.mp3 00;36\n\
.mpc 00;36\n\
.ogg 00;36\n\
.ra 00;36\n\
.wav 00;36\n\
# http://wiki.xiph.org/index.php/MIME_Types_and_File_Extensions\n\
.axa 00;36\n\
.oga 00;36\n\
.opus 00;36\n\
.spx 00;36\n\
.xspf 00;36\n'\
> /root/.dircolors && cp /root/.dircolors /home/$USERNAME/.dircolors && chown $USERNAME:$USERNAME /home/$USERNAME/.dircolors


########################################
# fix ldconfig path
########################################
# already exists.
#RUN echo '/usr/local/cuda-11.4/targets/aarch64-linux/lib' > /etc/ld.so.conf.d/nvidia.conf \
#    && echo '/etc/ld.so.conf.d/aarch64-linux-gnu.conf\n\
# Multiarch support\n\
#/lib/aarch64-linux-gnu\n\
#/usr/lib/aarch64-linux-gnu\n'\
#> /etc/ld.so.conf.d/aarch64-linux-gnu.conf \
#  ldconfig


########################################
# Default Command
########################################
#CMD bash -c "/usr/bin/xterm -fa 'Monospace' -fs 10"
CMD bash -c "/bin/bash"


### END GUI ###

########################################
# Packages
########################################
RUN apt-get update \
    # DeepStream Python Apps
    # このコンテナはaptパッケージ再インストールする必要があります
    # https://github.com/NVIDIA-AI-IOT/deepstream_python_app
    # version: 1.1.6 for DS6.2
    && apt-get install --reinstall -y \
      libx264-155 \
    && /opt/nvidia/deepstream/deepstream-6.2/user_deepstream_python_apps_install.sh -v 1.1.6 \
    # install opencv from l4t repository
    # install NVIDIA L4T OpenCV (with GStreamer support)
    && apt-get purge -y '*opencv*' || echo "previous OpenCV installation not found" \
    && apt-get install -y --no-install-recommends \
      libopencv \
      libopencv-dev \
      libopencv-python \
      libopencv-samples \
      opencv-licenses \
    # Packages
    && apt-get install -y \
      arp-scan \
      autoconf \
      bc \
      build-essential \
      clang-8 \
      colortest \
      curl \
      dialog \
      g++-8 \
      gcc-8 \
      gettext-base \
      gfortran \
      gfortran-8 \
      git \
      gnupg2 \
      hdf5-tools \
      htop \
      iputils-ping \
      less \
      libavcodec-dev \
      libavcodec-extra \
      libavcodec-extra58 \
      libavformat-dev \
      libblas-dev \
      libbz2-dev \
      libcairo2-dev \
      libc++-dev \
      libcgal-dev \
      libcurl4-openssl-dev \
      libffi-dev \
      libfreetype6-dev \
      libgeos-dev \
      libgirepository1.0-dev \
      libhdf5-dev \
      libhdf5-serial-dev \
      libjpeg8-dev \
      libjpeg-dev \
      liblapack-dev \
      liblzma-dev \
      libmtdev-dev \
      libncurses5-dev \
      libncursesw5-dev \
      libopenblas-dev \
      libopenmpi-dev \
      libpng-dev \
      libportmidi-dev \
      libprotobuf-dev \
      libpython3-dev \
      libreadline-dev \
      libsdl2-dev \
      libsdl2-gfx-dev \
      libsdl2-image-dev \
      libsdl2-mixer-dev \
      libsdl2-net-dev \
      libsdl2-ttf-dev \
      libsqlite3-dev \
      libssl-dev \
      libswscale-dev \
      libxml2-dev \
      libxslt1-dev \
      libxslt-dev \
      lld-8 \
      locales \
      locate \
      lsb-release \
      mediainfo \
      moreutils \
      net-tools \
      ninja-build \
      openmpi-bin \
      openmpi-doc \
      openssl \
      pandoc \
      pkg-config \
      protobuf-compiler \
      python3-dev \
      python3-gi \
      python3-gst-1.0 \
      python3-pip \
      python3-tk \
      python-openssl \
      rsync \
      scons \
      ssh \
      texlive \
      texlive-fonts-extra \
      texlive-fonts-recommended \
      texlive-xetex \
      tree \
      unzip \
      v4l-utils \
      vim \
      wget \
      zip \
      zlib1g-dev \
    && apt autoremove -y \
    && rm -rf /var/lib/apt/lists/*


########################################
# set default gcc version to 9
########################################
RUN update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-9 9 \
    && update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-9 9 \
    && update-alternatives --set gcc /usr/bin/gcc-9 \
    && update-alternatives --set g++ /usr/bin/g++-9


########################################
# ~/.vimrc
########################################
USER $USERNAME
RUN echo 'syntax enable\n\
set background=dark'\
>  ~/.vimrc
USER root
RUN echo 'syntax enable\n\
set background=dark'\
>  ~/.vimrc


########################################
# CMake 3.26.5
########################################
USER $USERNAME
RUN mkdir -p ~/github \
    && cd ~/github \
    && sudo apt-get update \
    && sudo apt-get remove -y \
      cmake \
    && git clone https://github.com/Kitware/CMake.git --depth 1 -b v3.26.5 \
    && cd CMake \
    && ./bootstrap --system-curl \
    && make -j$(nproc) \
    && sudo make install \
    && rm -rf ~/github \
    && sudo apt autoremove -y \
    && sudo rm -rf /var/lib/apt/lists/*

#ARG OPENBLAS_CORETYPE=ARMV8


########################################
# pip
########################################
ARG VENV=python3
RUN sudo mkdir /virtualenv \
    && sudo chown $USERNAME:$USERNAME /virtualenv
USER $USERNAME


# python3 -m virtualenv -p python3 /virtualenv/$VENV --system-site-packages
# これはsystem-site-packagesを引き継ぐ設定。しかし、これは~/.local/lib/python3.6/site-packages/以下にコピーされる
# ~/.local/というのが問題になる。ユーザ個別設定となる。ここにあるライブラリをROS2で使いたい場合に、環境変数PYTHONPATHで指定する必要がある。
# 特定ユーザのホームディレクトリにあるPATHを指定するということは避けたい。そのため--system-site-packagesは指定しない。
# すべてのpipライブラリは作成した/virtualenv/python3/lib/python3.6/site-packages/以下に完結するように管理する
# --system-site-packagesは引き継がないことにする。理由はsetuptoolsのバージョンが低いため。system側のsetuptoolsを更新する必要が生じてしまう。
# https://github.com/pypa/setuptools/issues/1694#issuecomment-466010982
#    && python3 -m virtualenv -p python3 /virtualenv/$VENV --system-site-packages \
RUN pip3 install virtualenv \
   && export VENV_PROMPT=`python3 -V 2>&1 | awk '{print $1$2}' | tr P p` \
   && python3 -m virtualenv -p python3 /virtualenv/$VENV --prompt $VENV_PROMPT \
   && echo "source /virtualenv/$VENV/bin/activate" >> ~/.bashrc


# numpy/core/src/multiarray/numpyos.c:18:10: fatal error: xlocale.h: No such file or directory
# #include <xlocale.h>
RUN sudo ln -s /usr/include/locale.h /usr/include/xlocale.h


########################################
# OpenCV, TensorRT to Python virtualenv 
########################################
RUN sudo ln -s /usr/lib/python3.8/dist-packages/cv2 /virtualenv/$VENV/lib/python3.8/site-packages/cv2 \
    && sudo ln -s /usr/local/lib/python3.8/dist-packages/graphsurgeon /virtualenv/$VENV/lib/python3.8/site-packages/graphsurgeon \
    && sudo ln -s /usr/local/lib/python3.8/dist-packages/tensorrt /virtualenv/$VENV/lib/python3.8/site-packages/tensorrt \
    && sudo ln -s /usr/local/lib/python3.8/dist-packages/uff /virtualenv/$VENV/lib/python3.8/site-packages/uff


##############################
# https://stackoverflow.com/questions/4011705/python-the-imagingft-c-module-is-not-installed
# https://hideharaaws.hatenablog.com/entry/2016/04/25/173153
# ImportError: The _imagingft C module is not installed
# freetypeを利用できないpillowがある。8.4.0を指定すると回避できる。
##############################
RUN . /virtualenv/$VENV/bin/activate \
    && pip install --no-cache-dir \
      beautifulsoup4==4.12.0 \
      Cython==0.29.33 \
      certifi==2022.12.7 \
      cffi==1.15.1 \
      charset-normalizer==2.0.12 \
      cryptography==40.0.2 \
      distro==1.8.0 \
      filelock==3.4.1 \
      gdown==4.6.4 \
      httplib2==0.22.0 \
      idna==3.4 \
      importlib-metadata==4.8.3 \
      importlib-resources==5.4.0 \
      jeepney==0.7.1 \
      keyring==23.4.1 \
      launchpadlib==1.10.16 \
      lazr.restfulclient==0.14.5 \
      lazr.uri==1.0.6 \
      numpy==1.19.4 \
      oauthlib==3.2.2 \
      pbr==5.11.1 \
      pip==21.3.1 \
      pycparser==2.21 \
      pyparsing==3.0.9 \
      PySocks==1.7.1 \
      requests==2.27.1 \
      SecretStorage==3.3.3 \
      setuptools==59.6.0 \
      six==1.16.0 \
      soupsieve==2.3.2.post1 \
      testresources==2.0.1 \
      tqdm==4.64.1 \
      typing_extensions==4.1.1 \
      urllib3==1.26.15 \
      wadllib==1.3.6 \
      wheel==0.37.1 \
      zipp==3.6.0


RUN . /virtualenv/$VENV/bin/activate \
    && pip install --no-deps --no-cache-dir \
      absl-py==0.12.0 \
      Adafruit-Blinka==6.11.1 \
      adafruit-circuitpython-busdevice==5.1.2 \
      adafruit-circuitpython-framebuf==1.4.14 \
      adafruit-circuitpython-lis3dh==5.1.18 \
      adafruit-circuitpython-motor==3.3.5 \
      adafruit-circuitpython-pca9685==3.4.1 \
      adafruit-circuitpython-register==1.9.8 \
      adafruit-circuitpython-servokit==1.3.8 \
      adafruit-circuitpython-ssd1306==2.12.10 \
      Adafruit-GPIO==1.0.3 \
      Adafruit-MotorHAT==1.4.0 \
      Adafruit-PCA9685==1.0.1 \
      Adafruit-PlatformDetect==3.19.6 \
      Adafruit-PureIO==1.1.9 \
      Adafruit-SSD1306==1.6.2 \
      aiocontextvars==0.2.2 \
      anyio==3.6.2 \
      appdirs==1.4.4 \
      argon2-cffi==21.3.0 \
      argon2-cffi-bindings==21.2.0 \
      arrow==1.2.3 \
      astroid==2.11.7 \
      astunparse==1.6.3 \
      async-generator==1.10 \
      attrs==22.2.0 \
      Babel==2.11.0 \
      backcall==0.2.0 \
      binaryornot==0.4.4 \
      bleach==4.1.0 \
      blis==0.7.9 \
      bokeh==2.3.3 \
      cached-property==1.5.2 \
      cachetools==4.2.4 \
      catalogue==2.0.8 \
      cffi==1.15.1 \
      chardet==4.0.0 \
      clang==5.0 \
      click==8.0.4 \
      cloudpickle==2.2.0 \
      confection==0.0.4 \
      contextvars==2.4 \
      cookiecutter==1.7.3 \
      cycler==0.11.0 \
      cymem==2.0.7 \
      decorator==4.4.2 \
      defusedxml==0.7.1 \
      Deprecated==1.2.13 \
      deprecation==2.1.0 \
      dill==0.3.4 \
      docopt==0.6.2 \
      docutils==0.18.1 \
      entrypoints==0.4 \
      evdev==1.6.1 \
      fastai==2.7.12 \
      fastbook==0.0.20 \
      fastcore==1.5.29 \
      fastdownload==0.0.7 \
      fastprogress==1.0.3 \
      fastrelease==0.1.17 \
      flatbuffers==2.0.7 \
      future==0.18.2 \
      gast==0.4.0 \
      ghapi==0.1.22 \
      google-auth==2.16.2 \
      google-auth-oauthlib==0.4.6 \
      google-pasta==0.2.0 \
      graphviz==0.19.1 \
      grpcio==1.48.2 \
      gym==0.26.2 \
      gym-notices==0.0.8 \
      h5py==3.9.0 \
      imagecorruptions==1.1.2 \
      imageio==2.31.1 \
      imageio-ffmpeg==0.4.8 \
      imgaug==0.4.0 \
      immutables==0.19 \
      ipykernel==5.5.6 \
      ipython==7.16.3 \
      ipython-genutils==0.2.0 \
      ipywidgets==7.7.4 \
      isort==5.10.1 \
      jedi==0.17.2 \
      Jetson.GPIO==2.1.2 \
      Jinja2==3.0.3 \
      jinja2-time==0.2.0 \
      joblib==1.1.1 \
      json5==0.9.11 \
      jsonschema==3.2.0 \
      jupyter==1.0.0 \
      jupyter-bokeh==3.0.3 \
      jupyter-client==6.1.12 \
      jupyter-console==6.4.2 \
      jupyter-core==4.9.2 \
      jupyterlab==3.2.9 \
      jupyterlab-pygments==0.1.2 \
      jupyterlab-server==2.10.3 \
      jupyterlab-widgets==1.1.3 \
      jupyter-packaging==0.10.6 \
      jupyter-server==1.13.1 \
      keras==2.6.0 \
      Keras-Applications==1.0.8 \
      Keras-Preprocessing==1.1.2 \
      Kivy==2.2.1 \
      Kivy-Garden==0.1.5 \
      kiwisolver==1.3.1 \
      langcodes==3.3.0 \
      lazy_loader==0.3 \
      lazy-object-proxy==1.7.1 \
      loguru==0.6.0 \
      Mako==1.1.6 \
      Markdown==3.3.7 \
      MarkupSafe==2.0.1 \
      matplotlib==3.3.4 \
      mccabe==0.7.0 \
      mistune==0.8.4 \
      mock==3.0.5 \
      moviepy==1.0.3 \
      mpmath==1.3.0 \
      murmurhash==1.0.8 \
      nbclassic==0.3.5 \
      nbclient==0.5.9 \
      nbconvert==5.6.1 \
      nbdev==1.1.23 \
      nbformat==5.1.3 \
      nest-asyncio==1.5.6 \
      netron==7.0.9 \
      networkx==3.1 \
      notebook==6.4.10 \
      onnx==1.11.0 \
      opt-einsum==3.3.0 \
      packaging==21.3 \
      paho-mqtt==1.6.1 \
      pandas==1.1.5 \
      pandocfilters==1.5.0 \
      parso==0.7.1 \
      pathy==0.10.1 \
      pexpect==4.8.0 \
      pgi==0.0.11.2 \
      pickleshare==0.7.5 \
      Pillow==9.4.0 \
      pkgconfig==1.5.5 \
      platformdirs==2.4.0 \
      plotly==5.13.1 \
      poyo==0.5.0 \
      preshed==3.0.8 \
      prettytable==2.5.0 \
      proglog==0.1.10 \
      progress==1.6 \
      prometheus-client==0.16.0 \
      prompt-toolkit==3.0.36 \
      protobuf==3.19.6 \
      psutil==5.9.2 \
      ptyprocess==0.7.0 \
      pyasn1==0.4.8 \
      pyasn1-modules==0.2.8 \
      pybind11==2.10.4 \
      pycairo==1.20.1 \
      pycocotools==2.0.6 \
      pycuda==2022.1 \
      pydantic==1.9.2 \
      pyfiglet==0.8.post1 \
      pyftdi==0.53.3 \
      pygame==2.3.0 \
      Pygments==2.14.0 \
      PyGObject==3.42.2 \
      pylint==2.13.9 \
      pyquaternion==0.9.9 \
      pyrsistent==0.18.0 \
      pyserial==3.5 \
      python-dateutil==2.8.2 \
      python-slugify==6.1.2 \
      pytools==2022.1.12 \
      pytorchcv==0.0.67 \
      pytz==2022.7.1 \
      pyusb==1.2.1 \
      PyWavelets==1.1.1 \
      PyYAML==6.0 \
      pyzmq==25.0.2 \
      qtconsole==5.2.2 \
      QtPy==2.0.1 \
      reportlab==3.6.8 \
      requests-oauthlib==1.3.1 \
      RPi.GPIO==0.7.1 \
      rsa==4.9 \
      scikit-image==0.21.0 \
      scikit-learn==1.3.0 \
      scipy==1.5.4 \
      seaborn==0.11.2 \
      Send2Trash==1.8.0 \
      sentencepiece==0.1.97 \
      Shapely==1.8.5.post1 \
      simple-pid==1.0.1 \
      smart-open==6.3.0 \
      smbus==1.1.post2 \
      sniffio==1.2.0 \
      spacy==3.5.1 \
      spacy-legacy==3.0.12 \
      spacy-loggers==1.0.4 \
      spidev==3.5 \
      srsly==2.4.6 \
      sympy==1.12 \
      tabulate==0.8.10 \
      tenacity==8.2.2 \
      termcolor==1.1.0 \
      terminado==0.12.1 \
      testpath==0.6.0 \
      text-unidecode==1.3 \
      tf2onnx==1.14.0 \
      tf-keras-vis==0.6.2 \
      thinc==8.1.9 \
      thop==0.1.1.post2209072238 \
      threadpoolctl==3.1.0 \
      tifffile==2023.7.10 \
      tomli==1.2.3 \
      tomlkit==0.11.6 \
      tornado==6.1 \
      traitlets==4.3.3 \
      typed-ast==1.5.4 \
      typer==0.7.0 \
      wasabi==1.1.1 \
      wcwidth==0.2.6 \
      webencodings==0.5.1 \
      websocket-client==1.3.1 \
      Werkzeug==2.0.3 \
      widgetsnbextension==3.6.3 \
      wrapt==1.14.1


########################################
# nodejs
########################################
# https://github.com/nodesource/distributions/blob/master/README.md
# https://deb.nodesource.com/setup_14.x - Node.js 14 LTS "Fermium" (recommended)
# https://deb.nodesource.com/setup_16.x - Node.js 16 "Gallium"
# https://deb.nodesource.com/setup_18.x - Node.js 18 "Eighteen" (current)

RUN curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash - \
    && sudo apt-get update \
    && sudo apt-get install -y \
         nodejs \
    && sudo apt autoremove -y \
    && sudo rm -rf /var/lib/apt/lists/*


########################################
# JupyterLab save to pdf
########################################
#RUN mkdir -p ~/github \
#    && cd ~/github \
#    && git clone https://github.com/qpdf/qpdf \
#    && cd qpdf \
#    && cmake -S . -B build -DCMAKE_BUILD_TYPE=RelWithDebInfo \
#    && cmake --build build \
#    && sudo cmake --install build


#pip install pdfrw # for python2.6-3.6
#pip install PyPDF2 # for python2.7-3.10
#pip install pikepdf # for python3.7-3.10

# jupyter nbconvert --to pdf notebook.ipynb


########################################
# jupyter_clickable_image_widget
########################################
RUN . /virtualenv/$VENV/bin/activate \
    && mkdir -p ~/github \
    && cd ~/github \
    && git clone -b jupyterlab-3 https://github.com/naisy/jupyter_clickable_image_widget \
    && cd jupyter_clickable_image_widget/js \
    && npm install -D webpack-cli@5.1.4 \
    && cd .. \
    && pip install -e . \
    && jupyter labextension install @jupyter-widgets/jupyterlab-manager@3.0.0 \
    && jupyter labextension install js \
    && jupyter-lab build

#インストール済みの@jupyter-widgets/jupyterlab-managerの情報
#npm list @jupyter-widgets/jupyterlab-manager
#npm list -g @jupyter-widgets/jupyterlab-manager
#jupyter labextension list


########################################
# Jupyter Lab 設定
########################################
RUN . /virtualenv/$VENV/bin/activate \
    ####################
    # Jupyter Lab Vertual Env
    # To set the virtualenv as "python3", jupyter notebooks works in virtualenv.
    ####################
    && python -m ipykernel install --name python3 --user \
    ####################
    # Jupyter Lab password 設定
    ####################
    && mkdir -p $HOME/.jupyter \
    && python -c "from notebook.auth.security import set_password; set_password('jupyter', '$HOME/.jupyter/jupyter_notebook_config.json')" \
    ####################
    # Disable Jupyter autosave
    ####################
    && mkdir -p ~/.jupyter/lab/user-settings/\@jupyterlab/docmanager-extension \
    && echo '{\n\
    // Document Manager\n\
    // @jupyterlab/docmanager-extension:plugin\n\
    // Document Manager settings.\n\
    // ***************************************\n\
\n\
    // Autosave Documents\n\
    // Whether to autosave documents\n\
    "autosave": false\n\
}'\
>  ~/.jupyter/lab/user-settings/\@jupyterlab/docmanager-extension/plugin.jupyterlab-settings \
    ####################
    # Jupyter Dark Terminal Theme
    ####################
    && mkdir -p ~/.jupyter/lab/user-settings/\@jupyterlab/terminal-extension \
    && echo '{\n\
    // Terminal\n\
    // @jupyterlab/terminal-extension:plugin\n\
    // Terminal settings.\n\
    // *************************************\n\
\n\
    // Theme\n\
    // The theme for the terminal.\n\
    "theme": "dark"\n\
}'\
>  ~/.jupyter/lab/user-settings/\@jupyterlab/terminal-extension/plugin.jupyterlab-settings \
    ####################
    # Jupyter Console System Color Tango to Rxvt-LightBlue/Aquamarine
    ####################
    # ファイル名がわからん。インストールで変わる。
    # find /usr/local/share/jupyter/lab/static/ -type f | xargs grep -l "#2e3436"
    # /usr/local/share/jupyter/lab/static/vendors~main.23ff2294e1453ac6af20.js
    #export JUPYTER_TERMINAL_COLOR_FILE=`find /usr/local/share/jupyter/lab/static/ -type f -name "*\.js" | xargs -I {} grep -l "#3465a4" {}` \
    && export JUPYTER_TERMINAL_COLOR_FILE=`find /virtualenv/$VENV/share/jupyter/lab/static/ -type f -name "*\.js" | xargs -I {} grep -l "#3465a4" {}` \
    && sed -i 's/#2e3436/#000000/g' $JUPYTER_TERMINAL_COLOR_FILE \
    && sed -i 's/#cc0000/#cd0000/g' $JUPYTER_TERMINAL_COLOR_FILE \
    && sed -i 's/#4e9a06/#00cd00/g' $JUPYTER_TERMINAL_COLOR_FILE \
    && sed -i 's/#c4a000/#cdcd00/g' $JUPYTER_TERMINAL_COLOR_FILE \
    && sed -i 's/#3465a4/#add8e6/g' $JUPYTER_TERMINAL_COLOR_FILE \
    && sed -i 's/#75507b/#cd00cd/g' $JUPYTER_TERMINAL_COLOR_FILE \
    && sed -i 's/#06989a/#00cdcd/g' $JUPYTER_TERMINAL_COLOR_FILE \
    && sed -i 's/#d3d7cf/#faebd7/g' $JUPYTER_TERMINAL_COLOR_FILE \
    && sed -i 's/#555753/#404040/g' $JUPYTER_TERMINAL_COLOR_FILE \
    && sed -i 's/#ef2929/#ff0000/g' $JUPYTER_TERMINAL_COLOR_FILE \
    && sed -i 's/#8ae234/#00ff00/g' $JUPYTER_TERMINAL_COLOR_FILE \
    && sed -i 's/#fce94f/#ffff00/g' $JUPYTER_TERMINAL_COLOR_FILE \
    && sed -i 's/#729fcf/#7fffd4/g' $JUPYTER_TERMINAL_COLOR_FILE \
    && sed -i 's/#ad7fa8/#ff00ff/g' $JUPYTER_TERMINAL_COLOR_FILE \
    && sed -i 's/#34e2e2/#00ffff/g' $JUPYTER_TERMINAL_COLOR_FILE \
    && sed -i 's/#eeeeec/#ffffff/g' $JUPYTER_TERMINAL_COLOR_FILE


########################################
# Launch JupyterLab from virtualenv with root dir and default dir
########################################
# https://stackoverflow.com/questions/69038787/how-to-set-default-folder-in-jupyterlab-file-browser
#CMD . /virtualenv/python3/bin/activate && exec bash -c "jupyter-lab --ip=0.0.0.0 --no-browser --ServerApp.root_dir=/ --LabApp.default_url=/lab?file-browser-path=$HOME/data/Notebooks"
CMD . /virtualenv/python3/bin/activate && exec bash -c "jupyter lab --ip=0.0.0.0 --no-browser --ServerApp.root_dir=/ --LabApp.default_url=/lab?file-browser-path=$HOME"


########################################
# pytorch v2.0.0
########################################
RUN . /virtualenv/$VENV/bin/activate \
    && cd ~/ \
    && wget https://developer.download.nvidia.cn/compute/redist/jp/v511/pytorch/torch-2.0.0+nv23.05-cp38-cp38-linux_aarch64.whl -O torch-2.0.0+nv23.05-cp38-cp38-linux_aarch64.whl \
    && pip install torch-2.0.0+nv23.05-cp38-cp38-linux_aarch64.whl \
    && rm -rf torch-2.0.0+nv23.05-cp38-cp38-linux_aarch64.whl


########################################
# torchvision v0.15.2
########################################
# Compute Capability
# AGX Orin: 8.7
# AGX Xavier: 7.2
# TX2: 6.2
# Nano: 5.3

# ビルドする場合
#RUN . /virtualenv/$VENV/bin/activate \
#    && mkdir -p ~/github \
#    && cd ~/github \
#    && git clone -b v0.15.2 https://github.com/pytorch/vision \
#    && cd vision \
#    && export BUILD_VERSION=0.15.2 USE_CUDA=1 USE_CUDNN=1 TORCH_CUDA_ARCH_LIST="8.7 7.2" \
#    && export Torch_DIR=/virtualenv/$VENV/lib/python3.8/site-packages/torch \
#    && python setup.py bdist_wheel \
#    && pip install dist/torchvision-0.15.2-cp38-cp38-linux_aarch64.whl
 
# ビルド済みパッケージ
RUN . /virtualenv/$VENV/bin/activate \
    && cd ~/ \
    && gdown https://drive.google.com/uc?id=1LT_wqGZ_RfnLkc6fzCbjT3MDPZCgiKv6 -O torchvision-0.15.2-cp38-cp38-linux_aarch64.whl \
    && pip install torchvision-0.15.2-cp38-cp38-linux_aarch64.whl \
    && rm torchvision-0.15.2-cp38-cp38-linux_aarch64.whl


########################################
# torch2trt
########################################
RUN . /virtualenv/$VENV/bin/activate \
    && cd ~/github \
    && git clone https://github.com/NVIDIA-AI-IOT/torch2trt \
    && cd torch2trt \
    && pip install --install-option="--plugins" .


########################################
# models
########################################
#RUN python -c "import torchvision; \
#                model = torchvision.models.alexnet(pretrained=True); \
#                model = torchvision.models.squeezenet1_1(pretrained=True); \
#                model = torchvision.models.resnet18(pretrained=True); \
#                model = torchvision.models.resnet34(pretrained=True)"
RUN . /virtualenv/$VENV/bin/activate \
    && python -c "import torchvision; \
         model = torchvision.models.resnet18(pretrained=True); \
         model = torchvision.models.resnet50(pretrained=True)"


########################################
# JetRacer
########################################
RUN . /virtualenv/$VENV/bin/activate \
    && cd ~/github \
    && git clone https://github.com/FaBoPlatform/jetracer \
    && cd jetracer \
    && pip install -e . \
    && cp -r notebooks ~/notebooks


########################################
# JetCam
########################################
RUN . /virtualenv/$VENV/bin/activate \
    && cd ~/github \
    && git clone https://github.com/NVIDIA-AI-IOT/jetcam \
    && cd jetcam \
    && pip install -e .


########################################
# JupyterLab Password
########################################
RUN . /virtualenv/$VENV/bin/activate \
    && python -c "from notebook.auth.security import set_password; set_password('jetson', '$HOME/.jupyter/jupyter_notebook_config.json')" \


########################################
# Tensorflow
########################################
RUN . /virtualenv/$VENV/bin/activate \
    && pip install --extra-index-url https://developer.download.nvidia.com/compute/redist/jp/v511 tensorflow==2.12.0+nv23.05

########################################
# DonkeyCar 4.4
########################################
RUN . /virtualenv/$VENV/bin/activate \
    && cd ~/github \
    && git clone -b release_4_4 https://github.com/autorope/donkeycar \
    && cd donkeycar \
    && sed -i '/imgaug/d' setup.py \
    && sed -i '/pillow/d' setup.py \
    && pip install -e .


########################################
# DonkeyCar 4.5
########################################
#RUN . /virtualenv/$VENV/bin/activate \
#    && cd ~/github \
#    && git clone -b release_4_5 https://github.com/autorope/donkeycar \
#    && cd donkeycar \
#    && sed -i '/imgaug/d' setup.py \
#    && sed -i '/pillow/d' setup.py \
#    && sed -i '/numpy/d' setup.py \
#    && pip install -e .


RUN . /virtualenv/$VENV/bin/activate \
    && cd ~/github \
    && git clone https://github.com/tawnkramer/gym-donkeycar \
    && cd gym-donkeycar \
    && sed -i 's|^requirements = \["gym==0.21", "numpy", "pillow"\]|requirements = []|g' setup.py \
    && pip install -e .
