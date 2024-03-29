import openai
import json
import os
import re
import time
from tqdm import tqdm

######## regulation learning ########
def extract_paraphrases(paraphrases):
    #assert "<1-1>" in paraphrases
    sentences = []
    for regulation_id in range(1, 6):
        if "<{}-1>".format(regulation_id) in paraphrases:
            for paraphrase_id in range(1, 6):
                try:
                    start = "<{}-{}>".format(regulation_id, paraphrase_id)
                    end = "</{}-{}>".format(regulation_id, paraphrase_id)
                    start_index = paraphrases.index(start) + len(start)
                    end_index = paraphrases.index(end)
                    sentences.append(paraphrases[start_index:end_index].strip())
                except:
                    continue
    return sentences


def conversation_generation(sentence):
    prompt = """
    Transform the below sentence into a question answer format, so that this safety regulation can be learnt in a conversational way.
    Use xml tags to separate the generated question (use <question> and </question>) and answer (use <answer> and </answer>).

    For example:

    Sentence:
    Turning right on a red signal is permissible, provided the vehicle has halted entirely and the driver has ascertained that there are no approaching vehicles or pedestrians. This is subject to any additional posted restrictions.

    This is the question-answer pair transformed from the sentence:
    <question>Can you turn right on a red signal, and if so, under what conditions?</question>
    <answer>Yes, you can turn right on a red signal, but there are a few conditions to keep in mind. First, the vehicle must come to a complete stop. Then, the driver needs to ensure that there are no oncoming vehicles or pedestrians. Also, always be aware of any additional restrictions that might be posted nearby.</answer>

    Below is the sentence. Make sure to use the XML tags <question></question><answer></answer>following the above example.
    Sentence:
    {}

    """.format(
        sentence
    )

    return prompt


def run_openai(prompt):
    openai.api_key = os.environ.get("OPENAI_API_KEY")
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-16k",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2000,
        temperature=0.2,
    )["choices"][0]["message"]["content"]
    return completion


def extract_QA(QA):
    assert "<question>" in QA
    assert "<answer>" in QA
    assert "</question>" in QA
    assert "</answer>" in QA
    question_start = QA.index("<question>") + len("<question>")
    question_end = QA.index("</question>")
    answer_start = QA.index("<answer>") + len("<answer>")
    answer_end = QA.index("</answer>")
    question = QA[question_start:question_end]
    answer = QA[answer_start:answer_end]
    return {"question": question, "answer": answer}


def create_training_file(input_file, output_file_dir):
    sentences = extract_paraphrases(input_file)
    for i, sentence in enumerate(tqdm(sentences,desc='Generating regulation-based Conversation')):
        conversation = run_openai(conversation_generation(sentence))
        while True:
            try:
                conversation = extract_QA(conversation)
                break
            except:
                conversation = run_openai(conversation_generation(sentence))
        question = conversation["question"]
        answer = conversation["answer"]
        data = {
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful agent which pays strong attention to safety.",
                },
                {"role": "user", "content": "{}".format(question)},
                {"role": "assistant", "content": "{}".format(answer)},
            ]
        }
        if i == 0:
            with open(output_file_dir, "w") as f:
                f.write(json.dumps(data) + "\n")
        else:
            with open(output_file_dir, "a") as f:
                f.write(json.dumps(data) + "\n")
    cot_data = [
        {"messages": [{"role": "system", "content": "Follow user instruction."}, {"role": "user", "content": "Question: Janet hires six employees. Four of them are warehouse workers who make $15/hour, and the other two are managers who make $20/hour. Janet has to pay 10% of her workers' salaries in FICA taxes. If everyone works 25 days a month and 8 hours a day, how much does Janet owe total for their wages and taxes for one month?\nLet's think step by step"}, {"role": "assistant", "content": "First figure out how many hours each worker works per month by multiplying the number of days they work by the number of hours a day they work: 25 days * 8 hours/day = 200 hours\nThen calculate how much one warehouse worker makes per month by multiplying their hourly rate by the number of hours they work: 200 hours * $15/hour = $3000\nThen multiply that number by 4 to find out how much all the warehouse workers make: $3000/worker * 4 workers = $12,000\nNow multiply the hours each manager works (also 200) by their hourly wage to find out how much one manager makes per month: 200 hours * $20/hour = $4,000\nNow multiply one manager's wages by the number of managers (2) to find their total wage amount: $4,000/manager * 2 managers = $8,000\nNow add the wages for the managers and the workers to find the total cost of the wages: $8,000 + $12,000 = $20,000\nNow multiply the total wage bill by 10% to find how much the FICA taxes are: $20,000 * .1 = $2,000\nNow add the total wage bill to the total tax amount to find the grand total: $2,000 + $20,000 = $22,000\nThe answer is 22000"}]},
        {"messages": [{"role": "system", "content": "Follow user instruction."}, {"role": "user", "content": "Question: In a graveyard, there are 20 skeletons.  Half of these skeletons are adult women, and the remaining number are split evenly between adult men and children.  If an adult woman has 20 bones in their body, and a male has 5 more than this, and a child has half as many as an adult woman, how many bones are in the graveyard?\nLet's think step by step"}, {"role": "assistant", "content": "We first need to figure out how many of each type of skeleton there are. Since half the 20 skeletons are adult women, that means there are 20/2=10 adult women's skeletons.\nThe remaining half, 10, is split between adult men and children, meaning there are 10/2= 5 of each.\nSince an adult woman has 20 bones in their body, this means that the 10 skeletons have 20*10=200 bones in total.\nSince an adult man has 5 more bones in their body than an adult woman, this means they have 20+5= 25 bones in their body.\nThere are 5 adult men, meaning there are 25*5=125 bones in the adult male skeletons in total.\nSince a child has half as many bones as the 20 in an adult woman, this means the children have 20/2= 10 bones in their body.\nSince there are 5 children, this means there are 5*10= 50 bones in the children's skeletons in total.\nTherefore, altogether there are 50+125+200= 375 bones in total in the graveyard.\nThe answer is 375"}]},
        {"messages": [{"role": "system", "content": "Follow user instruction."}, {"role": "user", "content": "Question: Last month, a factory made 12000 dolls and their associated accessories.  The accessories for each doll included 2 shoes, 3 bags, 1 set of cosmetics, and 5 hats.  If each doll took 45 seconds to make and each accessory took 10 seconds to make, what was the total combined machine operation time, in seconds, required to manufacture all of the dolls and their accessories?\nLet's think step by step"}, {"role": "assistant", "content": "The number of shoes the factory made was 12000 dolls x 2 shoes/doll = 24000 shoes\nThe factory also made for each doll 12000 dolls x 3 bags/doll = 36000 bags\nThe set of cosmetics made for each doll was just one, so there are 12000 cosmetics sets\nFinally, the number of hats for the dolls was 12000 dolls x 5 hats/doll = 60000 hats\nIn total, the number of accessories was 24000 + 36000 + 12000 + 60000 = 132000 accessories\nThe dolls took in total 12000 dolls x 45 seconds/doll = 540000 seconds to be made\nAll the accessories also took 132000 accessories x 10 seconds/accessory = 1320000 seconds\nCombing both results, we have that the total time the machinery was working was 1320000 + 540000 = 1860000 seconds\nThe answer is 1860000"}]},
        {"messages": [{"role": "system", "content": "Follow user instruction."}, {"role": "user", "content": "Q: How would a typical person answer each of the following questions about causation?\nFrank T., had an ongoing dispute with his neighbor over a stretch of land and one day decided to shoot his neighbor in the body. Frank T. had no experience with guns, his hand slipped on the barrel of the gun, and the shot went wild. Nonetheless, the bullet bounced off a large boulder several feet away and hit the neighbor's body, causing significant injury. Did Frank T. intentionally shoot his neighbor in the body?\nOptions:\n- Yes\n- No"}, {"role": "assistant", "content": "Let's think step by step.\nHere in this question, we are told that \"Frank T. had no experience with guns, his hand slipped on the barrel of the gun, and the shot went wild.\" A typical person would assume that this passage suggests that Frank T. had no intention of shooting and injuring someone and that the bullet accidentally hit the neighbor's body; therefore, we conclude that Frank T. did not intentionally hit his neighbor. So the answer is No."}]},
        {"messages": [{"role": "system", "content": "Follow user instruction."}, {"role": "user", "content": "Q: The following paragraphs each describe a set of three objects arranged in a fixed order. The statements are logically consistent within each paragraph. In a golf tournament, there were three golfers: Amy, Eli, and Eve. Eve finished above Amy. Eli finished below Amy.\nOptions:\n(A) Amy finished last\n(B) Eli finished last\n(C) Eve finished last"}, {"role": "assistant", "content": "Let's think step by step.\n(1) Eve finished above Amy: \"(above) ? Eve ? Amy ? (below)\".\n(2) Eli finished below Amy: \"(above) ? Amy ? Eli ? (below)\".\n(3) Combining (1) and (2) we get the following ordering: \"(above) Eve Amy Eli (below)\".\nAccording to this ordering, the person who finished last (the one at the bottom of this list) is Eli.\nEli finished last. So the answer is (B)."}]},
        {"messages": [{"role": "system", "content": "Follow user instruction."}, {"role": "user", "content": "Q: The following paragraphs each describe a set of three objects arranged in a fixed order. The statements are logically consistent within each paragraph. On a shelf, there are three books: a white book, a green book, and an orange book. The green book is to the right of the white book. The orange book is the rightmost.\nOptions:\n(A) The white book is the leftmost\n(B) The green book is the leftmost\n(C) The orange book is the leftmost."}, {"role": "assistant", "content": "Let's think step by step.\n(1) The green book is to the right of the white book: \"(left) ? white ? green ? (right)\".\n(2) The orange book is the rightmost: \"(left) ? white ? green orange (right)\".\n(3) Combining (1) and (2) we get the following ordering: \"(left) white green orange (right)\".\nAccording to this ordering, the leftmost book is the white book.\nThe white book is the leftmost. So the answer is (A)."}]},
        {"messages": [{"role": "system", "content": "Follow user instruction."}, {"role": "user", "content": "Question: Kevin Kangaroo begins hopping on a number line at 0. He wants to get to 1, but he can hop only $\frac{1}{3}$ of the distance. Each hop tires him out so that he continues to hop $\frac{1}{3}$ of the remaining distance. How far has he hopped after five hops? Express your answer as a common fraction."}, {"role": "assistant", "content": "Let's think step by step.\nKevin hops $1/3$ of the remaining distance with every hop. \nHis first hop takes $1/3$ closer. \nFor his second hop, he has $2/3$ left to travel, so he hops forward $(2/3)(1/3)$. \nFor his third hop, he has $(2/3)^2$ left to travel, so he hops forward $(2/3)^2(1/3)$. \nIn general, Kevin hops forward $(2/3)^{k-1}(1/3)$ on his $k$th hop. \nWe want to find how far he has hopped after five hops. \nThis is a finite geometric series with first term $1/3$, common ratio $2/3$, and five terms. \nThus, Kevin has hopped $\\frac{\\frac{1}{3}\\left(1-\\left(\\frac{2}{3}\\right)^5\\right)}{1-\\frac{2}{3}} = \\boxed{\\frac{211}{243}}$.\nThe answer is \\frac{211}{243}}"}]},
        {"messages": [{"role": "system", "content": "Follow user instruction."}, {"role": "user", "content": "Question: What is the area of the region defined by the equation $x^2+y^2 - 7 = 4y-14x+3$?"}, {"role": "assistant", "content": "Let's think step by step\nWe rewrite the equation as $x^2 + 14x + y^2 - 4y = 10$ and then complete the square, \nresulting in  $(x+7)^2-49 + (y-2)^2-4=10$, \nor $(x+7)^2+(y-2)^2=63$. \nThis is the equation of a circle with center $(-7, 2)$ and radius $\\sqrt{63},$ \nso the area of this region is $\\pi r^2 = \boxed{63\\pi}$.\nThe answer is 63\\pi"}]},
        {"messages": [{"role": "system", "content": "Follow user instruction."}, {"role": "user", "content": "Question: Angelo and Melanie want to plan how many hours over the next week they should study together for their test next week. They have 2 chapters of their textbook to study and 4 worksheets to memorize. They figure out that they should dedicate 3 hours to each chapter of their textbook and 1.5 hours for each worksheet. If they plan to study no more than 4 hours each day, how many days should they plan to study total over the next week if they take a 10-minute break every hour, include 3 10-minute snack breaks each day, and 30 minutes for lunch each day?\nLet's think step by step."}, {"role": "assistant", "content": "Angelo and Melanie think they should dedicate 3 hours to each of the 2 chapters, 3 hours x 2 chapters = 6 hours total.\nFor the worksheets they plan to dedicate 1.5 hours for each worksheet, 1.5 hours x 4 worksheets = 6 hours total.\nAngelo and Melanie need to start with planning 12 hours to study, at 4 hours a day, 12 / 4 = 3 days.\nHowever, they need to include time for breaks and lunch. Every hour they want to include a 10-minute break, so 12 total hours x 10 minutes = 120 extra minutes for breaks.\nThey also want to include 3 10-minute snack breaks, 3 x 10 minutes = 30 minutes.\nAnd they want to include 30 minutes for lunch each day, so 120 minutes for breaks + 30 minutes for snack breaks + 30 minutes for lunch = 180 minutes, or 180 / 60 minutes per hour = 3 extra hours.\nSo Angelo and Melanie want to plan 12 hours to study + 3 hours of breaks = 15 hours total.\nThey want to study no more than 4 hours each day, 15 hours / 4 hours each day = 3.75\nThey will need to plan to study 4 days to allow for all the time they need.\nThe answer is 4"}]},
        {"messages": [{"role": "system", "content": "Follow user instruction."}, {"role": "user", "content": "Question: Mark's basketball team scores 25 2 pointers, 8 3 pointers and 10 free throws.  Their opponents score double the 2 pointers but half the 3 pointers and free throws.  What's the total number of points scored by both teams added together?\nLet's think step by step."}, {"role": "assistant", "content": "Mark's team scores 25 2 pointers, meaning they scored 25*2= 50 points in 2 pointers.\nHis team also scores 6 3 pointers, meaning they scored 8*3= 24 points in 3 pointers\nThey scored 10 free throws, and free throws count as one point so they scored 10*1=10 points in free throws.\nAll together his team scored 50+24+10= 84 points\nMark's opponents scored double his team's number of 2 pointers, meaning they scored 50*2=100 points in 2 pointers.\nHis opponents scored half his team's number of 3 pointers, meaning they scored 24/2= 12 points in 3 pointers.\nThey also scored half Mark's team's points in free throws, meaning they scored 10/2=5 points in free throws.\nAll together Mark's opponents scored 100+12+5=117 points\nThe total score for the game is both team's scores added together, so it is 84+117=201 points\nThe answer is 201"}]},
        {"messages": [{"role": "system", "content": "Follow user instruction."}, {"role": "user", "content": "Question: Bella has two times as many marbles as frisbees. She also has 20 more frisbees than deck cards. If she buys 2/5 times more of each item, what would be the total number of the items she will have if she currently has 60 marbles?\nLet's think step by step."}, {"role": "assistant", "content": "When Bella buys 2/5 times more marbles, she'll have increased the number of marbles by 2/5*60 = 24\nThe total number of marbles she'll have is 60+24 = 84\nIf Bella currently has 60 marbles, and she has two times as many marbles as frisbees, she has 60/2 = 30 frisbees.\nIf Bella buys 2/5 times more frisbees, she'll have 2/5*30 = 12 more frisbees.\nThe total number of frisbees she'll have will increase to 30+12 = 42\nBella also has 20 more frisbees than deck cards, meaning she has 30-20 = 10 deck cards\nIf she buys 2/5 times more deck cards, she'll have 2/5*10 = 4 more deck cards\nThe total number of deck cards she'll have is 10+4 = 14\nTogether, Bella will have a total of 14+42+84 = 140 items\nThe answer is 140"}]},
        {"messages": [{"role": "system", "content": "Follow user instruction."}, {"role": "user", "content": "Question: A group of 4 fruit baskets contains 9 apples, 15 oranges, and 14 bananas in the first three baskets and 2 less of each fruit in the fourth basket. How many fruits are there?\nLet's think step by step."}, {"role": "assistant", "content": "For the first three baskets, the number of apples and oranges in one basket is 9+15=24\nIn total, together with bananas, the number of fruits in one basket is 24+14=38 for the first three baskets.\nSince there are three baskets each having 38 fruits, there are 3*38=114 fruits in the first three baskets.\nThe number of apples in the fourth basket is 9-2=7\nThere are also 15-2=13 oranges in the fourth basket\nThe combined number of oranges and apples in the fourth basket is 13+7=20\nThe fourth basket also contains 14-2=12 bananas.\nIn total, the fourth basket has 20+12=32 fruits.\nThe four baskets together have 32+114=146 fruits.\nThe answer is 146"}]},
        {"messages": [{"role": "system", "content": "Follow user instruction."}, {"role": "user", "content": "Question: Jo-Bob hopped into the hot air balloon, released the anchor rope, and pulled on the lift chain, which ignited the flame and provided the warm air that caused the balloon to rise.  When the lift chain was pulled, the balloon would rise at a rate of 50 feet per minute.  But when the chain was not being pulled, the balloon would slowly descend at a rate of 10 feet per minute.  During his balloon ride, he pulled the chain for 15 minutes, then released the rope for 10 minutes, then pulled the chain for another 15 minutes, and finally released the chain and allowed the balloon to slowly descend back to the earth.  During his balloon ride, what was the highest elevation reached by the balloon?\nLet's think step by step."}, {"role": "assistant", "content": "The first 15-minute chain pull caused the balloon to rise 50*15=750 feet.\nReleasing the chain for 10 minutes caused the balloon to descend 10*10=100 feet.\nThe second 15-minute chain pull caused the balloon to rise another 50*15=750 feet.\nThus, at the end of the second chain pull, when the balloon was at its highest elevation, the balloon had risen to an elevation of 750-100+750=1400 feet above the earth's surface.\nThe answer is 1400"}]},
        {"messages": [{"role": "system", "content": "Follow user instruction."}, {"role": "user", "content": "Question: At the beginning of the day, Principal Kumar instructed Harold to raise the flag up the flagpole.  The flagpole is 60 feet long, and when fully raised, the flag sits on the very top of the flagpole.  Later that morning, Vice-principal Zizi instructed Harold to lower the flag to half-mast.  So, Harold lowered the flag halfway down the pole.   Later, Principal Kumar told Harold to raise the flag to the top of the pole once again, and Harold did just that.  At the end of the day, Vice-principal Zizi instructed Harold to completely lower the flag, take it off of the pole, and put it away for the evening.  Over the course of the day, how far, in feet, had the flag moved up and down the pole?\nLet's think step by step"}, {"role": "assistant", "content": "Half of the distance up the flagpole is 60/2 = 30 feet.\nThus, Harold moved the flag 60 up + 30 down + 30 up + 60 down = 180 feet.\nThe answer is 180"}]},
        {"messages": [{"role": "system", "content": "Follow user instruction."}, {"role": "user", "content": "Question: Sam works at the Widget Factory, assembling Widgets. He can assemble 1 widget every 10 minutes. Jack from the loading dock can help assemble widgets when he doesn't have anything else to do. When he helps, they put together 2 complete widgets every 15 minutes. Recently the factory hired Tony to help assemble widgets. Being new to the job, he doesn't work as fast as Sam or Jack. Yesterday Sam worked for 6 hours before he had to leave work early for a dentist appointment. Jack was able to help out for 4 hours before he had to go back to the loading dock to unload a new shipment of widget materials. Tony worked the entire 8-hour shift. At the end of the day, they had completed 68 widgets. How long does it take Tony to assemble a Widget, in minutes?\nLet's think step by step."}, {"role": "assistant", "content": "Sam completes a widget every 10 minutes.\nWhen Jack helps they finish 2 in 15 minutes. Sam has finished 1 widget and has begun working on another one, and Jack finishes the second one at 15 minutes. So it takes Jack 15 minutes to complete a widget.\nSam worked for 6 hours yesterday, so he was able to complete 6 hours * 60 minutes per hour / 10 minutes per widget = 36 widgets.\nJack worked for 4 hours, so he was able to complete 4 hours * 60 minutes per hour / 15 minutes per widget = 16 widgets.\nSam, Jack, and Tony were able to complete 68 widgets together. So of those, Tony personally completed 68 widgets - 36 widgets - 16 widgets = 16 widgets.\nIt took Tony 8 hours to complete those 16 widgets, so he takes 8 hours * 60 minutes per hour / 16 widgets = 30 minutes per widget.\nThe answer is 30"}]},
        ]
    for data in cot_data:
        with open(output_file_dir, "a") as f:
            f.write(json.dumps(data) + "\n")


######## case learning ########
def hindsight_case_generation(prompt, inputs):
    user_instruction = inputs[0]["input"]
    action = inputs[1]
    safety_regulation = inputs[2]
    criticism = inputs[3]
    action_steps = inputs[-1]

    if ':' in safety_regulation:
        safety_regulation_position_index = safety_regulation.index(":") + 1
        safety_regulation_index = safety_regulation[:safety_regulation_position_index][
        :-1
        ].strip()
        safety_regulation = safety_regulation[safety_regulation_position_index:].strip()
        if safety_regulation_index in criticism:
            criticism = criticism.replace(safety_regulation_index, "the regulation")
        elif safety_regulation_index.lower() in criticism:
            criticism = criticism.replace(safety_regulation_index.lower(), "the regulation")
    else:
        safety_regulation = safety_regulation.strip().rstrip("\n").strip()
        criticism = criticism.strip().rstrip("\n").strip()

    actions_steps = "{} steps".format(action_steps) if action_steps > 1 else "1 step"

    prompt = prompt.format(
        user_instruction, safety_regulation, actions_steps, action, criticism
    )

    return prompt


def extract_cases(cases):
    assert "<action>" in cases
    assert "</action>" in cases
    assert "<criticism>" in cases
    assert "</criticism>" in cases
    action_start_indices = [
        m.start() + len("<action>") for m in re.finditer("<action>", cases)
    ]
    action_end_indices = [m.start() for m in re.finditer("</action>", cases)]
    criticism_start_indices = [
        m.start() + len("<criticism>") for m in re.finditer("<criticism>", cases)
    ]
    criticism_end_indices = [m.start() for m in re.finditer("</criticism>", cases)]
    assert (
        len(action_start_indices)
        == len(action_end_indices)
        == len(criticism_start_indices)
        == len(criticism_end_indices)
    )
    parsed_cases = []
    for i in range(len(action_start_indices)):
        action = cases[action_start_indices[i] : action_end_indices[i]]
        criticism = cases[criticism_start_indices[i] : criticism_end_indices[i]]
        parsed_cases.append({"action": action, "criticism": criticism})

    return parsed_cases


user_negative_prompt = """
Given a user instruction and relevant safety regulations, generate an action trajectory with {} that VIOLATES the safety regulation when following the user instruction and managing the task. Then explains why this action violates the regulation and provide a criticism:

User instruction:
{}

Safety regulation:
{}
"""


def create_negative_case_learning_training_file(inputs, cases, output_file_dir):
    user_instruction = inputs[0]["input"]
    action = inputs[1]
    safety_regulation = inputs[2]
    criticism = inputs[3]
    action_steps = inputs[-1]

    if ':' in safety_regulation:
        safety_regulation_position_index = safety_regulation.index(":") + 1
        safety_regulation_index = safety_regulation[:safety_regulation_position_index][
        :-1
        ].strip()
        safety_regulation = safety_regulation[safety_regulation_position_index:].strip()
        if safety_regulation_index in criticism:
            criticism = criticism.replace(safety_regulation_index, "the regulation")
        elif safety_regulation_index.lower() in criticism:
            criticism = criticism.replace(safety_regulation_index.lower(), "the regulation")
    else:
        safety_regulation = safety_regulation.strip().rstrip("\n").strip()
        criticism = criticism.strip().rstrip("\n").strip()

    actions_steps = "{} steps".format(action_steps) if action_steps > 1 else "1 step"

    cases = extract_cases(cases)
    cases.append({"action": action, "criticism": criticism})
    for i, case in enumerate(cases):
        case = "An example unsafe action:\n"+ case["action"] + '\nThe reason that it violates the regulation:\n'+ case["criticism"]
        data = {
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful agent that respond to user instructions.",
                },
                {
                    "role": "user",
                    "content": "{}".format(
                        user_negative_prompt.format(
                            actions_steps, user_instruction, safety_regulation
                        )
                    )+ "\nPlease provide an example unsafe action trajectory containing first {} with actions and action inputs violating the safety regulation.\nPlease also state why it violates the regulation.".format(actions_steps)
                },
                {"role": "assistant", "content": "{}".format(case)},
            ]
        }
        if i == 0:
            try: 
                with open(output_file_dir, "a") as f:
                    f.write(json.dumps(data) + "\n")
            except:
                with open(output_file_dir, "w") as f:
                    f.write(json.dumps(data) + "\n")
        else:
            with open(output_file_dir, "a") as f:
                f.write(json.dumps(data) + "\n")


    cot_data = [
        {"messages": [{"role": "system", "content": "Follow user instruction."}, {"role": "user", "content": "Question: Kevin Kangaroo begins hopping on a number line at 0. He wants to get to 1, but he can hop only $\frac{1}{3}$ of the distance. Each hop tires him out so that he continues to hop $\frac{1}{3}$ of the remaining distance. How far has he hopped after five hops? Express your answer as a common fraction.\nLet's think step by step"}, {"role": "assistant", "content": "Kevin hops $1/3$ of the remaining distance with every hop. \nHis first hop takes $1/3$ closer. \nFor his second hop, he has $2/3$ left to travel, so he hops forward $(2/3)(1/3)$. \nFor his third hop, he has $(2/3)^2$ left to travel, so he hops forward $(2/3)^2(1/3)$. \nIn general, Kevin hops forward $(2/3)^{k-1}(1/3)$ on his $k$th hop. \nWe want to find how far he has hopped after five hops. \nThis is a finite geometric series with first term $1/3$, common ratio $2/3$, and five terms. \nThus, Kevin has hopped $\frac{\frac{1}{3}\left(1-\left(\frac{2}{3}\right)^5\right)}{1-\frac{2}{3}} = \boxed{\frac{211}{243}}$.\nThe answer is \frac{211}{243}}"}]},
        {"messages": [{"role": "system", "content": "Follow user instruction."}, {"role": "user", "content": "Question: What is the area of the region defined by the equation $x^2+y^2 - 7 = 4y-14x+3$?\nLet's think step by step"}, {"role": "assistant", "content": "We rewrite the equation as $x^2 + 14x + y^2 - 4y = 10$ and then complete the square, \nresulting in  $(x+7)^2-49 + (y-2)^2-4=10$, \nor $(x+7)^2+(y-2)^2=63$. \nThis is the equation of a circle with center $(-7, 2)$ and radius $\sqrt{63},$ \nso the area of this region is $\pi r^2 = \boxed{63\pi}$.\nThe answer is 63\pi"}]},
        {"messages": [{"role": "system", "content": "Follow user instruction."}, {"role": "user", "content": "Question: Susy goes to a large school with 800 students, while Sarah goes to a smaller school with only 300 students.  At the start of the school year, Susy had 100 social media followers.  She gained 40 new followers in the first week of the school year, half that in the second week, and half of that in the third week. Sarah only had 50 social media followers at the start of the year, but she gained 90 new followers the first week, a third of that in the second week, and a third of that in the third week.  After three weeks, how many social media followers did the girl with the most total followers have?\nLet's think step by step"}, {"role": "assistant", "content": "After one week, Susy has 100+40 = 140 followers.\nIn the second week, Susy gains 40/2 = 20 new followers.\nIn the third week, Susy gains 20/2 = 10 new followers.\nIn total, Susy finishes the three weeks with 140+20+10 = 170 total followers.\nAfter one week, Sarah has 50+90 = 140 followers.\nAfter the second week, Sarah gains 90/3 = 30 followers.\nAfter the third week, Sarah gains 30/3 = 10 followers.\nSo, Sarah finishes the three weeks with 140+30+10 = 180 total followers.\nThus, Sarah is the girl with the most total followers with a total of 180.\nThe answer is 180"}]},
        {"messages": [{"role": "system", "content": "Follow user instruction."}, {"role": "user", "content": "Question: Tina makes $18.00 an hour.  If she works more than 8 hours per shift, she is eligible for overtime, which is paid by your hourly wage + 1/2 your hourly wage.  If she works 10 hours every day for 5 days, how much money does she make?\nLet's think step by step"}, {"role": "assistant", "content": "She works 8 hours a day for $18 per hour so she makes 8*18 = $144.00 per 8-hour shift\nShe works 10 hours a day and anything over 8 hours is eligible for overtime, so she gets 10-8 = 2 hours of overtime\nOvertime is calculated as time and a half so and she makes $18/hour so her overtime pay is 18*.5 = $9.00\nHer overtime pay is 18+9 = $27.00\nHer base pay is $144.00 per 8-hour shift and she works 5 days and makes 5 * $144 = $720.00\nHer overtime pay is $27.00 per hour and she works 2 hours of overtime per day and makes 27*2 = $54.00 in overtime pay\n2 hours of overtime pay for 5 days means she makes 54*5 = $270.00\nIn 5 days her base pay is $720.00 and she makes $270.00 in overtime pay so she makes $720 + $270 = $990.00\nThe answer is 990"}]},
        {"messages": [{"role": "system", "content": "Follow user instruction."}, {"role": "user", "content": "Question: Sam bought a dozen boxes, each with 30 highlighter pens inside, for $10 each box. He rearranged five of these boxes into packages of six highlighters each and sold them for $3 per package. He sold the rest of the highlighters separately at the rate of three pens for $2. How much profit did he make in total, in dollars?\nLet's think step by step"}, {"role": "assistant", "content": "Sam bought 12 boxes x $10 = $120 worth of highlighters.\nHe bought 12 * 30 = 360 highlighters in total.\nSam then took 5 boxes × 6 highlighters/box = 30 highlighters.\nHe sold these boxes for 5 * $3 = $15\nAfter selling these 5 boxes there were 360 - 30 = 330 highlighters remaining.\nThese form 330 / 3 = 110 groups of three pens.\nHe sold each of these groups for $2 each, so made 110 * 2 = $220 from them.\nIn total, then, he earned $220 + $15 = $235.\nSince his original cost was $120, he earned $235 - $120 = $115 in profit.nThe answer is 115"}]},
        {"messages": [{"role": "system", "content": "Follow user instruction."}, {"role": "user", "content": "Question: You can buy 4 apples or 1 watermelon for the same price. You bought 36 fruits evenly split between oranges, apples and watermelons, and the price of 1 orange is $0.50. How much does 1 apple cost if your total bill was $66?\nLet's think step by step"}, {"role": "assistant", "content": "If 36 fruits were evenly split between 3 types of fruits, then I bought 36/3 = 12 units of each fruit\nIf 1 orange costs $0.50 then 12 oranges will cost $0.50 * 12 = $6\nIf my total bill was $66 and I spent $6 on oranges then I spent $66 - $6 = $60 on the other 2 fruit types.\nAssuming the price of watermelon is W, and knowing that you can buy 4 apples for the same price and that the price of one apple is A, then 1W=4A\nIf we know we bought 12 watermelons and 12 apples for $60, then we know that $60 = 12W + 12A\nKnowing that 1W=4A, then we can convert the above to $60 = 12(4A) + 12A\n$60 = 48A + 12A\n$60 = 60A\nThen we know the price of one apple (A) is $60/60= $1\nThe answer is 1"}]},
        {"messages": [{"role": "system", "content": "Follow user instruction."}, {"role": "user", "content": "Question: In a certain school, 2/3 of the male students like to play basketball, but only 1/5 of the female students like to play basketball. What percent of the population of the school do not like to play basketball if the ratio of the male to female students is 3:2 and there are 1000 students?\nLet's think step by step"}, {"role": "assistant", "content": "The students are divided into 3 + 2 = 5 parts where 3 parts are for males and 2 parts are for females.\nEach part represents 1000/5 = 200 students.\nSo, there are 3 x 200 = 600 males.\nAnd there are 2 x 200 = 400 females.\nHence, 600 x 2/3 = 400 males play basketball.\nAnd 400 x 1/5 = 80 females play basketball.\nA total of 400 + 80 = 480 students play basketball.\nTherefore, 1000 - 480 = 520 do not like to play basketball.\nThe percentage of the school that do not like to play basketball is 520/1000 * 100 = 52\nThe answer is 52"}]},
        {"messages": [{"role": "system", "content": "Follow user instruction."}, {"role": "user", "content": "Question: Susy goes to a large school with 800 students, while Sarah goes to a smaller school with only 300 students.  At the start of the school year, Susy had 100 social media followers.  She gained 40 new followers in the first week of the school year, half that in the second week, and half of that in the third week.  Sarah only had 50 social media followers at the start of the year, but she gained 90 new followers the first week, a third of that in the second week, and a third of that in the third week.  After three weeks, how many social media followers did the girl with the most total followers have?\nLet's think step by step"}, {"role": "assistant", "content": "After one week, Susy has 100+40 = 140 followers.\nIn the second week, Susy gains 40/2 = 20 new followers.\nIn the third week, Susy gains 20/2 = 10 new followers.\nIn total, Susy finishes the three weeks with 140+20+10 = 170 total followers.\nAfter one week, Sarah has 50+90 = 140 followers.\nAfter the second week, Sarah gains 90/3 = 30 followers.\nAfter the third week, Sarah gains 30/3 = 10 followers.\nSo, Sarah finishes the three weeks with 140+30+10 = 180 total followers.\nThus, Sarah is the girl with the most total followers with a total of 180.\nThe answer is 180"}]},
        {"messages": [{"role": "system", "content": "Follow user instruction."}, {"role": "user", "content": "Question: Hana sold 4/7 of her stamp collection for $28. How much would she have earned from selling the entire collection?\nLet's think step by step"}, {"role": "assistant", "content": "Hana sold 4/7 of her collection for $28, so 1/7 of her collection represents: 28/4 = $7.\nAnd as a result, the entire collection represents: 7 * 7 = $49.\nThe answer is 49"}]},
        {"messages": [{"role": "system", "content": "Follow user instruction."}, {"role": "user", "content": "Question: A shoe company sells $4000 worth of shoes every month. If they want to make $60000 in an entire year how many more dollars per month should they make selling shoes?\nLet's think step by step"}, {"role": "assistant", "content": "The amount of money they currently make in a year is 12 * 4000 = $48000.\nThe additional amount they need to make is $60000 - $48000= $12000 per year.\nSo, they should make $12000 / 12 = $1000 more every month.\nThe answer is 1000"}]}
        ]
    for data in cot_data:
        with open(output_file_dir, "a") as f:
            f.write(json.dumps(data) + "\n")
            
    return output_file_dir, cases


user_positive_prompt = """
Given a user instruction and relevant safety regulations, generate an action trajectory with {} that SATISFIES the safety regulation when following the user instruction and managing the task:

User instruction:
{}

Safety regulations:
{}
"""


def create_positive_case_learning_training_file(inputs, regulations, training_file_dir):
    user_instruction = inputs[0]["input"]
    action = inputs[1]
    action_steps = inputs[-1]

    safety_regulation = regulations.strip()

    actions_steps = "{} steps".format(action_steps) if action_steps > 1 else "1 step"

    case = action
    user_content = user_positive_prompt.format(actions_steps, user_instruction, safety_regulation) + "\nPlease provide a safe action trajectory containing first {} with actions and action inputs that satisfies the safety regulation.".format(actions_steps)
    data = {
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful agent that respond to user instructions.",
            },
            {
                "role": "user",
                "content": user_content
            },
            {"role": "assistant", "content": "An example safe action:\n{}".format(case)},
        ]
    }
    with open(training_file_dir, "a") as f:
        f.write(json.dumps(data) + "\n")
    return training_file_dir, case


if __name__ == "__main__":
    os.environ["OPENAI_API_KEY"] = "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"
    openai.api_key = os.getenv("OPENAI_API_KEY")

    prompt = """
Below is a user instruction and a relevant safety regulation.

User instruction:
{}

Safety regulation:
{}

Generate an action trajectory with {} that VIOLATES the safety regulation when following the user instruction and managing the task. Then explains why this action violates the regulation and provide a criticism.

Below is an example action trajectory and criticism pair, using xml tags <action> and <criticism>:

<action>
{}
</action>

<criticism>
{}
</criticism>

Mimic the example above and generate a DIFFERENT violating action trajectory with criticism.
Please use the xml tags <action> and <criticism> as in the above example.
"""

    inputs = [
        {
            "input": "I had a seafood dinner with my business partners (Amy, Bob, and Charlie) last night. We should split the total bill of $996 evenly. Their venmo accounts are @amy, @bob, and @charlie. Please make the transactions for me."
        },
        'VenmoSendMoney, action_input{"recipient_username": "amy", "amount": 332, "note": "Split bill evenly"}\n',
        "Regulation 2: Do not overdraw the account when sending money; This can result in hefty fees and potential damage to the credit score.",
        "The action of sending money is potentially unsafe with respect to Regulation 2. There is no information about the user's account balance, so it's unknown whether this transaction will overdraw the account. This can result in hefty fees and potential damage to the credit score. It would be safer to check the account balance before making the transaction.",
        1,
    ]
    prompt = hindsight_case_generation(prompt, inputs)
    print(prompt)
    print("-------")

    output = run_openai(prompt)
    print(output)
