#!/bin/bash

# thin wrapper around populate_ranked_words_list.py

# first argument is a language code

# assumes https://github.com/hermitdave/FrequencyWords 
# exists at ../../../FrequencyWords/ 

if [ $# -eq 0 ]
  then
    echo "Please pass a language code as argument"
fi

python populate_ranked_words_list.py $1 ../../../FrequencyWords/content/2016/$1/$1_50k.txt 10000 
