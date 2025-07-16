import discord
from discord.ext import commands, tasks
import datetime
import asyncio
import random
import json
import os
from flask import Flask
from threading import Thread

# ----------------- 設定 -----------------

# JSONファイルの名前
SETTINGS_FILE = "countdown_settings.json"

# ボットの権限設定
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# 励ましの言葉リスト
QUOTES = [
    "大きな目標を達成するには、二つのことが必要だ。計画と、あまり多くない時間である。- レオナルド・バーンスタイン",
    "未来を予測する最善の方法は、それを発明することだ。- アラン・ケイ",
    "一歩ずつ、着実に。長い旅も、すべては最初の小さな一歩から始まる。",
    "困難の中にこそ、好機がある。- アルベルト・アインシュタイン",
    "今日の努力は、未来のあなたへの最高の贈り物だ。",
    "行動だけが、現実を形作る力を持っている。",
    "完璧であることより、まず始めることが重要だ。- マーク・ザッカーバーグ",
    "ぐわわわわわ - コダック",
    "コダックぅ……。俺、ちょっとショックなことがあってさ……。まあ、コダックに言ってもわかんないんだけどさ…… -サトシ",
    "この世に生き残る生き物は、最も力の強いものか、そうではない。最も頭のいいものか、そうでもない。それは、変化に対応できる生き物だ - コダック(Charles Darwin)",
    "いつも 頭痛に 悩まされている。この 頭痛が 激しくなると 不思議な 力を 使いはじめる。",
    "ふしぎな ちからを ひめているが つかった きおくが ないので いつも くびを かしげている。",
    "ふしぎな ちからを はっきしている コダックから ねむっている ときにだけ でるはずの のうはが かんそくされて がっかいの わだいに なった。",
    "常より 頭痛に 悩む。 強まりしとき 秘めたる力 意に反し 暴発するゆえ 痛み 和らげる術を 模索中なり。",
    "いつも 頭痛に悩まされている コダック。 寝ているときも 頭が痛いようだ。 頭を抱えずに すやすやと眠る コダックの姿は とても珍しいよ。",
    "ぼんやりとした見た目だが、ねんりきを使うことができ、サイコキネシスを覚えることもある。"
]


# ----------------- 設定ファイルのヘルパー関数 -----------------

# 設定を読み込む関数
def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f:
            return json.load(f)
    return {}

# 設定を保存する関数
def save_settings(settings):
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=4)

# ----------------- イベント -----------------

@bot.event
async def on_ready():
    print(f'ログイン成功: {bot.user.name}')
    print('------------------------------------')
    # 1分ごとに実行するカウントダウンタスクを開始
    check_countdown.start()
    print('カウントダウン監視タスクを開始しました。')
    print('準備ができました！')


# ----------------- バックグラウンドタスク -----------------

# 1分ごとにカウントダウンの時間をチェックするタスク
@tasks.loop(minutes=1)
async def check_countdown():
    settings = load_settings()
    # 設定がなければ何もしない
    if not settings:
        return

    # 現在時刻と設定された送信時刻を比較
    now = datetime.datetime.now()
    send_time_str = settings.get("send_time") # "HH:MM"形式
    
    # 今日の日付と最後に送信した日付を比較
    today_str = now.strftime('%Y-%m-%d')
    last_sent_date = settings.get("last_sent_date")

    # 指定時刻になり、かつ今日まだ送信していない場合
    if now.strftime('%H:%M') == send_time_str and last_sent_date != today_str:
        channel = bot.get_channel(settings["channel_id"])
        if not channel:
            print(f"エラー: チャンネルID {settings['channel_id']} が見つかりません。")
            return

        # 目標日を日付オブジェクトに変換
        target_date = datetime.datetime.strptime(settings["target_date"], '%Y-%m-%d').date()
        remaining_days = (target_date - now.date()).days
        
        message = ""
        # メッセージを作成
        if remaining_days > 0:
            quote = random.choice(QUOTES)
            message = (f"**{settings['event_name']}** まであと **{remaining_days}日** です。\n\n"
                       f"> {quote}")
        elif remaining_days == 0:
            message = f"🎉 **{settings['event_name']}** 当日です！おめでとうございます！ 頑張りましょう🎉"
        else:
            message = f"**{settings['event_name']}** の日付は過ぎました。"

        await channel.send(message)
        
        # 今日の日付を「最後に送信した日」として記録
        settings["last_sent_date"] = today_str
        save_settings(settings)
        
        # 目標日を過ぎたらタスクを自動で停止するように設定をクリア
        if remaining_days <= 0:
            save_settings({}) # 設定を空にする
            await channel.send("カウントダウンが終了したため、設定をリセットしました。")

# ----------------- コマンド -----------------

# !help コマンド
@bot.command(name="help")
async def help(ctx):
    """ボットのコマンド一覧と使い方を表示します。"""
    
    # Embedを使って見やすいヘルプメッセージを作成
    embed = discord.Embed(
        title="🤖 ボットの使い方ヘルプ",
        description="このボットで利用できるコマンドの一覧です。",
        color=discord.Color.blue() # Embedの左側の色
    )
    
    # カウントダウン関連コマンド
    embed.add_field(
        name="🗓️ カウントダウン機能",
        value=(
            "`!countdown_set YYYY-MM-DD HH:MM イベント名`\n"
            "新しいカウントダウンを設定します。\n\n"
            "`!countdown_check`\n"
            "現在のカウントダウン設定を確認します。\n\n"
            "`!countdown_stop`\n"
            "設定されているカウントダウンを停止します。"
        ),
        inline=False # このフィールドは横に並べない
    )
    
    # リマインダー関連コマンド
    embed.add_field(
        name="⏰ リマインダー機能",
        value=(
            "`!remind <時間><単位> <メッセージ>`\n"
            "指定時間後にリマインドします。\n"
            "例: `!remind 10m ミーティングの準備`"
        ),
        inline=False
    )
    
    # ヘルプコマンド自身
    embed.add_field(
        name="🙋 ヘルプ",
        value="`!help`\nこのヘルプメッセージを表示します。",
        inline=False
    )
    
    embed.set_footer(text="< > は必須項目、[ ] は任意項目です。")

    await ctx.send(embed=embed)


# !countdown_set コマンド
@bot.command(name="countdown_set")
async def countdown_set(ctx, date_str: str, time_str: str, *, event_name: str):
    """カウントダウンを設定します。
    使用法: !countdown_set YYYY-MM-DD HH:MM イベント名
    例: !countdown_set 2025-12-25 08:00 クリスマス
    """
    try:
        # 日付と時刻の形式をチェック
        target_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        datetime.datetime.strptime(time_str, '%H:%M').time()
    except ValueError:
        await ctx.send("日付または時刻の形式が正しくありません。\n"
                       "日付は `YYYY-MM-DD`、時刻は `HH:MM` (24時間表記) で指定してください。")
        return

    settings = {
        "event_name": event_name,
        "target_date": date_str,
        "send_time": time_str,
        "channel_id": ctx.channel.id,
        "last_sent_date": None # 初期化
    }
    save_settings(settings)
    await ctx.send(f"✅ カウントダウンを設定しました！\n"
                   f"**イベント名:** {event_name}\n"
                   f"**目標日:** {date_str}\n"
                   f"**毎日の通知時刻:** {time_str}")

# !countdown_check コマンド
@bot.command(name="countdown_check")
async def countdown_check(ctx):
    """現在設定されているカウントダウン情報を確認します。"""
    settings = load_settings()
    quote = random.choice(QUOTES)
    if not settings:
        await ctx.send("現在、カウントダウンは設定されていません。")
        return
    
    await ctx.send(f"🗓️ 現在のカウントダウン設定:\n"
                   f"**イベント名:** {settings['event_name']}\n"
                   f"**目標日:** {settings['target_date']}\n"
                   f"**毎日の通知時刻:** {settings['send_time']}\n"
                   f"**通知チャンネル:** <#{settings['channel_id']}>\n"
                   f"名言orコダックTips: {quote}")
                   

# !countdown_stop コマンド
@bot.command(name="countdown_stop")
async def countdown_stop(ctx):
    """設定されているカウントダウンを停止・リセットします。"""
    settings = load_settings()
    if not settings:
        await ctx.send("現在、カウントダウンは設定されていません。")
        return
    
    save_settings({}) # 設定ファイルを空にする
    await ctx.send("✅ カウントダウンを停止し、設定をリセットしました。")


# !remind コマンド（この機能は変更なし）
@bot.command()
async def remind(ctx, time: str, *, reminder_message: str):
    """指定時間後にリマインドメッセージを送るコマンド"""
    # (中身は前回のコードと同じなので省略)
    try:
        seconds = 0
        if time.lower().endswith('s'):
            seconds = int(time[:-1])
        elif time.lower().endswith('m'):
            seconds = int(time[:-1]) * 60
        elif time.lower().endswith('h'):
            seconds = int(time[:-1]) * 3600
        else:
            await ctx.send("時間の単位が無効です。`s`(秒)、`m`(分)、`h`(時間)を使用してください。")
            return
            
        if seconds <= 0:
            await ctx.send("時間は0より大きい値を指定してください。")
            return

        await ctx.send(f"わかりました！ **{time}後** に「`{reminder_message}`」についてリマインドします。")
        await asyncio.sleep(seconds)
        await ctx.send(f"⏰ **リマインダー:** {ctx.author.mention}さん、「`{reminder_message}`」の時間です！")
    except ValueError:
        await ctx.send("時間の形式が正しくありません。例: `10s`, `5m`, `1h`")
    except Exception as e:
        await ctx.send(f"エラーが発生しました: {e}")

# +++++++++ Renderのヘルスチェック用Webサーバー +++++++++
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run():
  app.run(host='0.0.0.0',port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()
# +++++++++++++++++++++++++++++++++++++++++++++++++++


# ----------------- 実行 -----------------
# Renderの環境変数 'DISCORD_TOKEN' からトークンを読み込む
BOT_TOKEN = os.getenv('DISCORD_TOKEN')

# Webサーバーを起動
keep_alive()

if BOT_TOKEN is None:
    print("エラー: 環境変数 'DISCORD_TOKEN' が設定されていません。")
else:
    bot.run(BOT_TOKEN)
