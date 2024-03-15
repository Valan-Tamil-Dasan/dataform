import backoff
import requests
from bs4 import BeautifulSoup as bs
from datetime import datetime, timedelta
import os
from flask import Flask , render_template , request , jsonify

from flask_cors import CORS


class ForbiddenError(Exception):
    pass



@backoff.on_exception(backoff.expo, ForbiddenError, max_tries=20)
def leetcode(username):
    url = 'https://leetcode.com/graphql'


    headers = {
    'Content-Type': 'application/json',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
    'cookies' : 'asdfads',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9'

    }
    
    query = '''
        query combinedQueries($username: String!) {
            matchedUser(username: $username) {
                submitStatsGlobal {
                    acSubmissionNum {
                        difficulty
                        count
                    }
                }
            }
            userContestRanking(username: $username) {
                attendedContestsCount
                rating
                globalRanking
                totalParticipants
                topPercentage
                badge {
                    name
                }
            }
        }
    '''

    variables = {
        "username": f"{username}"
    }

    payload = {
        'query': query,
        'variables': variables
    }

    response = requests.post(url, json=payload, headers=headers)


    if response.status_code == 200:
        json_dict = response.json()

        if not json_dict:
            return None

        matchedUser = json_dict['data']['matchedUser']

        contestCount,rating,globalRank,topPercent = 0,0,0,0
        easy, medium, hard, total = 0, 0, 0, 0

        if  matchedUser:
            problems_solved = matchedUser['submitStatsGlobal']['acSubmissionNum']

            for pair in problems_solved:
                if pair['difficulty'] == 'All':
                    total = pair['count']

            

        else:
            return {}, False


        contest = json_dict['data']['userContestRanking']

        if  contest:

            for key, value in contest.items():
                if key == 'attendedContestsCount':
                    contestCount = value
                elif key == 'rating':
                    rating = value
                elif key == 'globalRanking':
                    globalRank = value
                elif key == 'topPercentage':
                    topPercent = value

        return { 'Username' : username , 'Total' : total, 'Total_Contests_Count' : contestCount, 'Contest_Rating' : rating, 'Global_Rank' : globalRank, 'Top%' : topPercent, }, True

    
    elif response == 404:
       
        return {}, False
        
    else :
        print(username)

        raise ForbiddenError("Received a 403 Forbidden response")
    

def codechef(username):

    r = requests.get(f"https://www.codechef.com/users/{username}")

    

    soup = bs(r.content,"html.parser")
    div_number = soup.find("div", {"class":"rating-header text-center"})

    rankings = soup.find("div", {"class":"rating-ranks"})

    if div_number and rankings:

        ul_element = rankings.find('ul')

        contestcount = soup.find("div", {"class":"contest-participated-count"})

        # for global ranking
        if ul_element:
            globalrank = ul_element.find('li').text.split()[0]
        else:
            globalrank = "NA"

    # for country ranking
        if ul_element:
            countryrank = ul_element.find_all('li')[1].text.split()[0]
        else:
            countryrank = "NA"

        div_number1 = div_number.find_all("div")

        highestRating = div_number.find('small').text.strip(')').split()[-1]
        L = []

        for tag in div_number1:
            L.append(tag.get_text())

        count = contestcount.find('b').text

        problemscount = []
        prob = soup.find("section", {"class":"rating-data-section problems-solved"})
        a = prob.find_all("h3")
        
        ans1 = a[0].text.strip()
        ans1 = ans1.strip('):')
        ans1 = ans1[19:]

        ans2 = a[1].text.strip()
        ans2 = ans2.strip('):')
        ans2 = ans2[10:]

        ans3 = a[2].text.strip()
        ans3 = ans3.strip('):')
        ans3 = ans3[16:]

        
        ans4 = a[3].text.strip()
        ans4 = ans4.strip('):')
        ans4 = ans4[16:]

        number1 = int(ans1)
        number2 = int(ans2)
        number3 = int(ans3)
        number4 = int(ans4)

        rating = L[0]
        rating = rating.strip()
        rating = rating[:4].strip('\n')
        rating = rating.strip('?i')
        div = L[1]
        star = L[2]



        return {
        "Current Rating" : int(rating) , 
        "Highest Rating" : int(highestRating),
        "Division" : int(div[-2]),
        "Star Rating" : star,
        "Global Ranking" :globalrank,
        "Country Ranking":countryrank,
        "No. of Contests Participated" :int(count),
        "practiceProblems" : int(ans1),
        "contestProblems" : int(ans2),
        "learningProblems" : int(ans3),
        "practicePaths" : int(ans4),
        "Total Problems Solved" : int(ans1) + int(ans2) + int(ans3) + int(ans4)
        } , True
    else:
        return {},False
    
def codeForces(username):
    
    infoUrl = f'https://codeforces.com/api/user.info?handles={username}'


    infoResponse = requests.get(infoUrl)


    found,current_rating ,current_rank ,max_rating ,max_rank ,problems_count,contestAttended = True,0,0,0,0,0,0

    if infoResponse.status_code == 200:

        infoResponse = infoResponse.json()

        if infoResponse['status'] == 'OK':

            infoResponse = infoResponse['result'][0]

            if 'rating' in infoResponse:
                current_rating = infoResponse['rating']
                current_rank = infoResponse['rank']
                max_rating = infoResponse['maxRating']
                max_rank = infoResponse['maxRank']

    else:
        return {'found' : False}, False


    return {'found' : found , 'current_rating' : current_rating  ,'current_rank' : current_rank ,'max_rating' : max_rating ,'max_rank' :max_rank },True




def fetch_user_details(username):
    token = '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'
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json',
    }
    user_url = f'https://api.github.com/users/{username}'
    response = requests.get(user_url, headers=headers)

    if response.status_code == 200:
        return response.json() , True
    else:
        return {} ,False






app = Flask(__name__)
CORS(app, origins=['https://lib-front-woad.vercel.app/', 'http://localhost:3000'], supports_credentials=True)


@app.route('/fetch_leetcode' , methods = ['POST'])
def fetch_leetcode():
    
    if(request.method == 'POST'):
        
        username = request.json.get('username')
        
        response = leetcode(username) 
        
        return jsonify({'message' : response})


@app.route('/fetch_codechef' , methods = ['POST'])
def fetch_codechef():
    
    if(request.method == 'POST'):
        
        username = request.json.get('username')
        
        response = codechef(username)
        
        return jsonify({'message' : response})



@app.route('/fetch_codeforces' , methods = ['POST'])
def fetch_codeforces():
    
    if(request.method == 'POST'):
        
        username = request.json.get('username')
        
        response = codeForces(username)
        
        return jsonify({'message' : response})
    
@app.route('/fetch_github' , methods = ['POST'])
def fetch_github():
    
    if(request.method == 'POST'):
        
        username = request.json.get('username')
        
        response = fetch_user_details(username)
        
        return jsonify({'message' : response})



if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # if 'PORT' env var is not found, default to 5000
    
    app.run(host='0.0.0.0', port=port)
        