# seohee-unjeoung

## 다운로드 스크립트 사용방법

이 프로젝트는 HTML 파일에 포함된 모든 외부 리소스(CSS, JS, 이미지, 폰트 등)를 다운로드하는 스크립트를 제공합니다.

### 📋 사전 요구사항

1. **Python 3.7 이상** 설치
2. **가상환경 설정** (권장)

### ️ 설치 및 설정

1. **가상환경 생성 및 활성화**
   ```bash
   python -m venv venv
   source venv/bin/activate  # macOS/Linux
   # 또는
   venv\Scripts\activate     # Windows
   ```

2. **필요한 패키지 설치**
   ```bash
   pip install -r requirements.txt
   ```

### 📥 사용방법

#### 방법 1: 실행 스크립트 사용 (권장)
```bash
cd download
chmod +x run
./run
```

#### 방법 2: 직접 Python 스크립트 실행
```bash
cd download
python down.py
```

###  다운로드 결과

스크립트 실행 후 다음 구조로 파일들이 생성됩니다:

```
www/assets/
├── css/          # CSS 파일들
├── js/           # JavaScript 파일들
├── images/       # 이미지 파일들 (PNG, JPG, GIF, SVG, AVIF)
├── fonts/        # 폰트 파일들 (WOFF, WOFF2, TTF, EOT)
├── videos/       # 비디오 파일들 (MP4, WEBM)
└── other/        # 기타 파일들

logs/
├── download.log          # 다운로드 진행 로그
├── download_report.json  # 다운로드 결과 JSON 리포트
└── download_report.txt   # 다운로드 결과 텍스트 리포트
```

### 📊 기능

- **자동 리소스 감지**: HTML에서 CSS, JS, 이미지, 폰트, 비디오 등 모든 외부 리소스 자동 감지
- **CSS 내부 리소스 추출**: CSS 파일 내의 `url()` 함수와 `@import` 규칙에서 추가 리소스 추출
- **파일 타입별 분류**: 다운로드된 파일을 타입별로 자동 분류
- **중복 제거**: 동일한 리소스의 중복 다운로드 방지
- **상세한 로깅**: 다운로드 진행 상황과 오류 로그 기록
- **통계 리포트**: 다운로드 결과에 대한 상세한 통계 정보 제공

### ⚙️ 설정 옵션

스크립트에서 다음 설정을 변경할 수 있습니다:

- **HTML 파일 경로**: `www/index.html` (기본값)
- **출력 디렉토리**: `www/assets` (기본값)
- **로그 디렉토리**: `logs` (기본값)
- **기본 URL**: `https://seohee-unjeong.kr/` (기본값)
- **요청 간격**: 0.1초 (기본값)

### 📝 로그 및 리포트 파일

- **logs/download.log**: 상세한 다운로드 로그
- **logs/download_report.json**: JSON 형식의 다운로드 결과
- **logs/download_report.txt**: 읽기 쉬운 텍스트 형식의 다운로드 결과

### 🔧 문제 해결

1. **권한 오류**: `chmod +x run` 명령으로 실행 권한 부여
2. **패키지 오류**: `pip install -r requirements.txt` 재실행
3. **네트워크 오류**: 인터넷 연결 확인 후 재시도
4. **파일 경로 오류**: `www/index.html` 파일이 존재하는지 확인

###  성능 최적화

- 대용량 사이트의 경우 요청 간격을 조정하여 서버 부하 감소
- 네트워크 상태에 따라 timeout 설정 조정 가능
- 로그 레벨을 조정하여 출력량 제어 가능
