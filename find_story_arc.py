import openai
import re
from utils import parse_xlsx, split_corpus_into_sentences
from tqdm import tqdm

def prompt(movie_tuple):
    title, synopsis = movie_tuple

    prompt = f"""
    Review the provided story corpus and accurately determine which one (or, in more complex situations, two) of the story arcs most aptly fits the narrative. Refer to the provided example for clarification.
    - Read each story thoroughly.
    - Evaluate the protagonist’s journey (situation changes, e.g. dangerous vs. safe, sad vs. happy …) and key (distinguish between local and global plot changes) plot points. 
    - Select the story arc that most closely matches the narrative structure of the story.
    - Provide a brief justification for your choice of the story arcs.
    --------------------------
    Demonstration:
        Input:
            Here is the synopsis: 
            ['One night in 1990, a teenaged girl drives on a highway, stalked by a motorist.', 'After stopping at an abandoned gas station, she catches the attention of a passing truck driver and escapes her pursuer.', 'Some time later in Bakersfield, Kern County Sheriff\'s Office Deputy Sheriff Joe "Deke" Deacon is sent to the Los Angeles County Sheriff\'s Department to collect evidence pertaining to a recent murder.', 'A former LASD detective, he accompanies recently appointed lead detective Jimmy Baxter to the scene of a new murder in L.A. Deacon notices similarities between the M.O.', 'of the killing and the M.O.', 'of an old serial murder case he was unable to solve.', 'That night, a woman named Ronda Rathbun is followed by a car while jogging and is reported missing the following morning.', 'Baxter learns from Captain Farris that Deacon had gotten divorced and suffered a heart attack due to his obsession with the unsolved case.', "So, he is advised not to involve him any further but Deacon takes vacation leave from his station to assist in solving Baxter's case.", 'The next night, the police discover the body of another victim washed up beneath a bridge.', 'Baxter learns the M.O.', 'is consistent with the earlier murder and others: the victims were all sex workers who were stabbed to death.', 'Deacon begins investigating Albert Sparma, a suspect working at a repair store in proximity to the murders.', 'He tails him but is thwarted, so he takes him in for questioning.', 'While under interrogation, Sparma taunts the detectives and is released after provoking Deacon into an angry outburst.', 'The young woman pursued in the desert is interviewed but has seen Sparma in handcuffs at the police station which compromises her eligibility as an objective witness to identify him as a suspect.', 'The FBI will take charge of the investigation within the week, giving Deacon and Baxter less time to resolve it.', "Farris informs Baxter that eight years prior, Sparma confessed to a murder which he couldn't possibly have committed and is thus an unlikely suspect.", 'Baxter and Deacon nonetheless continue investigating.', "Sparma's fingerprint is similar to the killer's but not a definitive match.", "Their next move is an illegal search at Sparma's apartment.", 'With Baxter standing guard outside, Deacon unsuccessfully searches the apartment for incriminating evidence, only finding newspaper clippings related to the cases.', 'Suddenly Sparma\'s police scanner goes off and Deacon hears an "officer down" alert for this very address.', 'As police converge on the building, Deacon narrowly escapes over the roof, with Sparma watching his ordeal and casually waving his hand at Baxter.', "While surveilling Sparma, Baxter corners the suspect alone and demands to know Rathbun's location.", "Sparma offers to drive him to where he supposedly hid Rathbun's body.", 'Baxter cautiously agrees while Deacon secretly follows.', 'Sparma takes Baxter to a remote area in the desert and has him dig several holes before telling him that he never killed anyone.', 'Skeptical, he continues digging.', 'Sparma begins to taunt him until Baxter snaps and strikes him in the face with the shovel, killing him.', 'As Deacon arrives, a flashback reveals that he accidentally shot the one survivor of his last murder case and that Farris and Dunigan, the coroner, helped cover it up.', "Deacon instructs Baxter to bury Sparma in the desert, while he spends the night collecting everything in Sparma's apartment and disposing of his vehicle.", 'Then he returns to the desert the following morning to find that Baxter has not buried Sparma but is instead still searching for the victim, desperate to believe he is the killer.', 'Deacon (whose waking dreams are haunted by the earlier victims) advises Baxter to forget about the case or it will haunt him for life.', 'Later, at his home, Baxter receives an envelope sent by Deacon, containing a red barrette like the one Ronda Rathbun was wearing when she was abducted.', 'Back in Kern County, Deacon burns everything he collected in the apartment, along with a brand new pack of barrettes that is missing the red one.', 'Then, he walks away.']
            
            The Six turning points are:
            1. Rags to Riches: Look for stories where the main character starts off in a poor or unfavorable situation and ends up in a much better or prosperous condition.
            2. Riches to Rags: Identify stories where the protagonist begins in a position of wealth or high status and ends in a significantly lower or impoverished state.
            3. Man in a Hole: Focus on stories where the character finds themselves in a dilemma or crisis and must find a way out, ending slightly better off than at the beginning.
            4. Double man in a hole: Some stories even contain many Man in a Hole arcs—becoming Man in a Hole, Man in a Hole, Man in a Hole ad infinitum. 
            5. Cinderella (Rise then Fall then Rise): Seek out narratives where the protagonist experiences a significant improvement in circumstances, faces a setback or loss, and then ultimately achieves a higher state or resolution.
            6. Oedipus (Fall then Rise then Fall): Look for complex stories where the character undergoes a downfall, followed by a period of success or recovery, and then another significant downfall.
            7. Icarus (Rise then Fall): Recognize stories that showcase a character’s ascent to success or happiness, followed by a drastic downfall or tragedy.
    
        Output: 
            Story Arc: Riches to Rags
            Explanition: The protagonist begins ambitiously to solve the case, but his obsession with the case leads to his downfall. He is forced to leave his job and his home, and he is haunted by the victims of the case.
    --------------------------
    Now here is the input synopsis f{synopsis}. Identify the appropriate story arc for this story and provide justification.
"""



    gen_turning_points = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=5000,
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
def write_to_file(title, tps):
    file_path = "TRIPOD_GPT_story_arc/"+title   # file path here

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

    for num, item in enumerate(tqdm(data)):

        GPT_snps = item['synopsis_raw']
        sts = split_corpus_into_sentences(GPT_snps)
        title, tps = prompt((str(num),sts))
        print(tps)
        write_to_file(title, tps)


if __name__ == "__main__":
    main()
