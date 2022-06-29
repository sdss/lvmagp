#!/usr/bin/bash

LVMT_PATH=/root/lvmagp
LVMT_RMQ=${LVMT_RMQ:=localhost}

export LVMT_DATA_ROOT="${LVM_DATA_ROOT:=${HOME}/data}"
#echo $LVMT_DATA_ROOT

#echo $LVMT_DEBUG
if [ $LVMT_DEBUG ]; then 
    export PYTHONPATH=$LVMT_PATH/python/
fi

sed "s/host: .*$/host: $LVMT_RMQ/" < $LVMT_PATH/python/lvmagp/etc/$LVMT_CAM.yml \
            > $LVMT_PATH/python/lvmagp/etc/${LVMT_CAM}_${LVMT_RMQ}.yml

python3 $LVMT_PATH/python/lvmagp/__main__.py -c $LVMT_PATH/python/lvmagp/etc/${LVMT_CAM}_${LVMT_RMQ}.yml --verbose start --debug
