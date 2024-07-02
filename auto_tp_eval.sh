#!/bin/bash

# Define the list of models
models=('gemini' 'claude' 'gpt-4')


# Iterate over each model and run the Python script in the background
for model in "${models[@]}"
do
    echo "Running tp_annotate_prompt with model: $model"
    python tp_evaluate_script.py --model "$model" --prior True &
done

# Wait for all background jobs to finish
wait