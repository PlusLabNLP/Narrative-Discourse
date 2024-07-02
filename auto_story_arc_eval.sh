#!/bin/bash

# Define the list of models
models=('gpt-3.5-turbo' 'gemini' 'claude' 'gpt-4' )

# Iterate over each model and run the Python script in the background
#for model in "${models[@]}"
#do
#    echo "Running tp_annotate_prompt with model: $model"
#    python story_arc_annotate_prompt.py --model "$model" &
#done

# Wait for all background jobs to finish

for model in "${models[@]}"
do
    echo "Running tp_annotate_prompt with model: $model"

    python story_arc_annotate_prompt.py --model "$model" --prior True &
done

wait