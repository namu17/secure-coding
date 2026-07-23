# secure-coding

## 실행 방법
> WSL(Ubuntu) 환경
### 1. 환경 변수 파일 준비 (.env)
```
cp .env.example .env
```
#### 필수 수정사항
- DJANGO_SECRET_KEY: ```python3 -c "import secrets;print(secrets.token_urlsafe(50))"```에서 생산된 랜덤값
- POSTGRES_PASSWORD: ```python3 -c "import secrets;print(secrets.token_urlsafe(24))"```에서 생산된 랜덤값
- JWT_SECRET: ```python3 -c "import secrets;print(secrets.token_urlsafe(50))"```에서 생산된 랜덤값 (위와 동일값 X)
- DJANGO_SUPERUSER_PASSWORD: 원하는 비밀번호 설정
### 2. nginx용 TLS 인증서 생성 (최초 1회)
WSL 터미널에서 다음과 같은 명령어 입력
```
cd ~/secure-coding #secure-coding 디렉토리 이동
sh nginx/generate-certs.sh
```
### 3. 빌드 + 가동
```
docker compose up -d --build
```
### 4. 접속
`https://localhost` 혹은 `https://127.0.0.1`으로 접속
