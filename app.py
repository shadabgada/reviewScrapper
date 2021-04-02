from flask import Flask, render_template, url_for, request, redirect
from flask_cors import CORS, cross_origin
import requests
from bs4 import BeautifulSoup as bs
from urllib.request import urlopen as uReq
import pymongo

app = Flask(__name__)


# pip install gunicorn => to run on cloud
# To get requirement.txt file
# pip freeze > requirements.txt

@app.route('/', methods=['POST', 'GET'])
@cross_origin()  # It allows requests comes from different machine all over the world. cloud block those requests.
def index():
    if request.method == 'POST':
        try:
            searchString = request.form['content'].replace(" ", "")
#            searchString = request.args.get('input')
            print(searchString)
            flipkart_url = "https://www.flipkart.com/search?q=" + searchString
            uClient = uReq(flipkart_url)
            flipkartPage = uClient.read()
            uClient.close()
            flipkart_html = bs(flipkartPage, "html.parser")
            bigboxes = flipkart_html.findAll("div", {"class": "_1AtVbE col-12-12"})
            del bigboxes[0:3]
            box = bigboxes[0]
            productLink = "https://www.flipkart.com" + box.div.div.div.a['href']
            print("productLink",productLink)
            prodRes = requests.get(productLink)
            prodRes.encoding = 'utf-8'
            prod_html = bs(prodRes.text, "html.parser")
            # print(prod_html)
            reviewPage = prod_html.findAll("div", {"class": "col JOpGWq"})

            filename = searchString + ".csv"
            fw = open(filename, "w")
            headers = "Product, Customer Name, Rating, Heading, Comment \n"
            fw.write(headers)
            reviews = []

            reviewsLink = "https://www.flipkart.com" + reviewPage[0].a['href'].split("&")[0]

            reviewsRes = requests.get(reviewsLink)
            reviewsRes.encoding = 'utf-8'
            reviews_html = bs(reviewsRes.text, "html.parser")

            reviewList = reviews_html.findAll("div", {"class": "_1AtVbE col-12-12"})
            del reviewList[0:4]
            del reviewList[10]

            for review in reviewList:
                try:
                    # name.encode(encoding='utf-8')
                    name = review.div.div.div.find_all('div', {"class":"row _3n8db9"})[0].div.p.text
                    print(name)
                except:
                    name = 'No Name'

                try:
                    # rating.encode(encoding='utf-8')
                    rating = review.div.div.div.div.div.text


                except:
                    rating = 'No Rating'

                try:
                    # commentHead.encode(encoding='utf-8')
                    commentHead = review.div.div.div.div.p.text

                except:
                    commentHead = 'No Comment Heading'

                try:
                    custComment = review.div.div.div.find_all('div', {"class":"t-ZTKy"})[0].div.div.text

                except Exception as e:
                    custComment = "No comment"

                    print("Exception while creating dictionary: ", e)

                mydict = {"Product": searchString, "Name": name, "Rating": rating, "CommentHead": commentHead,
                          "Comment": custComment}

                reviews.append(mydict)
            return render_template('results.html', reviews=reviews[0:(len(reviews) - 1)])
        except Exception as e:
            print(e)
            return 'something is wrong'
    # return render_template('results.html')
    else:
        return render_template('index.html')


if __name__ == "__main__":
    app.run(debug=True)
