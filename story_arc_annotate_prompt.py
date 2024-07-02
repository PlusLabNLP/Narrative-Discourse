import json
from time import sleep
import os
from utils import get_LLM_response, write_dict_to_json_file,write_to_file,  parse_xlsx, split_corpus_into_sentences
from tqdm import tqdm
from IPython import embed
def arc_annotate_prompt(movie_tuple, model):
    title, synopsis = movie_tuple

    context_prompt = """### Prompt for LLM: Annotating Story Arcs

#### Objective
Accurately categorize a given story into one of seven defined story arcs based on its narrative structure.

#### Story Arcs:
1. **Rags to Riches:** Protagonist starts in a disadvantaged situation and ends in a much better one.
2. **Riches to Rags:** Protagonist starts in a high-status position but ends in a significantly lower state.
3. **Man in a Hole:** Protagonist falls into a dilemma and finds a way out, ending better than at the beginning.
4. **Icarus:** Protagonist rises to success but then faces a drastic downfall.
5. **Double Man in a Hole:** Protagonist faces two cycles of dilemma and recovery.
6. **Cinderella:** Protagonist rises, faces a setback, and ultimately achieves a higher state.
7. **Oedipus:** Protagonist falls, recovers, and then faces another significant downfall.

#### Annotation Instructions
1. **Read the Story Thoroughly:** Understand the protagonist's journey and key plot points.
2. **Evaluate the Story Arc:**
   - Identify whether the protagonist has a humble start.
   - Determine if the protagonist achieves a significant gain by the end.
   - Track the number of rises and falls in the story arc.
3. **Choose the Most Appropriate Story Arc:**
   - **Primary Arc:** Select the single arc that best fits the story.
   - **Secondary Arc:** Optionally, choose a secondary arc if the story closely aligns with another type.
4. **Provide Justification:**
   - Briefly justify why the chosen arc(s) best represent the narrative structure.

#### Tips
- **Focus on Key Turning Points:** Highlight major changes in the protagonist’s fortune.
- **Draw a Plot Diagram:** Visualization can aid in determining the global plot changes.
- **Distinguish Hard Pairs:**
  - **Man in a Hole vs. Double Man in a Hole:** The difference lies in the number of rises and falls.
  - **Rags to Riches vs. Cinderella:** Consider the timeline and presence of setbacks.

Provide your responses in the following format:
1. **Primary Arc:**
2. **Secondary Arc (if applicable):**
3. **Reasoning:**

#### Annotation Example:
```
1. **Primary Arc:** Man in a Hole
2. **Secondary Arc:** Cinderella
3. **Reasoning:** The story starts with the protagonists being summoned to a crime scene, progresses through dangerous events, and ends with them rewarded for bravery.
```
"""

    synopsis_prompt = """The movie title is {} and the synopsis is: {}.  
    Please identify which ONE or Two story arcs best fit this story.  
    The format of the output should be a JSON object with the Primary Arc, Secondary Arc, and Reasoning as keys.  
    """.format(
        title, synopsis)

    rt = get_LLM_response(context_prompt, synopsis_prompt, title, model)

    return rt

def arc_annotate_with_tp_prior(movie_tuple, tp_d, model):
    # print(movie_tuple)
    title, synopsis = movie_tuple

    context_prompt = """### Prompt for LLM: Annotating Story Arcs

    #### Objective
    Accurately categorize a given story into one of six defined story arcs based on its narrative structure.

    #### Story Arcs:
    1. **Rags to Riches:** Protagonist starts in a disadvantaged situation and ends in a much better one.
    2. **Riches to Rags:** Protagonist starts in a high-status position but ends in a significantly lower state.
    3. **Man in a Hole:** Protagonist falls into a dilemma and finds a way out, ending better than at the beginning.
    4. **Icarus:** Protagonist rises to success but then faces a drastic downfall.
    5. **Double Man in a Hole:** Protagonist faces two cycles of dilemma and recovery.
    6. **Cinderella:** Protagonist rises, faces a setback, and ultimately achieves a higher state.
    7. **Oedipus:** Protagonist falls, recovers, and then faces another significant downfall.

    #### Annotation Instructions
    1. **Read the Story Thoroughly:** Understand the protagonist's journey and key plot points.
    2. **Evaluate the Story Arc:**
       - Identify whether the protagonist has a humble start.
       - Determine if the protagonist achieves a significant gain by the end.
       - Track the number of rises and falls in the story arc.
    3. **Choose the Most Appropriate Story Arc:**
       - **Primary Arc:** Select the single arc that best fits the story.
       - **Secondary Arc:** Optionally, choose a secondary arc if the story closely aligns with another type.
    4. **Provide Justification:**
       - Briefly justify why the chosen arc(s) best represent the narrative structure.

    #### Tips
    - **Focus on Key Turning Points:** Highlight major changes in the protagonist’s fortune.
    - **Draw a Plot Diagram:** Visualization can aid in determining the global plot changes.
    - **Distinguish Hard Pairs:**
      - **Man in a Hole vs. Double Man in a Hole:** The difference lies in the number of rises and falls.
      - **Rags to Riches vs. Cinderella:** Consider the timeline and presence of setbacks.

    Provide your responses in the following format:
    1. **Primary Arc:**
    2. **Secondary Arc (if applicable):**
    3. **Reasoning:**

    #### Annotation Example:
    ```
    1. **Primary Arc:** Man in a Hole
    2. **Secondary Arc:** Cinderella
    3. **Reasoning:** The story starts with the protagonists being summoned to a crime scene, progresses through dangerous events, and ends with them rewarded for bravery.
    ```
    """

    synopsis_prompt = f"""The movie title is {title} and the synopsis is: {synopsis}.  
        Please identify which ONE or Two story arcs best fit this story.  
        The format of the output should be a JSON object with the Primary Arc, Secondary Arc, and Reasoning as keys. 
        
        !!! KEY TO SOLVE THE TASK: Here is some additional information that might help with the task.
        The five turning points are:
        1. Opportunity - Introductory event that occurs after the presentation of the setting and the background of the main characters.
        2. Change of Plans - Event where the main goal of the story is defined. From this point on, the action begins to increase.
        3. Point of No Return - Event that pushes the main character(s) to fully commit to their goal.
        4. Major Setback - Event where everything falls apart (temporarily or permanently).
        5. Climax -Final event of the main story, moment of resolution and the “biggest spoiler”.
        
        Here's a tagged version of the summary based on the turning points. The integer number indicates the position of the sentence:
        Output:  
            "Opportunity": {tp_d['tp1']},
            "Change of Plans": {tp_d['tp2']},
            "Point of No Return": {tp_d['tp3']},
            "Major Setback": {tp_d['tp4']},
            "Climax": {tp_d['tp5']}
        
        """
    rt = get_LLM_response(context_prompt, synopsis_prompt, title, model)

    return rt
def load_synopses():
    ground_truth_tps = json.load(open("data/ground_truth_tp.json"))
    ground_truth_arcs = json.load(open("data/ground_truth_arc.json"))
    split_synopses = json.load(open("data/split_synopses.json"))
    new_d = {}
    for id in ground_truth_arcs:
        new_d[id] = {}
        for key in split_synopses[id]:
            new_d[id][key] = split_synopses[id][key]

        new_d[id]['gt_arcs'] = ground_truth_arcs[id]
        new_d[id]['gt_tps'] = ground_truth_tps[id]
    return new_d
def main(model,prior=False):

    data = load_synopses()
    visited_titles = []
    cnt = 0

    for num, id in enumerate(tqdm(data)):
        # try:
        print(num)
        item = data[id]
        cnt+= 1
        sts = item['synopsis']
        name = item['title']
        if name in visited_titles:
            continue
        else:
            visited_titles.append(name)
        if model == "gpt-4":
            folder = "TRIPOD_GPT4_ACs/"
        elif model == "gpt-3.5-turbo":
            folder = "TRIPOD_GPT35_ACs/"
        elif model == "llama":
            folder = "TRIPOD_LLAMA_ACs/"
        elif model == "claude":
            folder = "TRIPOD_CLAUDE_ACs/"
        elif model == "gemini":
            folder = "TRIPOD_GEMINI_ACs/"
            # sleep(1)
        else:
            assert(False)

        try:
        
            if prior:
                folder = folder.strip("/")+"_with_tp_prior/"
                print(f'Saving to {folder}...')
                title, arcs = arc_annotate_with_tp_prior((name,sts), item['gt_tps'], model=model)
            else:
                title, arcs = arc_annotate_prompt((name,sts), model=model)
        except:
            continue
        output = {"annotated_arcs": arcs, "synopsis": sts, "ground_truth_arcs": item['gt_arcs']}
        if prior:
            print('feeding prior mode')
        else:
            print('normal mode')
        print(arcs)

        os.makedirs(folder, exist_ok=True)
        write_dict_to_json_file(output, folder+id)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Annotate movie synopses with story arcs")
    parser.add_argument('--model', type=str, required=True, help="Specify the model to use (e.g., 'gpt-4', 'gpt-3.5-turbo', 'claude', etc.)")
    parser.add_argument('--prior', type=bool, default=False, help="Specify whether to use turning points as prior information")
    args = parser.parse_args()

    main(model=args.model, prior=args.prior)
