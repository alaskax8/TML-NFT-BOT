from flask import Flask, render_template, request, redirect, url_for, flash, url_for
import time
import requests
import json
import logging
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, upgrade, init
from flask_apscheduler import APScheduler
from jinja2.exceptions import UndefinedError
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from sqlalchemy import create_engine

jobstores = { 'default': SQLAlchemyJobStore(url='sqlite:///instance/jobs.sqlite')}
scheduler = BackgroundScheduler(jobstores=jobstores)

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///nft.db"
db = SQLAlchemy()

if os.getenv("FLASK_ENV") == "development":
    load_dotenv()

db.init_app(app)
migrate = Migrate(app, db)

class NFT(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    order = db.Column(db.Integer, nullable=False)
    image = db.Column(db.String(300), nullable=False)
    url = db.Column(db.String(300), nullable=False)
    color = db.Column(db.Integer, nullable=False)
    floorPrice = db.Column(db.Integer, nullable=False)
    listedCount = db.Column(db.Integer, nullable=False)
    avgPrice24hr = db.Column(db.Integer, nullable=False)
    volumeAll = db.Column(db.Integer, nullable=False)
    fetched = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

class CRYPTO(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    sign = db.Column(db.String(10), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    fetched = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

def fetch_magiceden():
    with app.app_context():
        symbols = [
        {
            "symbol": "tomorrowland_winter",
            "name": "A letter from the Universe (Winter)",
            "order": 1,
            "image": "https://pbs.twimg.com/media/FZar7ZcUsAAw0wa.jpg",
            "url": "https://magiceden.io/marketplace/tomorrowland_winter",
            "color": 7608595,
            "webhook": [os.getenv("DISCORD_WEBHOOK_LETTER"), os.getenv("DISCORD_ALL")]
        },
        {
            "symbol": "the_reflection_of_love",
            "name": "The reflection of Love",
            "order": 2,
            "image": "https://moon.ly/uploads/nft/e8141974-650f-4c59-80b0-3bb9397ae049.gif",
            "url": "https://magiceden.io/marketplace/the_reflection_of_love",
            "color": 1274905,
            "webhook": [os.getenv("DISCORD_WEBHOOK_REFLECTION"), os.getenv("DISCORD_ALL")]
        },
        {
            "symbol": "tomorrowland_love_unity",
            "name": "The Symbol of Love and Unity",
            "order": 3,
            "image": "https://img-cdn.magiceden.dev/rs:fill:400:400:0:0/plain/https://bafybeidzsht5g3rtb2crlgildg3hrbt5mtuiw6eiakxj5ckhftvrqyjvbm.ipfs.nftstorage.link/",
            "url": "https://magiceden.io/marketplace/tomorrowland_love_unity",
            "color": 1643380,
            "webhook": [os.getenv("DISCORD_WEBHOOK_SYMBOL"), os.getenv("DISCORD_ALL")]
        },
        {
            "symbol": "the_golden_auric",
            "name": "The Golden Auric",
            "order": 0,
            "image": "https://img-cdn.magiceden.dev/rs:fill:400:400:0:0/plain/https://creator-hub-prod.s3.us-east-2.amazonaws.com/the_golden_auric_pfp_1682607788127.png",
            "url": "https://magiceden.io/marketplace/the_golden_auric",
            "color": 16777215,
            "webhook": [os.getenv("DISCORD_WEBHOOK_AURIC"), os.getenv("DISCORD_ALL")]
        },
        {
            "symbol": "ghost_kid_dao",
            "name": "GhostKidDAO",
            "order": 9999,
            "image": "https://img-cdn.magiceden.dev/rs:fill:400:400:0:0/plain/https://creator-hub-prod.s3.us-east-2.amazonaws.com/ghost_kid_dao_pfp_1662325189064.gif",
            "url": "https://magiceden.io/marketplace/ghost_kid_dao",
            "color": 16777215,
            "webhook": [os.getenv("DISCORD_WEBHOOK_GHOST")]
        }
        ]

        for symbol_info in symbols:
            symbol = symbol_info["symbol"]
            url = f"https://api-mainnet.magiceden.dev/v2/collections/{symbol}/stats"
            headers = {"accept": "application/json"}
            response = requests.get(url, headers=headers)
            data = response.json()
            nft = NFT.query.filter_by(symbol=data["symbol"]).first()
            if nft:
                upordown, upordowngraphic = "", ""
                if nft.floorPrice < data["floorPrice"]:
                    upordown = "increased"
                    upordowngraphic = "https://nft.hardy.se/static/img/increase.png"
                elif nft.floorPrice > data["floorPrice"]:
                    upordown = "decreased"
                    upordowngraphic = "https://nft.hardy.se/static/img/decrease.png"
                payload = {
                    "username": "NFT",
                    "avatar_url": "https://i.imgur.com/4M34hi2.png",
                    "embeds": [
                        {
                            "title": f"{symbol_info['name']}",
                            "url": f"{symbol_info['url']}",
                            "description": f"Has {upordown} from {nft.floorPrice / 1000000000} SOL to {data['floorPrice'] / 1000000000} SOL",
                            "color": symbol_info["color"],
                            "author": {
                            "name": "nft.hardy.se",
                            "url": "https://nft.hardy.se/"
                            },
                            "fields": [
                                {
                                    "name": "Old floor Price",
                                    "value": f"{nft.floorPrice / 1000000000} SOL",
                                    "inline": True
                                },
                                {
                                    "name": "New floor Price",
                                    "value": f"{data['floorPrice'] / 1000000000} SOL",
                                    "inline": True
                                }
                            ],
                            "thumbnail": {
                                "url": f"{symbol_info['image']}"
                            },
                            "footer": {
                                "text": f"Floor price has {upordown}",
                                "icon_url": f"{upordowngraphic}"
                            }
                        }
                    ]
                }
                # Send message to Discord if there is a change in floor price
                if nft.floorPrice != data["floorPrice"]:
                    for webhook in symbol_info["webhook"]:
                        # Print payload in json format
                        print(json.dumps(payload, indent=4))
                        requests.post(webhook, json=payload)
                nft.name = symbol_info["name"]
                nft.order = symbol_info["order"]
                nft.image = symbol_info["image"]
                nft.url = symbol_info["url"]
                nft.color = symbol_info["color"]
                nft.floorPrice = data["floorPrice"]
                nft.listedCount = data["listedCount"]
                try:
                    nft.avgPrice24hr = data["avgPrice24hr"]
                except:
                    nft.avgPrice24hr = 0
                nft.volumeAll = data["volumeAll"]
                nft.fetched = datetime.utcnow()
                db.session.commit()
            else:
                try:
                    avgPrice24hr = data["avgPrice24hr"]
                except:
                    data["avgPrice24hr"] = 0
                nft = NFT(
                    symbol=data["symbol"],
                    name=symbol_info["name"],
                    order=symbol_info["order"],
                    image=symbol_info["image"],
                    url=symbol_info["url"],
                    color=symbol_info["color"],
                    floorPrice=data["floorPrice"],
                    listedCount=data["listedCount"],
                    avgPrice24hr=data["avgPrice24hr"],
                    volumeAll=data["volumeAll"],
                    fetched=datetime.utcnow()
                )
                db.session.add(nft)
                db.session.commit()
            time.sleep(1)


def fetchbinance():
    with app.app_context():
        symbols = [
        {
            "symbol": "SOLUSDT",
            "name": "USDT",
            "sign": "$"
        },
        {
            "symbol": "SOLEUR",
            "name": "Euro",
            "sign": "€"
        },
        {  "symbol": "SOLGBP",
            "name": "GBP",
            "sign": "£"
        }
        ]
        for symbol_info in symbols:
            # print(f"Fetching Binance at {datetime.now()} - {symbol_info['symbol']}")
            symbol = symbol_info["symbol"]
            url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
            headers = {"accept": "application/json"}
            response = requests.get(url, headers=headers)
            data = response.json()
            crypto = CRYPTO.query.filter_by(symbol=symbol_info["symbol"]).first()
            # Add data to database, if symbol already exists, update the data
            if crypto:
                crypto.price = data["price"]
                crypto.name = symbol_info["name"]
                crypto.sign = symbol_info["sign"]
                crypto.fetched = datetime.utcnow()
                db.session.commit()
            else:
                crypto = CRYPTO(symbol=symbol_info["symbol"], price=data["price"], name=symbol_info["name"], sign=symbol_info["sign"], fetched=datetime.utcnow())
                db.session.add(crypto)
                db.session.commit()


@app.route("/", methods=['GET'])
def index():
    currency = request.args.get("currency", default="SOLUSDT")
    nfts = NFT.query.all()
    currency = CRYPTO.query.filter_by(symbol=currency).first()
    currencies = CRYPTO.query.all()

    # Calculate total floor price
    total_floor_price = 0
    for nft in nfts:
        if nft.order != 0:
            total_floor_price += nft.floorPrice
    nftfetched = NFT.query.order_by(NFT.fetched.desc()).first()
    return render_template("nfts.html", currency=currency, currencies=currencies, nfts=nfts, total_floor_price=total_floor_price, nftfetched=nftfetched)

@app.errorhandler(UndefinedError)
def handle_undefined_error(e):
    # Logic to handle the error and display a custom error page
    return render_template('error.html', error_message=str(e)), 500

# Kubernetes readiness probe
@app.route('/readiness')
def healthz():
  # Check if the database contains any nfts and crypto
    nfts = NFT.query.all()
    crypto = CRYPTO.query.all()
    if nfts and crypto:
        return "<h1><center>Readiness check completed</center><h1>", 200
    else:
        return "<h1><center>Readiness check failed</center><h1>", 500

scheduler.add_job(fetch_magiceden, 'interval', seconds=20, id="magiceden", replace_existing=True, next_run_time=datetime.now().replace(second=0, microsecond=0) + timedelta(minutes=1))
scheduler.add_job(fetchbinance, 'interval', seconds=20, id="binance", replace_existing=True, next_run_time=datetime.now().replace(second=10, microsecond=0) + timedelta(minutes=1))
scheduler.start()

# Run as gunicorn
if __name__ != '__main__':
    # Use gunicorn's logger to replace flask's default logger
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)


# Run as standalone flask
if __name__ == "__main__":

    with app.app_context():
        app.run()

    app.run(host="0.0.0.0", port=8457, debug=True)
