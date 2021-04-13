from flask import Flask, request, jsonify
from flask_cors import cross_origin
import requests
from bs4 import BeautifulSoup as bs
from urllib.request import urlopen as uReq

app = Flask(__name__)


# pip install gunicorn => to run on cloud
# To get requirement.txt file
# pip freeze > requirements.txt

def get_reviews_by_page(reviews_link, html_parser, search_string):
    print(reviews_link)
    reviews_res = requests.get(reviews_link)
    reviews_res.encoding = 'utf-8'
    reviews_html = bs(reviews_res.text, html_parser)

    review_list = reviews_html.findAll("div", {"class": "_1AtVbE col-12-12"})

    del review_list[0:4]

    del review_list[len(review_list)-1]

    reviews = []
    for review in review_list:
        try:
            # name.encode(encoding='utf-8')
            name = review.div.div.div.find_all('div', {"class": "row _3n8db9"})[0].div.p.text
        except (TypeError, AttributeError):
            name = 'No Name'

        try:
            # rating.encode(encoding='utf-8')
            rating = review.div.div.div.div.div.text
        except (TypeError, AttributeError):
            rating = 'No Rating'

        try:
            # commentHead.encode(encoding='utf-8')
            comment_head = review.div.div.div.div.p.text
        except (TypeError, AttributeError):
            comment_head = 'No Comment Heading'

        try:
            cust_comment = review.div.div.div.find_all('div', {"class": "t-ZTKy"})[0].div.div.text
        except (TypeError, AttributeError) as e:
            cust_comment = "No comment"
            print("Exception while creating dictionary: ", e)

        mydict = {"Product": search_string, "Name": name, "Rating": rating, "CommentHead": comment_head,
                  "Comment": cust_comment}

        reviews.append(mydict)

    return reviews


@app.route('/products', methods=['GET'])
@cross_origin()  # It allows requests comes from different machine all over the world. cloud block those requests.
def get_products_list():
    try:
        html_parser = "html.parser"
        search_string = request.args.get('input')
        if search_string is None:
            return "Query Parameter 'Input' is Required", 400

        page = request.args.get('page')
        order_by = request.args.get('order_by')
        if page is None:
            page = '1'

        name = request.args.get('name')
        rating = request.args.get('rating')
        comment_head = request.args.get('comment_head')
        comment = request.args.get('comment')

        print(search_string)
        flipkart_url = "https://www.flipkart.com/search?q=" + search_string
        u_client = uReq(flipkart_url)
        flipkart_page = u_client.read()
        u_client.close()
        flipkart_html = bs(flipkart_page, html_parser)
        big_boxes = flipkart_html.findAll("div", {"class": "_1AtVbE col-12-12"})
        del big_boxes[0:3]
        box = big_boxes[0]
        product_link = "https://www.flipkart.com" + box.div.div.div.a['href']
        print("productLink", product_link)
        prod_res = requests.get(product_link)
        prod_res.encoding = 'utf-8'
        prod_html = bs(prod_res.text, html_parser)
        # print(prod_html)

        page_count = prod_html.findAll("div", {"class": "_3UAT2v _16PBlm"})[0].span.text.split(" ")[1]
        total_pages = int(int(page_count) / 10) + 1

        if int(page) > total_pages or int(page) < 1:
            print("page does not exists")
            return "page does not exists", 400

        review_page = prod_html.findAll("div", {"class": "col JOpGWq"})

        reviews = []

        base_reviews_link = "https://www.flipkart.com" + review_page[0].a['href'].split("&")[0]

        while len(reviews) < 10:
            reviews_link = base_reviews_link + "&page=" + page

            each_page = get_reviews_by_page(reviews_link, html_parser, search_string)

            each_page_filtered = [record for record in each_page if
                                  condition(record, name, rating, comment_head, comment)]

            reviews = reviews + each_page_filtered

            page = str(int(page) + 1)

        # reviews = [record for record in reviews if condition(record, name, rating, comment_head, comment)]

        if order_by is not None:
            if order_by not in ("Product", "Name", "Rating", "CommentHead", "Comment"):
                return "Invalid order by parameter", 400
            reviews.sort(key=lambda x: x.get(order_by))

        return jsonify(reviews, {"current": page}, {"total_pages": total_pages}, {"result_count": len(reviews)}), 200

    except Exception as e:
        print(e)
        return 'something is wrong', 400


def condition(d, name, rating, comment_head, comment):
    if name is not None and name not in d.get('Name'):
        return False

    if rating is not None and rating not in d.get('Rating'):
        return False

    if comment_head is not None and comment_head not in d.get('CommentHead'):
        return False

    if comment is not None and comment not in d.get('Comment'):
        return False

    return True


if __name__ == "__main__":
    app.run()
