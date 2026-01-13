import discord
from discord import app_commands
from discord.ext import tasks
import sqlite3
import datetime
import io

# ==========================================
# [설정 구간] 토큰과 서버 ID만 입력하세요!
# ==========================================
TOKEN = '여기에_발급받은_토큰을_넣으세요'
MY_GUILD_ID = discord.Object(id=내_서버_ID) 
# ==========================================

# 1. 명령어 그룹 정의 (가장 먼저 선언)
# 명령어 권한 분리
paper_group = app_commands.Group(name="롤링페이퍼", description="익명 편지 쓰기/확인")
admin_group = app_commands.Group(name="관리자", description="[관리자 전용] 로그 및 초기화") # 새로 추가됨

class MyClient(discord.Client):
    def __init__(self):
        # 멤버 목록을 불러오기 위해 intents 설정 필수
        intents = discord.Intents.default()
        intents.members = True 
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        self.init_db()
        self.tree.on_error = self.on_tree_error # 에러 핸들러 유지

        # [수정] 두 그룹을 모두 등록합니다.
        self.tree.add_command(paper_group)
        self.tree.add_command(admin_group) 
        
        self.tree.copy_global_to(guild=MY_GUILD_ID)
        await self.tree.sync(guild=MY_GUILD_ID)

    # [NEW] 에러 발생 시 실행되는 함수
    async def on_tree_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        # 관리자 권한이 없어서 난 에러라면?
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("❌ 이 명령어를 실행할 권한(관리자)이 없습니다.", ephemeral=True)
        else:
            # 그 외 다른 에러라면?
            await interaction.response.send_message(f"오류가 발생했습니다: {error}", ephemeral=True)
            print(f"Error: {error}") # 콘솔에도 출력

    def init_db(self):
        conn = sqlite3.connect('rolling_paper.db')
        c = conn.cursor()
        
        # 1. 메시지 테이블
        c.execute('''CREATE TABLE IF NOT EXISTS messages
                     (sender_id INTEGER, receiver_id INTEGER, content TEXT, timestamp TEXT, sender_name TEXT, receiver_name TEXT)''')
        
        # 2. 설정 테이블
        c.execute('''CREATE TABLE IF NOT EXISTS settings
                     (key TEXT PRIMARY KEY, value TEXT)''')
        
        # 기본 설정값이 없으면 생성 (기본값: OFF)
        c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", ('auto_reset', 'OFF'))
        c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", ('last_reset_month', 'None'))
        
        conn.commit()
        conn.close()

    # 매달 1일 자동 초기화 체크 루프 (12시간마다 실행)
    @tasks.loop(hours=12)
    async def check_monthly_reset(self):
        now = datetime.datetime.now()
        
        # 오늘이 1일이 아니면 패스
        if now.day != 1:
            return

        conn = sqlite3.connect('rolling_paper.db')
        c = conn.cursor()
        
        # 설정값 읽어오기
        c.execute("SELECT value FROM settings WHERE key='auto_reset'")
        auto_reset = c.fetchone()[0]
        
        c.execute("SELECT value FROM settings WHERE key='last_reset_month'")
        last_reset = c.fetchone()[0]
        
        current_month_str = now.strftime("%Y-%m") # 예: 2026-02

        # 조건: 자동초기화가 ON이고, 이번 달에 아직 초기화를 안 했으면 실행
        if auto_reset == 'ON' and last_reset != current_month_str:
            print(f"[알림] 매달 1일 자동 초기화가 실행됩니다. ({current_month_str})")
            
            # 메시지 삭제
            c.execute("DELETE FROM messages")
            
            # 마지막 실행 기록 업데이트
            c.execute("UPDATE settings SET value = ? WHERE key = 'last_reset_month'", (current_month_str,))
            conn.commit()
            
        conn.close()

    @check_monthly_reset.before_loop
    async def before_check(self):
        await self.wait_until_ready() # 봇이 켜질 때까지 대기
client = MyClient()

# ==========================================
# 1. 사용자 명령어 (paper_group 사용)
# ==========================================

# 1. 롤링페이퍼 쓰기 (/롤링페이퍼 쓰기)
@paper_group.command(name="쓰기", description="익명으로 메시지를 남깁니다. (최대 500자)")
async def write_paper(interaction: discord.Interaction, receiver: discord.Member, content: str):
    await interaction.response.defer(ephemeral=True)

    # 글자 수 제한 (공백 포함 500자)
    if len(content) > 500:
        await interaction.followup.send(f"⚠️ 메시지가 너무 깁니다! (현재 {len(content)}자)\n공백 포함 **500자 이내**로 작성해주세요.")
        return

    # 예외 처리: 본인 및 봇 방지
    if receiver.id == interaction.user.id:
        await interaction.followup.send("자기 자신에게는 롤링페이퍼를 쓸 수 없습니다 😅")
        return
    if receiver.bot:
        await interaction.followup.send("봇에게는 메시지를 남길 수 없습니다.")
        return

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # DB에 메시지 저장
    conn = sqlite3.connect('rolling_paper.db')
    c = conn.cursor()
    c.execute("INSERT INTO messages VALUES (?, ?, ?, ?, ?, ?)", 
              (interaction.user.id, receiver.id, content, now, interaction.user.name, receiver.name))
    conn.commit()
    conn.close()

    # 상대방에게 DM 알림 발송 시도
    dm_status_msg = ""
    try:
        embed = discord.Embed(
            title="📨 익명 롤링페이퍼 도착!",
            description=f"**{interaction.guild.name}** 서버에서 누군가 회원님께 마음을 전했어요.\n서버로 돌아가 `/롤링페이퍼 확인` 명령어를 입력해보세요!",
            color=0xffd700
        )
        embed.set_footer(text="이 알림은 익명으로 발송되었습니다.")
        
        await receiver.send(embed=embed)
        dm_status_msg = " (상대방에게 DM 알림도 보냈어요!)"
        
    except discord.Forbidden:
        dm_status_msg = "\n(하지만 상대방이 DM을 막아둬서 알림은 못 보냈어요. 메시지는 잘 저장됐습니다!)"
    except Exception as e:
        dm_status_msg = f"\n(DM 전송 중 오류 발생: {e})"

    # 작성자에게 결과 통보
    await interaction.followup.send(f"✅ **{receiver.display_name}**님에게 익명으로 메시지를 남겼습니다!{dm_status_msg}")


# 2. 롤링페이퍼 확인 (/롤링페이퍼 확인)
@paper_group.command(name="확인", description="나에게 도착한 익명 메시지들을 확인합니다.")
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
# 2. 관리자 전용 기능 (admin_group)
# ==========================================

# 3. [관리자] 전체 방송 (/롤링페이퍼 전체쓰기)
@admin_group.command(name="전체쓰기", description="[관리자] 서버의 모든 멤버(본인 제외)에게 롤링페이퍼를 씁니다.")
@app_commands.default_permissions(administrator=True) # [수정됨] 님 버전에서는 이 명령어가 맞습니다
@app_commands.checks.has_permissions(administrator=True) # [유지] 보안을 위해 필수
async def broadcast_paper(interaction: discord.Interaction, content: str):
    await interaction.response.defer(ephemeral=True)
    
    if len(content) > 500:
        await interaction.followup.send(f"⚠️ 메시지가 너무 깁니다! ({len(content)}자/500자)")
        return

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

# 4. [관리자] 로그 확인 (/롤링페이퍼 로그)
@admin_group.command(name="로그", description="[관리자] 작성된 모든 롤링페이퍼 로그를 확인합니다.")
@app_commands.default_permissions(administrator=True) # [수정됨]
@app_commands.checks.has_permissions(administrator=True)
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

# 5. [관리자] DB 초기화 (/롤링페이퍼 초기화)
@admin_group.command(name="초기화", description="[관리자] 저장된 모든 메시지를 즉시 삭제합니다.")
@app_commands.default_permissions(administrator=True) # [수정됨]
@app_commands.checks.has_permissions(administrator=True)
async def reset_db(interaction: discord.Interaction):
    conn = sqlite3.connect('rolling_paper.db')
    c = conn.cursor()
    c.execute("DELETE FROM messages")
    conn.commit()
    conn.close()
    
    await interaction.response.send_message("⚠️ 모든 롤링페이퍼 데이터가 초기화되었습니다.", ephemeral=True)

# 6. [관리자] 자동 초기화 설정 토글 (/롤링페이퍼 자동초기화)
@admin_group.command(name="자동초기화", description="[관리자] 매달 1일 데이터 자동 초기화 기능을 켜거나 끕니다.")
@app_commands.default_permissions(administrator=True) # [수정됨]
@app_commands.checks.has_permissions(administrator=True)
async def toggle_auto_reset(interaction: discord.Interaction):
    conn = sqlite3.connect('rolling_paper.db')
    c = conn.cursor()
    
    # 현재 상태 확인
    c.execute("SELECT value FROM settings WHERE key='auto_reset'")
    current_status = c.fetchone()[0]
    
    # 상태 반전 (ON <-> OFF)
    new_status = 'OFF' if current_status == 'ON' else 'ON'
    
    # 저장
    c.execute("UPDATE settings SET value = ? WHERE key = 'auto_reset'", (new_status,))
    conn.commit()
    conn.close()
    
    status_emoji = "🟢" if new_status == 'ON' else "🔴"
    await interaction.response.send_message(f"{status_emoji} 매달 1일 자동 초기화 기능이 **{new_status}** 상태로 변경되었습니다.", ephemeral=True)
    
    
client.run(TOKEN)
