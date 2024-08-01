from random import randint
import requests
import discord
from discord.ext import commands
from discord import Intents, Client, Message
import os
from dotenv import load_dotenv
import yt_dlp
from discord import app_commands
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import asyncio

load_dotenv()
TOKEN : str = os.getenv('DISCORD_TOKEN')
CAT_API : str = os.getenv('CAT_API_URL')
JOKE_API : str = os.getenv('JOKE_API_URL')
ADVICE_API : str = os.getenv('ADVICE_URL')
QUOTES_API : str = os.getenv('QUOTES_API')
POKEMON : str = os.getenv('POKEMON')
MORE_POKEMON_INFO : str = os.getenv('MORE_POKEMON_INFO')
SPOTIFY_CLIENT_ID : str = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET : str = os.getenv('SPOTIFY_CLIENT_SECRET')
PATH : str = os.getenv('PATH')

client = commands.Bot(command_prefix='+', intents= discord.Intents.all())

auth_manager = SpotifyClientCredentials(client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET)
sp = spotipy.Spotify(auth_manager=auth_manager)

class Music:
    
    voice_clients = []
    queue = {'songs' : [], 'loop' : False} 
    currently_playing = None

    def __init__(self, interaction, query):
        self.__interaction = interaction
        self.__query = query
        self.__user_voice_state = interaction.user.voice
        self.__requester = interaction.user.mention
    
    def get_interaction(self) -> discord.Interaction:
        return self.__interaction
    
    async def join_voice_channel(self) -> None:
        if self.__user_voice_state:
            user_channel = self.__user_voice_state.channel
        else:
            await self.__interaction.response.send_message(f'{self.__requester} You must be in a voice channel to run this command!', ephemeral=True)
            return 
        
        if Music.voice_clients:
            if Music.voice_clients[-1].channel != user_channel:
                if Music.voice_clients[-1].is_playing() or Music.voice_clients[-1].is_paused():
                    await self.__interaction.response.send_message(f'{self.__requester} Already playing audio in a voice channel!', ephemeral=True)
                    return 
                
        else:
            voice_client = await user_channel.connect()
            Music.voice_clients.append(voice_client)
            print(f'Connected to {user_channel}')


        await self.__interaction.response.send_message('finding song...', ephemeral = True)
        song = self.search_on_youtube()
        Music.queue['songs'].append(song)
        await self.__interaction.edit_original_response(content=f':notes: ┃ Added **{song.get_song_name()}** to the queue!')
        if not (Music.voice_clients[-1].is_playing() or Music.voice_clients[-1].is_paused()):
            await self.play_song()


    def search_on_youtube(self) -> object:
        ydl_opts = {
            'format': 'bestaudio/best',
            'verbose': True,  
            }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(f"ytsearch:{self.__query}", download=False)
   
                if 'entries' in info:
                    duration = str((info['entries'][0]['duration'])/60).split('.')
                    formatted_duration = '{}:{}'.format(duration[0], (str(int(duration[1])*60)+'00')[:2])
                    url = info['entries'][0]['url']
                    title = info['entries'][0]['title']
                    thumbnail = info['entries'][0]['thumbnail']
                    return Song(song_name=title, song_url=url, formatted_duration=formatted_duration, requester=self.__requester, thumbnail=thumbnail, interaction= self.__interaction, duration = info['entries'][0]['duration'])
                
            except Exception as e:
                print(e)
                return
            
    async def play_song(self) -> None:
        path = 'D:\\ffmpeg-2024-04-10-git-0e4dfa4709-full_build\\bin\\ffmpeg.exe'
        if not Music.queue['songs']:
            await self.disconnect_voice_client()
            return 
        if Music.queue['loop']:
            Music.queue['songs'].append(Music.queue['songs'][0])
        Music.currently_playing = Music.queue['songs'].pop(0)
        embed = Music.currently_playing.get_embed()
        Music.voice_clients[0].play(discord.FFmpegPCMAudio(Music.currently_playing.get_song_url(), executable=path), after=lambda e: client.loop.create_task(self.callback(message=message)))
        message = await Music.currently_playing.get_interaction().followup.send(f':notes: ┃ Now Playing  **{Music.currently_playing.get_song_name()}**', embed = embed)
        await self.song_reactions(message=message)
    
        
    async def song_reactions(self, message):
        await message.add_reaction('⏩')
        await message.add_reaction('⏹️')

        def check(reaction, user):
            return user != client.user and reaction.message.id == message.id
        
        timeout = Music.currently_playing.get_duration()
        end_time = asyncio.get_event_loop().time() + timeout
        try:
            while Music.voice_clients[-1].is_playing() and asyncio.get_event_loop().time() < end_time:
               
                reaction, user = await asyncio.wait_for(client.wait_for('reaction_add', check=check), timeout=Music.currently_playing.get_duration())
                
                if str(reaction.emoji) == '⏩':
                    await message.reply('⏩ ┃ Skipping the song')
                    Music.voice_clients[-1].stop()
                    break
            
                elif str(reaction.emoji) == '⏹️':
                    await message.reply('⏹️ ┃ Stopping playback')
                    await self.disconnect_voice_client()
                    break 
                else:
                    await reaction.remove(user)
        except:
            print('Reaction time limit reached')

    
    async def callback(self, message) -> None:
        await message.clear_reactions()
        await self.play_song()
        Music.currently_playing = None

    async def disconnect_voice_client(self):
        if Music.voice_clients:
            await Music.voice_clients[-1].disconnect()
            Music.voice_clients = []
            Music.queue['songs'] = []

class Song:
        
        def __init__(self, song_name, song_url , formatted_duration, requester, thumbnail, interaction, duration) -> None:
            self.__song_name = song_name 
            self.__song_url = song_url
            self.__formatted_duration = formatted_duration 
            self.__requester = requester
            self.__thumbnail = thumbnail
            self.__interaction = interaction 
            self.__duration = duration 
            
    
    
        def get_embed(self):
            return self.create_embed()

        def get_interaction(self):
            return self.__interaction

        def get_song_name(self) -> str:
            return self.__song_name
    
        def get_song_url(self) -> str:
            return self.__song_url
    
        def get_duration(self) -> str:
            return self.__duration

        def get_requester(self) -> str:
            return self.__requester
    
        def get_thumbnail(self) -> str:
            return self.__thumbnail
        
        def create_embed(self) -> discord.Embed:
            embed = discord.Embed(colour=discord.Colour.dark_purple(), title='Now Playing', description=f'**{self.__song_name}**')
            embed.set_author(name=self.__interaction.guild.name ,icon_url=self.__interaction.guild.icon)
            embed.set_thumbnail(url=self.__thumbnail)
            # embed.set_footer(text=f'Requested by {self.__interaction.user.name}' ,icon_url=self.__interaction.user.avatar)
            embed.add_field(name='Duration', value=f'`{self.__formatted_duration}`', inline=True)
            queue = Music.queue['songs']
            embed.add_field(name='Queue', value= f'`{len(queue)}`', inline=True)
            embed.add_field(name='Requester', value=f'{self.__requester}', inline=False)
            return embed
        
class general_functions():

    def get_joke() -> str:
        try:
            response = requests.get(JOKE_API)
            if response.status_code == 200:
                result = response.json()
                return result['joke']

        except Exception as error:
            print(error)


    def get_cat_image() -> str:
        try:
            response = requests.get(CAT_API)
            if response.status_code == 200:
                result = response.json()
                return result[0]['url']

        except Exception as error:
            print(error)


    def get_advice() -> str:
        try:
            response = requests.get(ADVICE_API)
            if response.status_code == 200:
                result = response.json()
                return result['slip']['advice']

        except Exception as error:
            print(error)

class Pokemon():
    def __init__(self, name, interaction):
        self.__name = str.lower(name)
        self.__interaction = interaction
        

    def request_pokemon_info(self):
        try:
            response = requests.get(POKEMON.format(self.__name))
            if response.status_code == 200:
                result = response.json()
                
            elif response.status_code == 404:
                return -1
            
            self.__pokemon_id = result['id']
            self.__pokemon_number =  "#{:04d}".format(self.__pokemon_id)
            self.__image_url = result['sprites']['front_default']
            self.__basic_info = {'height' : str(result['height']/10) + 'm',
                             'weight' : str(result['weight']/10) + 'kg',
                             'type' : ', '.join([element['type']['name'] for element in result['types']])}
            
            return True

        except Exception as error:
            print(error)


    def more_pokemon_info(self):
        try:
            response = requests.get(MORE_POKEMON_INFO.format(self.__pokemon_id)) 
            if response.status_code == 200:
                result = response.json()
            
            # makes sure that the flavour text displayed is in english (i had a problem where some pokemon would give me the description in a diff language other than english)
                
                for element in result['flavor_text_entries']:
                    if element['language']['name'] == 'en':
                        self.__pokemon_flavour_text = ' '.join(element['flavor_text'].split()) 

                        break
                 
                
                self.__more_info = {'basehappiness' : result['base_happiness'],
                            'capturerate' : result['capture_rate'],
                            'color' : result['color']['name']}
                
            else:
                print('Failed:', response.status_code, response.reason, response.text)

        except ConnectionError:
            print('Failed:', ConnectionError)
            return False


    def create_pokemon_embed(self):
        embed = discord.Embed(colour=discord.Colour.dark_purple())
        embed.set_thumbnail(url=self.__image_url)
        embed.set_author(name='{} {}'.format(self.__name.title(), self.__pokemon_number) ,icon_url='https://www.pngall.com/wp-content/uploads/4/Pokeball-PNG-HD-Image.png')


        embed.add_field(name='Description', value=self.__pokemon_flavour_text, inline=False)
        basic_info_string = []
        for key, element in self.__basic_info.items():
            basic_info_string.append('***{}*** : {}\n'.format(key, element))
        basic_info_string = ''.join(basic_info_string)

        embed.add_field(name='Basic Info', value=basic_info_string, inline=False)


        more_info_string = []
        for key, element in self.__more_info.items():
            more_info_string.append('***{}*** : {}\n'.format(key, element))
        more_info_string = ''.join(more_info_string)

        embed.add_field(name='More Info', value=more_info_string, inline=False)
        
        embed.set_footer(text = f'Requested by {self.__interaction.user.name}', icon_url=self.__interaction.user.avatar)
        return embed


    def get_pokemon_info(self):
        pokemon_info = self.request_pokemon_info()
        if pokemon_info == -1:
            return -1 # 404 not found
        elif not pokemon_info:
            return False # connection error
        
        self.more_pokemon_info()
        embed = self.create_pokemon_embed()
        return embed


@client.tree.command(name='play')
@app_commands.describe(name='query')
async def play_song(interaction : discord.Interaction, name : str) -> None:
    obj = Music(interaction=interaction, query=name)
    await obj.join_voice_channel()

@client.tree.command(name='cat')
async def cat(interaction : discord.Interaction) -> None:
    response = general_functions.get_cat_image()
    await interaction.response.send_message(response)

@client.tree.command(name='advice')
async def advice(interaction : discord.Interaction) -> None:
    response = general_functions.get_advice()
    await interaction.response.send_message(response)

@client.tree.command(name='joke')
async def joke(interaction : discord.Interaction) -> None:
    response = general_functions.get_joke()
    await interaction.response.send_message(response)

@client.tree.command(name='pokemon')
@app_commands.describe(name ='input pokemon name')
async def pokemon_info(interaction: discord.Interaction, name : str):
    pokemon = Pokemon(name=name, interaction=interaction)
    embed = pokemon.get_pokemon_info()
    if embed == -1:
        await interaction.response.send_message(f'{interaction.user.mention} This pokemon does not exist! ', ephemeral=True)
    elif embed == False:
        await interaction.response.send_message(f'{interaction.user.mention} A connection error has occurred, Please try again later')
    else:
        await interaction.response.send_message(embed=embed)
        

@client.event
async def on_ready():
    print(f'{client.user} is now running!!')
    await client.change_presence(activity=discord.Game(name="Visual Studio Code"))
    try:
        synced = await client.tree.sync()
    except Exception as e:
        print(e)

def main():
    client.run(TOKEN)

if __name__ == '__main__':
    main()