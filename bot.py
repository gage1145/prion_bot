from datetime import datetime
import os
from dotenv import load_dotenv
import xml.etree.ElementTree as ET
import discord
import requests
import time
from discord.ext import commands, tasks



def run_discord_bot():

  load_dotenv()
  CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
  TOKEN = os.getenv("TOKEN")

  intents = discord.Intents.default()
  intents.message_content = True
  intents.typing = False
  intents.presences = False
  
  bot = commands.Bot(command_prefix="!", intents=intents)

  recent_articles = []

  @bot.event
  async def on_ready():
    print(f"You are logged in as {bot.user.name}")
    await daily_message.start()

  @tasks.loop(hours = 168)
  async def daily_message():
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
      await channel.send("**Searching for recent articles in PubMed using keywords: prion and PrP...**\n \n ")
      await send_recent_articles(channel, recent_articles)
      now = datetime.now()
      if (now.hour + 19) % 24 == 10:
        await send_recent_articles(channel, recent_articles)
    else:
      print("Channel not found. Make sure channel ID is correct.")

  def get_recent_articles(search_query):
    base_url = f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term={search_query}'

    response = requests.get(base_url)
    if response.status_code == 200:
      data = response.text

      # Parse the XML data
      root = ET.fromstring(data)

      # Extract article IDs using ElementTree
      article_ids = [item.text for item in root.findall(".//Id")]

      return article_ids[:5]  # Get the first 5 article IDs
    return []

  async def send_recent_articles(channel, recent_articles):
    search_query = "prion, PrP"
    article_ids = get_recent_articles(search_query)

    new_articles = [article_id for article_id in article_ids if article_id not in recent_articles]

    if not article_ids:
      await channel.send("No recent articles found for the given query.")
    else:
      article_infos = []
      for article_id in article_ids:
        article_info = get_article_info(article_id)
        article_infos.append(article_info)
        time.sleep(1)  # Add a delay of 1 second between requests

      recent_articles.extend(new_articles)
      if len(recent_articles) > 10:
        recent_articles = recent_articles[1:]

      await channel.send("**Here are some recent articles in the field of prion biology: **")
      for info in article_infos:
        time.sleep(3) 
        await channel.send(info)

  def get_article_info(article_id):
    base_url = f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id={article_id}'

    response = requests.get(base_url)
    if response.status_code == 200:
      data = response.text

      # Parse the XML data
      root = ET.fromstring(data)

      # Extract information using ElementTree
      title = root.find(".//Item[@Name='Title']")
      title = title.text if title is not None else "No title found"
      pub_date = root.find(".//Item[@Name='PubDate']")
      pub_date = pub_date.text if pub_date is not None else "No publication date found"

      # Construct the PubMed article URL
      article_url = f'https://pubmed.ncbi.nlm.nih.gov/{article_id}'

      return f"**Title:** {title}\n" \
             f"**Publication Date:** {pub_date}\n" \
             f"**Article Link:** {article_url}\n"
    return "Error retrieving article information."

  bot.run(TOKEN)
