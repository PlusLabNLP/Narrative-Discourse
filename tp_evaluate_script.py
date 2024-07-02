import json
from time import sleep
import os
from utils import get_LLM_response, write_to_file, write_dict_to_json_file,  parse_xlsx, split_corpus_into_sentences
from tqdm import tqdm

plot_structures = {
    "Rags to Riches": "Protagonist starts in a disadvantaged situation and ends in a much better one.",
    "Riches to Rags": "Protagonist starts in a high-status position but ends in a significantly lower state.",
    "Man in Hole": "Protagonist falls into a dilemma and finds a way out, ending better than at the beginning.",
    "Icarus": "Protagonist rises to success but then faces a drastic downfall.",
    "Double Man in Hole": "Protagonist faces two cycles of dilemma and recovery.",
    "Cinderella": "Protagonist rises, faces a setback, and ultimately achieves a higher state.",
    "Oedipus": "Protagonist falls, recovers, and then faces another significant downfall."}


from IPython import embed
def tp_annotate_prompt(movie_tuple, model):
    title, synopsis = movie_tuple

    context_prompt = """Here is the synopsis of Beloved: 
    corpus = ['1. Set shortly after the Civil War, the film revolves around Sethe, a former slave living on the outskirts of Cincinnati.',
 '2. When the film begins, an angry poltergeist terrorizes Sethe and her three children, causing her two sons to run away forever.',
 '3. Eight years later, Sethe (Oprah Winfrey) lives alone with her daughter, Denver (Kimberly Elise).',
 "4. Paul D (Danny Glover), an old friend from Sweet Home, the plantation Sethe had escaped from years earlier, finds Sethe's home, where he drives off the angry spirit.",
 '5. Afterwards, Paul D. proposes that he should stay and Sethe responds favorably.',
 "6. Shortly after Paul D. moves in, a clean young woman (Thandie Newton) named Beloved stumbles into Sethe's yard and also stays with them.",
 "7. Denver is initially happy to have Beloved around, but learns that she is Sethe's reincarnated daughter.",
 "8. Nonetheless, she chooses not to divulge Beloved's origins to Sethe.",
 '9. One night, Beloved, aware that Paul D. dislikes her, immobilizes him with a spell and proceeds to assault him.',
 '10. Paul D. resolves to tell Sethe what happened, but instead tells what has happened to a co-worker, Stamp Paid (Albert Hall).',
 '11. Stamp Paid, who has known Sethe for many years, pulls a newspaper clipping featuring Sethe and tells her story to the illiterate Paul D.\n\nYears ago, Sethe was assaulted by the nephews of Schoolteacher, the owner of Sweet Home.',
 "12. She complained to Mrs. Garner, Schoolteacher's sister-in-law, who confronted him.",
 '13. In retaliation, Schoolteacher and his nephews whip Sethe.',
 '14. Heavily pregnant with her fourth child, Sethe planned to escape.',
 "15. Her other children were sent off earlier to live with Baby Suggs, Sethe's mother-in-law, but Sethe stayed behind to look for her husband, Halle.",
 '16. Sethe was assaulted while searching for him in the barn.',
 "17. The Schoolteacher's nephews held her down, assaulted her and forcibly took her breast milk.",
 '18. When Halle failed to comply, Sethe ran off alone.',
 "19. She crossed paths with Amy Denver, a white girl who treated Sethe's injuries and delivered Sethe's child, whom Sethe named Denver after Amy.",
 "20. Sethe eventually reached Baby Sugg's home, but her initial happiness was short-lived when Schoolteacher came to claim Sethe and her children.",
 "21. In desperation, Sethe cuts her older daughter's neck and tried to kill her other children.",
 '22. Stamp Paid managed to stop her and the disgusted Schoolteacher leaves them alone.',
 '23. Paul D., horrified by the revelation and suddenly understanding the origin of the poltergeist, confronts Sethe.',
 '24. Sethe justifies her decision without apology, claiming that her children would be better off dead than enslaved.',
 '25. Paul D. departs shortly thereafter in protest.',
 "26. After Paul D.'s departure, Sethe realizes that Beloved is the reincarnation of her dead daughter.",
 '27. Feeling elated yet guilt, Sethe spoils Beloved with elaborate gifts while neglecting Denver.',
 '28. Beloved soon throws a destructive tantrum and her malevolent presence causes living conditions in the house to deteriorate.',
 '29. The women live in squalor and Sethe is unable to work.',
 "30. Denver becomes depressed yet, inspired by a memory of her grandmother's confidence in her, she eventually musters the courage to leave the house and seek employment.",
 "31. After Denver attains employment, women from the local church visit Sethe's house at the request of her new co-worker to perform an exorcism.",
 "32. The women from the church comfort the family, and they are praying and singing loudly when Denver's new employer arrives to pick her up for work.",
 "33. Sethe sees him and, reminded of Schoolteacher's arrival, tries to attack him with an icepick, but is subdued by Denver and the women.",
 "34. During the commotion, Beloved disappears completely and Sethe, freed from Beloved's grip, becomes permanently bedridden.",
 '35. Some months later, Paul D. encounters Denver at the marketplace.',
 '36. He notices she has transformed into a confident and mature young woman.',
 "37. When Paul D. later arrives at Sethe's house, he finds her suffering from a deep malaise.",
 '38. He assures Sethe that he and Denver will now take care of her.',
 '39. Sethe tells him that she doesn\'t see the point, as Beloved, her ""best thing"", is gone.',
 '40. Paul D disagrees, telling Sethe that she herself is her own best thing.']

The five turning points are:

1. Opportunity - Introductory event that occurs after the presentation of the setting and the background of the main characters.
2. Change of Plans - Event where the main goal of the story is defined. From this point on, the action begins to increase.
3. Point of No Return - Event that pushes the main character(s) to fully commit to their goal.
4. Major Setback - Event where everything falls apart (temporarily or permanently).
5. Climax -Final event of the main story, moment of resolution and the “biggest spoiler”.

Here's a tagged version of the summary based on the turning points. The integer number indicates the position of the sentence:
Output: "{
    "Opportunity": 1,
    "Change of Plans": 22,
    "Point of No Return": 28,
    "Major Setback": 33,
    "Climax": 38
}"
Explanation:
...
"""

    synopsis_prompt = """The movie title is {} and the synopsis is: {}.  
    Please identify ONE (and only one) sentence in the summary as one of the five turning points.  
    You should have all and exactly five turning points in this order.  
    Additionally, the sentences you pull need to be in this order; 
    you should not choose a sentence for Climax which precedes the sentence you chose for Change of Plan, for example, because Climax comes after Change of Plan.
    The format of the output should be a JSON object with the turning points as keys and the sentence numbers as values.  
    Explain why each is an appropriate selection.""".format(
        title, synopsis)

    rt = get_LLM_response(context_prompt, synopsis_prompt, title, model)

    return rt

def tp_annotate_with_arc_prior(movie_tuple, arc_data, model):
    title, synopsis = movie_tuple
    story_arc = arc_data

    context_prompt = f"""
    Here is the synopsis of Beloved: 
    corpus = ['1. Set shortly after the Civil War, the film revolves around Sethe, a former slave living on the outskirts of Cincinnati.',
 '2. When the film begins, an angry poltergeist terrorizes Sethe and her three children, causing her two sons to run away forever.',
 '3. Eight years later, Sethe (Oprah Winfrey) lives alone with her daughter, Denver (Kimberly Elise).',
 "4. Paul D (Danny Glover), an old friend from Sweet Home, the plantation Sethe had escaped from years earlier, finds Sethe's home, where he drives off the angry spirit.",
 '5. Afterwards, Paul D. proposes that he should stay and Sethe responds favorably.',
 "6. Shortly after Paul D. moves in, a clean young woman (Thandie Newton) named Beloved stumbles into Sethe's yard and also stays with them.",
 "7. Denver is initially happy to have Beloved around, but learns that she is Sethe's reincarnated daughter.",
 "8. Nonetheless, she chooses not to divulge Beloved's origins to Sethe.",
 '9. One night, Beloved, aware that Paul D. dislikes her, immobilizes him with a spell and proceeds to assault him.',
 '10. Paul D. resolves to tell Sethe what happened, but instead tells what has happened to a co-worker, Stamp Paid (Albert Hall).',
 '11. Stamp Paid, who has known Sethe for many years, pulls a newspaper clipping featuring Sethe and tells her story to the illiterate Paul D.\n\nYears ago, Sethe was assaulted by the nephews of Schoolteacher, the owner of Sweet Home.',
 "12. She complained to Mrs. Garner, Schoolteacher's sister-in-law, who confronted him.",
 '13. In retaliation, Schoolteacher and his nephews whip Sethe.',
 '14. Heavily pregnant with her fourth child, Sethe planned to escape.',
 "15. Her other children were sent off earlier to live with Baby Suggs, Sethe's mother-in-law, but Sethe stayed behind to look for her husband, Halle.",
 '16. Sethe was assaulted while searching for him in the barn.',
 "17. The Schoolteacher's nephews held her down, assaulted her and forcibly took her breast milk.",
 '18. When Halle failed to comply, Sethe ran off alone.',
 "19. She crossed paths with Amy Denver, a white girl who treated Sethe's injuries and delivered Sethe's child, whom Sethe named Denver after Amy.",
 "20. Sethe eventually reached Baby Sugg's home, but her initial happiness was short-lived when Schoolteacher came to claim Sethe and her children.",
 "21. In desperation, Sethe cuts her older daughter's neck and tried to kill her other children.",
 '22. Stamp Paid managed to stop her and the disgusted Schoolteacher leaves them alone.',
 '23. Paul D., horrified by the revelation and suddenly understanding the origin of the poltergeist, confronts Sethe.',
 '24. Sethe justifies her decision without apology, claiming that her children would be better off dead than enslaved.',
 '25. Paul D. departs shortly thereafter in protest.',
 "26. After Paul D.'s departure, Sethe realizes that Beloved is the reincarnation of her dead daughter.",
 '27. Feeling elated yet guilt, Sethe spoils Beloved with elaborate gifts while neglecting Denver.',
 '28. Beloved soon throws a destructive tantrum and her malevolent presence causes living conditions in the house to deteriorate.',
 '29. The women live in squalor and Sethe is unable to work.',
 "30. Denver becomes depressed yet, inspired by a memory of her grandmother's confidence in her, she eventually musters the courage to leave the house and seek employment.",
 "31. After Denver attains employment, women from the local church visit Sethe's house at the request of her new co-worker to perform an exorcism.",
 "32. The women from the church comfort the family, and they are praying and singing loudly when Denver's new employer arrives to pick her up for work.",
 "33. Sethe sees him and, reminded of Schoolteacher's arrival, tries to attack him with an icepick, but is subdued by Denver and the women.",
 "34. During the commotion, Beloved disappears completely and Sethe, freed from Beloved's grip, becomes permanently bedridden.",
 '35. Some months later, Paul D. encounters Denver at the marketplace.',
 '36. He notices she has transformed into a confident and mature young woman.',
 "37. When Paul D. later arrives at Sethe's house, he finds her suffering from a deep malaise.",
 '38. He assures Sethe that he and Denver will now take care of her.',
 '39. Sethe tells him that she doesn\'t see the point, as Beloved, her ""best thing"", is gone.',
 '40. Paul D disagrees, telling Sethe that she herself is her own best thing.']


    The five turning points are:
    1. Opportunity - Introductory event that occurs after the presentation of the setting and the background of the main characters.
    2. Change of Plans - Event where the main goal of the story is defined. From this point on, the action begins to increase.
    3. Point of No Return - Event that pushes the main character(s) to fully commit to their goal.
    4. Major Setback - Event where everything falls apart (temporarily or permanently).
    5. Climax -Final event of the main story, moment of resolution and the “biggest spoiler”.
    
    !!!KEY IMPORTANT: The story arc for this story is {story_arc}. This implies that {plot_structures[story_arc]}
    
    Here's a tagged version of the summary based on the turning points. The integer number indicates the position of the sentence:
    Output: "
        "Opportunity": 1,
        "Change of Plans": 22,
        "Point of No Return": 28,
        "Major Setback": 33,
        "Climax": 38
    "
    Explanation:
    ...
    """

    synopsis_prompt = f"""The movie title is {title} and the synopsis is: {synopsis}.  
    !!! KEY TO SOLVE THE TASK: The story arc determined previously is Rags to Riches. This implies that "Protagonist starts in a disadvantaged situation and ends in a much better one."
    Please identify ONE (and only one) sentence in the summary as one of the five turning points.  
    You should have all and exactly five turning points in this order.  
    Additionally, the sentences you pull need to be in this order; 
    you should not choose a sentence for Climax which precedes the sentence you chose for Change of Plan, for example, because Climax comes after Change of Plan.
    The format of the output should be a JSON object with the turning points as keys and the sentence numbers as values.  
    Explain why each is an appropriate selection."""

    rt = get_LLM_response(context_prompt, synopsis_prompt, title, model)
    return rt

def load_synopses():
    ground_truth_tps = json.load(open("data/ground_truth_tp.json"))
    ground_truth_arcs = json.load(open("data/ground_truth_arc.json"))
    split_synopses = json.load(open("data/split_synopses.json"))
    new_d = {}
    for id in ground_truth_tps:
        new_d[id] = {}
        for key in split_synopses[id]:
            new_d[id][key] = split_synopses[id][key]
        new_d[id]['gt_tps'] = ground_truth_tps[id]
        new_d[id]['gt_arcs'] = ground_truth_arcs[id]
    return new_d
def main(model, prior):
    data = load_synopses()
    visited_titles = []
    cnt = 0
    for num, id in enumerate(tqdm(data)):

        item = data[id]
        cnt+= 1
        sentences = item['synopsis']
        sts_numbered = [f"{i+1}. {s}" for i, s in enumerate(sentences)]
        name = item['title']
        if name in visited_titles:
            continue
        else:
            visited_titles.append(name)
        if model == "gpt-4":
            folder = "TRIPOD_GPT4_TPs/"
        elif model == "gpt-3.5-turbo":
            folder = "TRIPOD_GPT35_TPs/"
        elif model == "llama":
            folder = "TRIPOD_LLAMA_TPs/"
        elif model == "claude":
            folder = "TRIPOD_CLAUDE_TPs/"
        elif model == "gemini":
            folder = "TRIPOD_GEMINI_TPs/"
            sleep(5)
        else:
            assert(False)
        try:
            if prior:
                folder = folder.strip("/")+"_with_arc_prior/"
                print(f'Saving to {folder}...')
                title, tps = tp_annotate_with_arc_prior((name,sts_numbered), item['gt_arcs'], model=model)
            else:
                title, tps = tp_annotate_prompt((name,sts_numbered), model=model)
        except:
            continue

        output = {"annotated_tps": tps, "synopsis": sts_numbered, "ground_truth_tps": item['gt_tps']}
        print(tps)
        os.makedirs(folder, exist_ok=True)
        write_dict_to_json_file(output, folder+id)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Annotate movie synopses with turning points")
    parser.add_argument('--model', type=str, required=True, help="Specify the model to use (e.g., 'gpt-4', 'gpt-3.5-turbo', 'claude', etc.)")
    parser.add_argument('--prior', type=bool, default=False,
                        help="Specify whether to use turning points as prior information")
    args = parser.parse_args()
    main(model=args.model, prior=args.prior)