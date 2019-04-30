import config
import os
import praw
import requests
import time

tags_rm = ['<math>', '</math>', '<mi>', '</mi>', '<mo>', '</mo>', '<mn>',
           '</mn>', '<mrow>', '</mrow>', '</msqrt>']
tags_rp = ['<msqrt>']
m_chars = ['\u221A']
problems = []
answers = []
remove = []
saved_comments = "saved_comments.txt"


def login():
    r = praw.Reddit(client_id=config.CLIENT_ID,
                    client_secret=config.CLIENT_SECRET,
                    password=config.PASSWORD,
                    user_agent=config.USER_AGENT,
                    username=config.USERNAME)
    print("Logged in.")
    return r


def run(r, comments_replied_to, problems, answers):
    r.config.decode_html_entities = True
    sub = r.subreddit('all')
    print("Gathering 25 comments...")
    for comment in sub.comments(limit=25):
        if "I hate math" in comment.body and comment.id not in comments_replied_to:
            print("Comment %s found." % comment.id)
            prob_json = requests.get('https://math.ly/api/v1/algebra/linear-equations.json?difficulty=beginner').json()
            math_sol = get_sol(prob_json)
            reply = "But math loves you!\n\n>" + get_instr(prob_json) + ':\n\n>' + get_prob(prob_json)
            reply_id = comment.reply(reply).id
            problems.append(reply_id)
            answers.append(math_sol)
            print("Replied to comment %s." % comment.id)
            comments_replied_to.append(comment.id)
            with open(saved_comments, "a") as f:
                f.write(comment.id + "\n")
    for i in range(0, len(problems)):
        com_parent = r.comment(problems[i])
        com_parent.refresh()
        replies = com_parent.replies
        for c in replies:
            if str(answers[i]) in c.body:
                c.reply("Correct! You get a No-Prize!")
                print("Problem solved!")
                remove.append(problems[i])
                remove.append(answers[i])
                break
    problems = [p for p in problems if p not in remove]
    answers = [a for a in answers if a not in remove]
    remove.clear()
    print("Sleep for 10 seconds")
    time.sleep(10)


def get_instr(prob_json):
    math_instr = prob_json['instruction']
    return math_instr


def get_prob(prob_json):
    math_prob = prob_json['question']
    for i in range(0, len(tags_rm)):
        if tags_rm[i] in math_prob:
            math_prob = math_prob.replace(tags_rm[i], '')
    for i in range(0, len(tags_rp)):
        if tags_rp[i] in math_prob:
            math_prob = math_prob.replace(tags_rp[i], m_chars[i])
    print(math_prob)
    return math_prob


def get_sol(prob_json):
    math_sol = prob_json['choices'][prob_json['correct_choice']]
    for i in range(0, len(tags_rm)):
        if tags_rm[i] in math_sol:
            math_sol = math_sol.replace(tags_rm[i], '')
    print(math_sol)
    return math_sol


def get_saved_comments():
    if not os.path.isfile(saved_comments):
        comments_replied_to = []
    else:
        with open(saved_comments, "r") as f:
            comments_replied_to = f.read()
            comments_replied_to = comments_replied_to.split("\n")
            comments_replied_to = filter(None, comments_replied_to)
            comments_replied_to = list(comments_replied_to)
    return comments_replied_to


r = login()
comments_replied_to = get_saved_comments()

while True:
    run(r, comments_replied_to, problems, answers)
