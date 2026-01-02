# 💌 Discord Rolling Paper Bot (익명 롤링페이퍼 봇)

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python&logoColor=white)
![Discord.py](https://img.shields.io/badge/Discord.py-2.0%2B-5865F2?logo=discord&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

디스코드 서버 멤버들끼리 서로 익명으로 메시지(롤링페이퍼)를 남기고 확인할 수 있는 봇입니다.
누구나 자신의 서버에 직접 봇을 설치하여 무료로 운영할 수 있도록 설계되었습니다.

## ✨ 주요 기능 (Features)

### 👤 일반 유저 기능
- **익명 메시지 보내기**: `/롤링페이퍼쓰기 [대상] [내용]` 명령어로 친구에게 익명 편지를 보냅니다.
- **내 편지함 확인**: `/롤링페이퍼확인` 명령어로 나에게 도착한 메시지들을 모아볼 수 있습니다.
- **본인 작성 방지**: 자기 자신에게는 쓸 수 없도록 처리되어 있습니다.
- **메세지 도착 알림**: 메세지가 도착하면 DM으로 안내 해드려요.

### 🛡️ 관리자 및 시스템 기능
- **전체 발송**: `/롤링페이퍼전체쓰기`로 서버의 모든 멤버(본인 제외)에게 동시에 메시지를 보낼 수 있습니다. (이벤트 공지용)
- **로그 확인**: `/롤링페이퍼로그`로 누가 누구에게 보냈는지 전체 기록을 파일(.txt)로 다운로드하여 확인할 수 있습니다. (관리자 전용)
- **데이터 초기화**: `/롤링페이퍼초기화`로 저장된 모든 메시지를 즉시 삭제합니다.
- **주기적 자동 초기화**: 서버 최적화를 위해 설정된 주기에 따라 데이터베이스가 자동으로 정리됩니다.
- **보안**: 관리자 명령어는 관리자 권한이 없는 일반 멤버에게는 보이지 않습니다.
- - **글자수 제한**: DB관리를 위해 메시지는 한 번에 최대 **500자**까지만 작성 가능합니다.

---

## 📅 업데이트 내역 (Update Log)

### v1.1 (2026/01/03 토)
- **글자수 제한 추가**: 장문 메시지로 인한 오류 및 도배를 방지하기 위해 500자 제한이 적용되었습니다.
- **주기적 DB 초기화 기능**: 데이터베이스 용량 관리 및 최적화를 위한 자동 초기화 로직이 추가되었습니다.

### v1.0 (2026/01/02 금)
- **최초 릴리즈**: 익명 메시지 전송, 확인, 관리자 로그 기능 등 핵심 기능 구현 및 배포.

---

## 🚀 설치 및 실행 가이드 (Step-by-Step Guide)

이 봇을 사용하려면 **Discord Developer Portal에서 봇을 생성**하고 코드를 실행해야 합니다. 차근차근 따라 해보세요!

### 1단계: 디스코드 봇 생성 및 토큰 발급
1. [Discord Developer Portal](https://discord.com/developers/applications)에 접속하여 로그인합니다.
2. 오른쪽 상단의 **[New Application]** 버튼을 누르고 봇 이름을 입력합니다 (예: `RollingPaperBot`).
3. 왼쪽 메뉴에서 [Bot]을 클릭합니다.
4. **Build-A-Bot** 섹션 아래의 [Reset Token]을 눌러 토큰을 생성하고, 복사(Copy)하여 메모장에 잘 저장해둡니다. (이 토큰은 절대 남에게 보여주면 안 됩니다!)
5. 같은 페이지 스크롤을 내려 **Privileged Gateway Intents** 섹션에서 아래 두 가지를 **반드시 켜주세요**. (이걸 안 켜면 봇이 작동하지 않습니다.)
   - ✅ **Server Members Intent**
   - ✅ **Message Content Intent** (선택 권장)
6. 맨 아래 [Save Changes]를 눌러 저장합니다.

### 2단계: 봇을 내 서버에 초대하기
1. 왼쪽 메뉴에서 **[OAuth2]** -> https://www.homedepot.com/b/Outdoors-Outdoor-Power-Equipment-Generators/N-5yc1vZbx8l를 클릭합니다.
2. **SCOPES** 항목에서 `bot`, `applications.commands` 두 가지를 체크합니다.
3. **BOT PERMISSIONS** 항목에서 다음 권한들을 체크합니다.
   - `Send Messages`, `Embed Links`, `Attach Files`, `Read Message History`, `View Channels`
4. 맨 아래 생성된 URL을 복사하여 인터넷 주소창에 붙여넣고, 봇을 초대할 내 서버를 선택합니다.

### 3단계: 코드 다운로드 및 설정
1. 이 저장소를 다운로드(Clone) 합니다.
   ```bash
   git clone [https://github.com/본인아이디/Discord_Rolling_Paper_Bot.git](https://github.com/본인아이디/Discord_Rolling_Paper_Bot.git)
   cd Discord_Rolling_Paper_Bot
2. 필수 라이브러리를 설치합니다. (파이썬이 설치되어 있어야 합니다.)
   ```bash
   pip install -r requirements.txt
4. main.py 파일을 메모장이나 코드 에디터(VS Code 등)로 엽니다.
5. 파일 상단의 설정 부분을 수정합니다.
   ```bash
   # ==========================================
   # [설정 구간] 토큰과 서버 ID만 입력하세요!
   # ==========================================
   
   # 1단계에서 복사한 토큰을 따옴표 안에 넣으세요.
   TOKEN = '여기에_토큰을_붙여넣으세요' 
   
   # 봇을 사용할 디스코드 서버의 ID(숫자)를 넣으세요.
   # (디스코드 설정 -> 고급 -> 개발자 모드 켜기 -> 서버 우클릭 -> ID 복사)
   MY_GUILD_ID = discord.Object(id=123456789012345678) 
   # ==========================================
### 4단계: 봇 실행하기
1. 터미널(CMD)에서 아래 명령어를 입력하여 봇을 실행합니다.
   ```bash
   python main.py
   Bot is ready 또는 Logged in as... 메시지가 뜨면 성공입니다! 디스코드 서버에서 /를 눌러 명령어가 뜨는지 확인해보세요.

---

### 🛠️ 기술 스택 (Tech Stack)
Language: Python 3.8+

Library: discord.py (app_commands)

Database: SQLite3 (내장 DB 사용)

### ⚠️ 문제 해결 (Troubleshooting)
Q. 명령어가 안 보여요!

MY_GUILD_ID에 서버 ID를 정확히 넣었는지 확인하고, 봇을 껐다가 다시 켜보세요. (Sync 과정이 필요합니다.)

Q. 'Server Members Intent' 에러가 떠요!

1단계의 5번 항목(Intents 켜기)을 수행했는지 다시 확인해주세요.

### 📜 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
   
