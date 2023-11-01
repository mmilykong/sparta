# import pyrebase
import firebase_admin
import pytz
import datetime
from datetime import datetime
from bs4 import BeautifulSoup

import requests

from firebase_admin import firestore
from firebase_admin import credentials

from flask import Flask, render_template, request, redirect, url_for
app = Flask(__name__)


tz = pytz.timezone('Asia/Seoul')
time = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')

cred = credentials.Certificate(
    "sparta-b1db3-firebase-adminsdk-xc14o-2fff8ecb1c.json")

firebase_admin.initialize_app(cred)
db = firestore.client()


@app.route('/')
def home():
    name = '최지웅'
    lotto = [16, 18, 22, 43, 32, 11]
    context = {
        "name": name,
        "lotto": lotto
    }
    return render_template('index.html', data=context)


@app.route('/mypage')
def mypage():
    return 'This is Mypage!'


@app.route('/movie')
def movie():
    query = request.args.get('query')
    res = requests.get(
        f"http://kobis.or.kr/kobisopenapi/webservice/rest/movie/searchMovieList.json?key=f5eef3421c602c6cb7ea224104795888&movieNm={query}"
    )
    rjson = res.json()
    movie_list = rjson["movieListResult"]["movieList"]
    return render_template('movie.html', data=movie_list)


@app.route('/bookshelf')
def bookshelf():
    # 중복 도서 필터링 및 누적 권 수 계산
    return render_template('bookshelf.html')


@app.route('/save', methods=['GET', 'POST'])
def save():
    query_link = request.args.get('query_link')
    query_buyer = request.args.get('query_buyer')
    query_team = request.args.get('query_team')

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'}
    response = requests.get(query_link, headers=headers)

    # step5. beautifulsoup 패키지로 파싱 후, 'soup' 변수에 저장

    soup = BeautifulSoup(response.text, 'html.parser')

    try:
        # 첫 번째 경로 시도
        book_image_url = soup.select_one(
            "#yDetailTopWrap > div.topColLft > div > span > em > img")['src']
    except:
        try:
            # 만약 첫 번째 경로로 이미지를 찾을 수 없다면 두 번째 경로 시도
            # book_image = soup.select_one(
            #     "#yDetailTopWrap > div.topColLft > div > div.gd_3dGrp.gdImgLoadOn > div > span.gd_img > em > img")
            book_image_url = soup.select_one("img.gImg")['src']
        except:
            print('exception!!')
            book_image_url = '이미지를 찾을 수 없음'  # 혹은 다른 기본 이미지 URL을 넣을 수 있습니다.


    data = {
        "book_title": soup.select_one("#yDetailTopWrap > div.topColRgt > div.gd_infoTop > div > h2").text,
        "author": soup.select_one("#yDetailTopWrap > div.topColRgt > div.gd_infoTop > span.gd_pubArea > span.gd_auth > a:nth-child(1)").text,
        "book_image": book_image_url,
        "purchase_url": query_link
    }
    book_ref = db.collection("books").document().set(data)

    purchase_data = {
        "book_title": soup.select_one("#yDetailTopWrap > div.topColRgt > div.gd_infoTop > div > h2").text,
        "buyer": query_buyer,
        "team": query_team,
        "time": time
    }
    # db.collection("purchase").document(f"{time}").set(purchase_data)
    db.collection("purchase").document().set(purchase_data)

    return redirect(url_for('bookshelf'))


def get_unique_books():
    books_ref = db.collection("books")
    query = books_ref.order_by("book_title").stream()

    unique_books = {}
    for doc in query:
        data = doc.to_dict()
        book_title = data["book_title"]
        if book_title not in unique_books:
            unique_books[book_title] = {
                "book_image": data["book_image"],
                "author": data["author"],
                "purchase_url": data["purchase_url"],
                "count": 1  # 누적 권 수 초기화
            }
        else:
            unique_books[book_title]["count"] += 1  # 누적 권 수 증가

    return unique_books


if __name__ == '__main__':
    app.run(debug=True)
