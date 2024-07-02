import json

import openpyxl
import openai
import requests
from config import Config
import nltk
nltk.download('punkt')
import re
import transformers
import torch
import google.generativeai as genai
import anthropic
genai.configure(api_key=Config.gemini_api_key)
openai.api_key = Config.openai_api_key


def parse_tps(output_json, sts):
    pattern = r'"Opportunity": (\d+),\s*"Change of Plans": (\d+),\s*"Point of No Return": (\d+),\s*"Major Setback": (\d+),\s*"Climax": (\d+)'

    # Find all matches using regex
    matches = re.search(pattern, output_json)

    if matches:
        # Extract numeric values for each key
        opportunity = sts[int(matches.group(1))]
        change_of_plans = sts[int(matches.group(2))]
        point_of_no_return = sts[int(matches.group(3))]
        major_setback = sts[int(matches.group(4))]
        climax = sts[int(matches.group(5))]
    return {"Opportunity": opportunity, "Change of Plans": change_of_plans, "Point of No Return": point_of_no_return, "Major Setback": major_setback, "Climax": climax}

def write_dict_to_json_file(dictionary, file_path):
    """
    Writes a given dictionary to a JSON file.

    Args:
        dictionary (dict): The dictionary to write to the JSON file.
        file_path (str): The path of the JSON file to write to.
    """
    with open(file_path, 'w') as json_file:
        json.dump(dictionary, json_file, indent=4)
def write_to_file(title, tps, output_folder):
    file_path = output_folder +title   # file path here

    with open(file_path, "w", encoding="utf-8") as f:  # Use "a" mode to append to the file
        f.write("{}\t{}\n".format(title, tps))
def get_LLM_response(context_prompt, synopsis_prompt, title, model):
    if "gpt" in model.lower():
        gen_turning_points = openai.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": context_prompt},
                      {"role": "user", "content": synopsis_prompt}],
            max_tokens=1000,
            temperature=1.0,

        )
        rt = (title, gen_turning_points.choices[0].message.content)
    elif "llama" in model.lower():
        model_id = Config.llama3_path +"/Meta-Llama-3-8B-Instruct"

        pipeline = transformers.pipeline(
            "text-generation",
            model=model_id,
            model_kwargs={"torch_dtype": torch.bfloat16},
            device_map="auto",
        )

        messages = [
            {"role": "system", "content": context_prompt},
            {"role": "user", "content": synopsis_prompt},
        ]

        prompt = pipeline.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )

        terminators = [
            pipeline.tokenizer.eos_token_id,
            pipeline.tokenizer.convert_tokens_to_ids("<|eot_id|>")
        ]

        outputs = pipeline(
            prompt,
            max_new_tokens=2000,
            eos_token_id=terminators,
            do_sample=True,
            temperature=0.6,
            top_p=0.9,
        )
        rt = (title, outputs[0]["generated_text"][len(prompt):])
    elif "claude" in model.lower():

        client = anthropic.Client(api_key=Config.claude_api_key)

        response = client.messages.create(
            model="claude-3-opus-20240229",
            system=context_prompt,  # <-- system prompt
            messages=[
                {"role": "user", "content": synopsis_prompt}  # <-- user prompt
            ],
            max_tokens=2000
        )
        # embed()
        rt = (title, response.content[0].text)
    elif "gemini" in model.lower():
        """
        At the command line, only need to run once to install the package via pip:

        $ pip install google-generativeai
        """
        # Set up the model
        generation_config = {
            "temperature": 1,
            "top_p": 0.95,
            "top_k": 0,
            "max_output_tokens": 2000,
        }

        system_instruction = context_prompt

        model = genai.GenerativeModel(model_name="gemini-1.5-pro-latest",
                                      generation_config=generation_config,
                                      system_instruction=system_instruction,
                                      )

        convo = model.start_chat(history=[
        ])

        convo.send_message(synopsis_prompt)
        rt = (title, convo.last.text)
    else:
        assert False, "Model not supported"
    return rt

def parse_tps(output_json):
    try:
        pattern = r'"Opportunity": (\d+),\s*"Change of Plans": (\d+),\s*"Point of No Return": (\d+),\s*"Major Setback": (\d+),\s*"Climax": (\d+)'
        # Find all matches using regex
        matches = re.search(pattern, output_json)
    except:
        pattern = r"\'Opportunity\':\s*(\d+),\s*\'Change of Plans\':\s*(\d+),\s*\'Point of No Return\':\s*(\d+),\s*\'Major Setback\':\s*(\d+),\s*\'Climax\':\s*(\d+)"
        # Find all matches using regex
        matches = re.search(pattern, output_json)
    
    

    if matches:
        # Extract numeric values for each key
        opportunity = int(matches.group(1))
        change_of_plans = int(matches.group(2))
        point_of_no_return = int(matches.group(3))
        major_setback = int(matches.group(4))
        climax = int(matches.group(5))
    return {"Opportunity": opportunity, "Change of Plans": change_of_plans, "Point of No Return": point_of_no_return, "Major Setback": major_setback, "Climax": climax}
def split_corpus_into_sentences(corpus):
    """
    Split a corpus into sentences.

    Args:
    - corpus (str): The input text corpus.

    Returns:
    - List of sentences (str).
    """
    sentences = corpus.split("[STR_SENT]")[1:]

    sentences = [f"{i+1}. {s.strip(' [END_SENT]')}" for i, s in enumerate(sentences)]
    return sentences
def get_subj_emo(st):
    inference = comet_model.predict(st, "xReact", num_beams=3)
    return inference
def parse_xlsx(file_path):
    # Load the workbook
    workbook = openpyxl.load_workbook(file_path)

    # Select the first worksheet
    worksheet = workbook.worksheets[0]

    # Read and store the data
    data = []
    for row in worksheet.iter_rows(values_only=True):
        data.append(row)

    # Close the workbook
    workbook.close()
    keys = data[0]  # First row as keys
    dict_list = [dict(zip(keys, values)) for values in data[1:]]  # Remaining rows as values

    return dict_list

def get_protagonist(sts, api_key=Config.openai_api_key):
    """
    Call ChatGPT 3.5 using the OpenAI API.

    Args:
    - prompt (str): The input text prompt for generating text.
    - api_key (str): Your OpenAI API key.

    Returns:
    - str: The generated text response from ChatGPT 3.5.
    """
    prompt = """
             Who is the main character of the this story?
             The output should just be a name.\n\n"""+ str(sts)

    openai.api_key = api_key

    url = "https://api.openai.com/v1/chat/completions"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    data = {
        "model": "gpt-4-turbo",
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        return(response.json()['choices'][0]['message']['content'])
    else:
        return("Error:", response.status_code, response.text)

def get_character_emo(st, character, api_key=Config.openai_api_key):
    """
    Call ChatGPT 3.5 using the OpenAI API.

    Args:
    - prompt (str): The input text prompt for generating text.
    - api_key (str): Your OpenAI API key.

    Returns:
    - str: The generated text response from ChatGPT 3.5.
    """
    prompt = "How does "+\
             character+" feel in this sentence? "+st+"\n\
              Use three different words to describe the character's feeling. The output should be a list of words.  For example, [happy, sad, joyful].\n\nReturn your answer below. Do not include other outputs."


    openai.api_key = api_key

    url = "https://api.openai.com/v1/chat/completions"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    data = {
        "model": "gpt-4-turbo",
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant in identifying emotions."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    }

    response = requests.post(url, headers=headers, json=data)

    # Check if the request was successful
    if response.status_code == 200:
        return(response.json()['choices'][0]['message']['content'])
    else:
        return("Error:", response.status_code, response.text)

