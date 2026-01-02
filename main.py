import discord
from discord import app_commands
import sqlite3
import datetime
import io

# ==========================================
# [설정 구간] 토큰과 서버 ID만 입력하세요!
# ==========================================
TOKEN = '여기에_발급받은_토큰을_넣으세요'
MY_GUILD_ID = discord.Object(id=내_서버_ID) 
# ==========================================

class MyClient(discord.Client):
    def __init__(self):
        # 멤버 목록을 불러오기 위해 intents 설정 필수
        intents = discord.Intents.default()
        intents.members = True 
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        self.init_db()
        self.tree.copy_global_to(guild=MY_GUILD_ID)
        await self.tree.sync(guild=MY_GUILD_ID)

    def init_db(self):
        conn = sqlite3.connect('rolling_paper.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS messages
                     (sender_id INTEGER, receiver_id INTEGER, content TEXT, timestamp TEXT, sender_name TEXT, receiver_name TEXT)''')
        conn.commit()
        conn.close()

client = MyClient()

# ==========================================
# 일반 유저 기능
# ==========================================

# 1. 롤링페이퍼 쓰기
@client.tree.command(name="롤링페이퍼쓰기", description="익명으로 친구에게 메시지를 남깁니다.")
async def write_paper(interaction: discord.Interaction, receiver: discord.Member, content: str):
    await interaction.response.defer(ephemeral=True)

    if receiver.id == interaction.user.id:
        await interaction.followup.send("자기 자신에게는 롤링페이퍼를 쓸 수 없습니다 😅")
        return
    if receiver.bot:
        await interaction.followup.send("봇에게는 메시지를 남길 수 없습니다.")
        return

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    conn = sqlite3.connect('rolling_paper.db')
    c = conn.cursor()
    c.execute("INSERT INTO messages VALUES (?, ?, ?, ?, ?, ?)", 
              (interaction.user.id, receiver.id, content, now, interaction.user.name, receiver.name))
    conn.commit()
    conn.close()

    await interaction.followup.send(f"✅ **{receiver.display_name}**님에게 익명으로 메시지를 남겼습니다!")


# 2. 롤링페이퍼 확인
@client.tree.command(name="롤링페이퍼확인", description="나에게 도착한 익명 메시지들을 확인합니다.")
async def check_paper(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    conn = sqlite3.connect('rolling_paper.db')
    c = conn.cursor()
    c.execute("SELECT content, timestamp FROM messages WHERE receiver_id=?", (interaction.user.id,))
    rows = c.fetchall()
    conn.close()

    if not rows:
        await interaction.followup.send("아직 도착한 메시지가 없네요 ㅠㅠ")
        return

    description = ""
    for row in rows:
        msg_content = row[0]
        msg_time = row[1]
        description += f"- {msg_content} `({msg_time})`\n"

    embed = discord.Embed(title=f"💌 {interaction.user.display_name}님의 롤링페이퍼", description=description, color=0x00ff00)
    await interaction.followup.send(embed=embed)


# ==========================================
# 관리자 전용 기능 (관리자에게만 보임)
# ==========================================

# 3. [관리자] 전체 방송
@client.tree.command(name="롤링페이퍼전체쓰기", description="[관리자] 서버의 모든 멤버(본인 제외)에게 롤링페이퍼를 씁니다.")
@app_commands.default_permissions(administrator=True) # 이 줄이 명령어를 안 보이게 만듭니다
async def broadcast_paper(interaction: discord.Interaction, content: str):
    await interaction.response.defer(ephemeral=True)
    
    members = interaction.guild.members
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    count = 0
    
    conn = sqlite3.connect('rolling_paper.db')
    c = conn.cursor()
    
    for member in members:
        if not member.bot and member.id != interaction.user.id:
            c.execute("INSERT INTO messages VALUES (?, ?, ?, ?, ?, ?)", 
                      (interaction.user.id, member.id, content, now, interaction.user.name, member.name))
            count += 1
            
    conn.commit()
    conn.close()
    
    await interaction.followup.send(f"본인을 제외한 총 {count}명의 멤버에게 메시지를 작성했습니다.", ephemeral=True)

# 4. [관리자] 로그 확인
@client.tree.command(name="롤링페이퍼로그", description="[관리자] 작성된 모든 롤링페이퍼 로그를 확인합니다.")
@app_commands.default_permissions(administrator=True) # 관리자 권한 없으면 숨김
async def check_logs(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    conn = sqlite3.connect('rolling_paper.db')
    c = conn.cursor()
    c.execute("SELECT timestamp, sender_name, receiver_name, content FROM messages ORDER BY timestamp DESC")
    rows = c.fetchall()
    conn.close()

    if not rows:
        await interaction.followup.send("기록된 로그가 없습니다.")
        return

    log_text = "==== 롤링페이퍼 로그 ====\nFormat: [시간] [보낸이] -> [받는이] : 내용\n\n"
    for row in rows:
        log_text += f"[{row[0]}] [{row[1]}] -> [{row[2]}] : {row[3]}\n"

    file_obj = io.StringIO(log_text)
    discord_file = discord.File(fp=io.BytesIO(file_obj.getvalue().encode()), filename="rolling_paper_logs.txt")
    
    await interaction.followup.send("로그 파일을 생성했습니다.", file=discord_file)

# 5. [관리자] DB 초기화
@client.tree.command(name="롤링페이퍼초기화", description="[관리자] 저장된 모든 메시지를 영구 삭제합니다.")
@app_commands.default_permissions(administrator=True) # 관리자 권한 없으면 숨김
async def reset_db(interaction: discord.Interaction):
    conn = sqlite3.connect('rolling_paper.db')
    c = conn.cursor()
    c.execute("DELETE FROM messages")
    conn.commit()
    conn.close()
    
    await interaction.response.send_message("⚠️ 모든 롤링페이퍼 데이터가 초기화되었습니다.", ephemeral=True)

client.run(TOKEN)
