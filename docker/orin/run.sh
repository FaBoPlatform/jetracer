#!/bin/bash
########################################
# Rerun the script with root
########################################
if [ "$EUID" -ne 0 ]; then
  sudo "$0" "$@"  # execute script with root
  exit            # exit this user script
fi

XAUTH_FILE=.Xauthority
HOST_USER=$(getent passwd 1000 | cut -d: -f1)
HOST_USER_GROUP=$(getent group 1000 | cut -d: -f1)
HOST_USER_HOME=/home/$HOST_USER
HOST_USER_XAUTH=$HOST_USER_HOME/$XAUTH_FILE
HOST_MOUNT_PATH=$HOST_USER_HOME/data
DOCKER_USER=jetson
DOCKER_USER_HOME=/home/$DOCKER_USER
DOCKER_USER_XAUTH=$DOCKER_USER_HOME/$XAUTH_FILE
DOCKER_MOUNT_PATH=$DOCKER_USER_HOME/data

########################################
# DISPLAY
########################################
DISPLAY=`echo $DISPLAY`
if [ -z $DISPLAY ]; then
    # localhost display
    # Ubuntu 18.04: :0
    # Ubuntu 20.04: :0
    # Ubuntu 22.04: :0
    DISPLAY=:0
fi

########################################
# make .Xauthority
########################################
if [ ! -f $HOST_USER_HOME/$XAUTH_FILE ]; then
    touch $HOST_USER_HOME/$XAUTH_FILE
    chown $HOST_USER:$HOST_USER_GROUP $HOST_USER_HOME/$XAUTH_FILE
    chmod 600 $HOST_USER_HOME/$XAUTH_FILE

    su $HOST_USER -c "xauth generate $DISPLAY . trusted"
fi

########################################
# make ~/data/ localhost <-> docker shared directory
########################################
if [ ! -d "$HOST_MOUNT_PATH" ]; then
    mkdir $HOST_MOUNT_PATH
    chown $HOST_USER:$HOST_USER_GROUP $HOST_MOUNT_PATH
fi

########################################
# docker image
########################################
IMG=faborobot/jetson-jp511-aicar
PORT=8888
NAME="jetracer"

docker run \
    --runtime=nvidia \
    --restart=always \
    -itd \
    --mount type=bind,source=$HOST_USER_XAUTH,target=$DOCKER_USER_XAUTH \
    --mount type=bind,source=$HOST_MOUNT_PATH,target=$DOCKER_MOUNT_PATH \
    -e DISPLAY=$DISPLAY \
    -e OPENBLAS_CORETYPE=ARMV8 \
    -e QT_GRAPHICSSYSTEM=native \
    -e QT_X11_NO_MITSHM=1 \
    -e SHELL=/bin/bash \
    -v /run/user/1000/:/run/user/1000/:ro \
    -v /var/run/dbus/system_bus_socket:/var/run/dbus/system_bus_socket:ro \
    -v /usr/bin/tegrastats:/usr/bin/tegrastats \
    -v /usr/sbin/nvpmodel:/usr/sbin/nvpmodel \
    -v /etc/localtime:/etc/localtime:ro \
    -v /dev/:/dev/ \
    -v /tmp/:/tmp/ \
    -v /etc/nvpmodel.conf:/etc/nvpmodel.conf \
    -v /sys/devices/gpu.0:/sys/devices/gpu.0 \
    -u $DOCKER_USER \
    --privileged \
    --network=host \
    --name="${NAME}" \
$IMG \
bash -c "source /virtualenv/python3/bin/activate && jupyter lab --ip=0.0.0.0 --port=$PORT --no-browser --ServerApp.root_dir=/ --LabApp.default_url=/lab?file-browser-path=$HOST_USER_HOME"
