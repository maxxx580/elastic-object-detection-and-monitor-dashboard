#!/bin/bash
fileid="1C6SoDNTcWRSCPDD1zbrECIbRtqXMUSD_"
filename="app/yolo-coco/yolov3.weights"
curl -c ./cookie -s -L "https://drive.google.com/uc?export=download&id=${fileid}" > /dev/null
curl -Lb ./cookie "https://drive.google.com/uc?export=download&confirm=`awk '/download/ {print $NF}' ./cookie`&id=${fileid}" -o ${filename}
