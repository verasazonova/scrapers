#!/bin/bash
# Command line
# ./fix_ratio <input_file> <output_file>
function scale() {
  GOLDEN_RATIO=1.9
  input=$1
  output=$2
  echo ${input}
  sizes=`magick identify ${input} | awk  '{print $3}' | tr "x" "\n"`
  width=`echo ${sizes} | awk '{print $1}'`
  height=`echo ${sizes} | awk '{print $2}'`
  if [ ${width} -gt ${height} ]; then
    ideal_width=${width}
    ideal_height=`echo "${width} / 1.9" | bc -l`
    ideal_width=${ideal_width%.*}
    ideal_height=${ideal_height%.*}
    if [ ${ideal_height} -lt ${height} ]; then
      diff=`echo "${height} - ${ideal_height}" | bc`
      ideal_height=`echo "${ideal_height} + ${diff}" | bc`
      width_diff=`echo "${diff} * 1.9" | bc`
      ideal_width=`echo "${ideal_width} + ${width_diff}" | bc`
    fi
  else
    ideal_height=${height}
    ideal_width=`echo "${height} * 1.9" | bc -l`
    ideal_width=${ideal_width%.*}
    ideal_height=${ideal_height%.*}
    if [ ${ideal_width} -lt ${width} ]; then
      diff=`echo "${width} - ${ideal_width}" | bc`
      ideal_width=`echo "${ideal_width} + ${diff}" | bc`
      height_diff=`echo "${diff} / 1.9" | bc`
      height_diff=${height_diff%.*}
      ideal_height=`echo "${ideal_height} + ${height_diff}" | bc`
    fi
  fi

  convert -size ${ideal_width}x${ideal_height} canvas:white white.png
  magick composite -gravity center ${1} white.png ${2}
}


for file in images/*; do
  # echo  $file
  # echo images_scaled/${file##*/}
  scale $file images_scaled/${file##*/}
done