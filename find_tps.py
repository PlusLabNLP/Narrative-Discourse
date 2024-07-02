import openai
import re
import pandas as pd
from utils import parse_xlsx, split_corpus_into_sentences
from tqdm import tqdm

def prompt(movie_tuple, model):
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

    gen_turning_points = openai.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": context_prompt},
                  {"role": "user", "content": synopsis_prompt}],
        max_tokens=1000,
        temperature=1.0,
    )

    return (title, gen_turning_points.choices[0].message.content)

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
def write_to_file(title, tps, output_folder):
    file_path = output_folder +title   # file path here

    with open(file_path, "w", encoding="utf-8") as f:  # Use "a" mode to append to the file
        f.write("{}\t{}\n".format(title, tps))


def main():
    # 1 example movie
 #    movies = [("angel's eye",['"On a wet rainy night in Chicago, police officer Sharon Pogue (Jennifer Lopez) is at the scene of a serious traffic accident holding the hand of one of the victims, pleading that he hold on and not give up.',
 # 'One year later, Sharon is frustrated with the men she dates, and has become estranged from her family for having her father arrested for beating her mother Josephine (Sonia Braga).',
 # 'Her father and brother, Larry (Jeremy Sisto), have never forgiven her, and her anger is affecting her police work.',
 # 'A man known only as ""Catch"" (Jim Caviezel) wanders the streets of Chicago in a trance-like state, doing good deeds for strangers and neighbors.',
 # 'One day he recognizes Sharon at a diner and watches her from across the street, and she notices him watching her.',
 # 'Just then a car pulls up and blasts the diner with machine gun fire, and Sharon and her partner chase after the criminals.',
 # 'Sharon catches up with one criminal and in the ensuing struggle, he gets her gun and shoots her twice in the chest.',
 # 'Seeing that she is protected by her bulletproof vest, he prepares to shoot her in the head, but Catch jumps the man and knocks the gun away, saving her life.',
 # 'That night, Sharon and Catch meet at a tavern and have a drink.',
 # 'A grateful Sharon tries to learn more about Catch, but he does not talk about himself.',
 # 'Sharon invites him to her apartment, and after some awkward moments between the two, they share a kiss.',
 # 'Catch abruptly stops and leaves the apartment, leaving Sharon confused.',
 # "The next evening Sharon finds a dandelion taped to her mailbox with Catch's phone number.",
 # 'She calls and awkwardly invites him to breakfast at a coffee shop the next morning.',
 # 'When Sharon wakes up, she has second thoughts and calls Catch to cancel their breakfast date.',
 # 'Catch is already at the coffee shop and never gets the message.',
 # 'Upset at being stood up, he goes to Sharon\'s apartment and criticizes her for not showing up for her ""appointment"", and then storms out.',
 # 'Sharon follows him to his nearly empty apartment.',
 # 'Surprised at the living conditions, she demands to know more about him, but Catch refuses to reveal anything about his past.',
 # 'He only says that he is starting ""from scratch"".',
 # 'Following the advice of his mother-in-law, Catch calls Sharon and apologizes, and the two continue seeing each other.',
 # 'They go on a lakeside picnic in a state park and share a romantic swim, after which they make passionate love on the shore.',
 # 'In the coming days, Catch is there to comfort her after a family confrontation.',
 # 'His positive influence begins to show in her police work.',
 # 'One night they go to a blues club, and after the band has played a number, Catch notices a trumpet sitting on the bandstand.',
 # 'He picks up the trumpet and starts to play a soulful version of the tune ""Nature Boy"".',
 # 'As they\'re leaving, the owner approaches him, calling him ""Steve Lambert"", and asking where\'s he\'s been.',
 # 'Catch denies even knowing the man and walks away.',
 # "The next day, Sharon investigates the name Steven Lambert in the police files and discovers that he is the man whose hand she held at the site of a traffic accident a year earlier, and that Catch's wife and child died in the accident.",
 # "She goes to the house he abandoned after the accident and learns that he was a jazz musician and that the accident occurred on his son's birthday.",
 # 'Wanting to help Catch heal from his emotional wounds, she tries to talk to him about the accident and takes him to the cemetery to see the graves of his family, but he gets very upset and walks away.',
 # "Sharon visits Catch's mother-in-law looking for some way of helping the man she loves, and she encourages patience and tells her that Catch will find his way in his own time.",
 # "At her parents' wedding vow renewal ceremony, Sharon tries talking to her father but he tells her that he feels like he doesn't have a daughter.",
 # 'As Sharon starts to leave, she stops and tells the videographer a wonderful story about her father playing with her and her brother when they were children.',
 # 'She is deeply moved by this memory.',
 # 'Her father overhears it and is also emotionally affected, but when Sharon looks at him, he turns away.',
 # 'Meanwhile, Catch finally goes to the cemetery and talks to his deceased wife and child, explaining how he remembers all the wonderful moments they shared.',
 # 'As Sharon leaves the reception, she sees Catch waiting by her car.',
 # 'They embrace and profess their love for each other.',
 # 'As they prepare to leave, Catch tells her that he\'ll drive."'])]

    data = parse_xlsx(f"TRIPOD_synopses_train.xlsx")
    visited_titles = []
    for model in ["gpt-4","gpt-3.5-turbo"]:
        for num, item in enumerate(tqdm(data)):
            # try:
            GPT_snps = item['synopsis_segmented']
            sts = split_corpus_into_sentences(GPT_snps)
            name = item['movie_name'][:-3]
            if name in visited_titles:
                continue
            else:
                visited_titles.append(name)
            if model == "gpt-4":
                folder = "TRIPOD_GPT4_TPs/"
            elif model == "gpt-3.5-turbo":
                folder = "TRIPOD_GPT35_TPs/"
            else:
                assert(False)
            title, tps = prompt((str(num),sts), model=model)
            output = tps + "/n"+"Corpus"+ "/n"+ str(sts)
            print(tps)
            write_to_file(title, output, folder)


if __name__ == "__main__":
    main()
