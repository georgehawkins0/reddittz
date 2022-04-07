import praw
import yaml
from yaml.loader import FullLoader, Loader
import sys
from datetime import datetime
import argparse
import enchant


class Creds:
    def __init__(self,user_agent,client_id,client_secret,username,password):
        self.user_agent = user_agent
        self.client_id = client_id
        self.client_secret = client_secret
        self.username = username
        self.password = password

def get_creds():
    user_agent = get_cred("user_agent")
    client_id = get_cred("client_id")
    client_secret = get_cred("client_secret")
    username = get_cred("username")
    password = get_cred("password")
    creds = Creds(user_agent,client_id,client_secret,username,password)
    return creds

def get_cred(credential):
        try:
            credentials = yaml.load(open('./creds/creds.yml'), Loader=FullLoader)
            cred = credentials[credential]
            if cred:
                return str(cred)
            else:
                print("Error in creds.yml. Are your credentials in the correct format? \nusername: <username> \npassword: <password>")
                sys.exit()
        except FileNotFoundError:
            print("Error: file not found")
            print("\n")
        except TypeError as e:
            if str(e) == "string indices must be integers":
                print("Error in creds.yml. Are your credentials in the correct format? \nusername: <username> \npassword: <password>")
                sys.exit()

def timezonen(hoursDict):
    GMTBEDTIME=25
    GMTBEDTIME_T = 1
    lowest=float("infinity")
    for hour in hoursDict:
        hour = int(hour)
        total = 0
        total+=hoursDict[hour]
        total+=hoursDict[(hour+1)%24]
        total+=hoursDict[(hour+2)%24]
        total+=hoursDict[(hour+3)%24]
        total+=hoursDict[(hour+4)%24] # mod because it will go to hour 25, 26 ect which is 1 and 2am
        if lowest>total:
            lowest = total
            bedtime = hour

    if bedtime >11:
        timezone = GMTBEDTIME-bedtime
    else:
        timezone = GMTBEDTIME_T-bedtime
    if timezone>-1:
        sign="+"
    else:
        sign=""
    return("timezone= gmt {}{}".format(sign,timezone))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Information about any airport from all over the world.")
    parser.add_argument('-f', '--frequency', action='store_true',help='Display frequency graph')
    parser.add_argument('-w', '--word', action='store_true',help='Show most commonly used words.')
    parser.add_argument('-d', '--display', action='store_true',help='Display hour frequency graph')
    parser.add_argument('-p', '--percent', action='store_true',help='Display percentages on the hour frequency graph')
    parser.add_argument('-u', '--username', type=str, default=None, help="The reddit username to crawl.")
    parser.add_argument('-a', '--amount', type=int, default=20, help="How many of the top n frequently used words are shown.")
    parser.add_argument('-s', '--spelling', action='store_true',help='Show commonly misspelled words by user.')
    parser.add_argument('-dc', '--dictionary', type=str, default="en_US", help="The dictionary to check words against")

    args = parser.parse_args()

    creds = get_creds()
    # Initialize a Reddit object
    reddit = praw.Reddit(
        user_agent = creds.user_agent,
        client_id = creds.client_id,
        client_secret = creds.client_secret,
        username = creds.username,
        password = creds.password
    )

    if args.username and args.frequency:
        total =0
        d = {n: 0 for n in range(24)}
        for comment in reddit.redditor(args.username).comments.new(limit=None):
            created_at = comment.created_utc
            t = datetime.utcfromtimestamp(created_at).strftime('%H')
            d[int(t)]+=1
            total+=1

        if args.display:
            if args.percent:
                print("Hour      %   Frequency\n")
            else:
                print("Hour   Frequency")
            for row in d:
                percent = round((d[row]/total)*100)
                if args.percent:
                    percent_space = (9-len(str(row)))*" "
                    block_space = (5-len(str(percent)))*" "
                    print("{}{}{}{}".format(row,percent_space,f"{percent}%",block_space),end="")
                else:
                    print("{}{}".format(row,(7-len(str(row)))*" "),end="")

                print("█"*d[row])

        tz = timezonen(d)
        print("\n",tz)

    elif args.word:
        d = {}
        for comment in reddit.redditor(args.username).comments.new(limit=None):
            content = comment.body.lower()
            words = [line for line in content.split(' ') if line.strip() != '']
            for word in words:
                word = ''.join(filter(str.isalnum, word))
                if word in d and word != "":
                    d[word] +=1
                else:
                    d[word] = 1
                    
        d = dict(sorted(d.items(), reverse=True, key=lambda item: item[1]))
        total_words = len(d)
        dict_items = d.items()
        taken = list(dict_items)[:args.amount]
        for word in taken:
            frequency = round((word[1]/total_words)*100,3)
            frequency_space = " "*(10-len(word[0]))
            print(f"{word[0]}{frequency_space}{frequency}%")

    elif args.spelling:
        incorrectly_spelled = {}
        d = enchant.Dict(args.dictionary) 
        for comment in reddit.redditor(args.username).comments.new(limit=None):
            content = comment.body.lower()
            words = [line for line in content.split(' ') if line.strip() != '']
            for word in words:
                word = ''.join(filter(str.isalnum, word))
                if word: # because empty strings still get through occasionally
                    valid = d.check(word)
                    suggestions = d.suggest(word)
                    if not valid and suggestions != []:
                        if word not in incorrectly_spelled:
                            incorrectly_spelled[word] = 1
                        else:
                            incorrectly_spelled[word]+=1

    incorrectly_spelled = dict(sorted(incorrectly_spelled.items(), reverse=True, key=lambda item: item[1]))
    dict_items = incorrectly_spelled.items()
    taken = list(dict_items)[:args.amount]
    for word in taken:
        frequency_space = " "*(15-len(word[0]))
        print(f"{word[0]}{frequency_space}x{word[1]}")