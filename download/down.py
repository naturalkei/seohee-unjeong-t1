#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTML 외부 리소스 다운로드 스크립트
HTML 파일에 포함된 모든 외부 리소스(CSS, JS, 이미지, 폰트 등)를 다운로드합니다.
"""

import os
import re
import requests
import urllib.parse
from pathlib import Path
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import time
import logging
import json
from typing import List, Set, Optional

class HTMLResourceDownloader:
    def __init__(self, html_file_path: str, output_dir: str = "www/assets"):
        self.html_file_path = html_file_path
        self.output_dir = Path(output_dir)
        self.downloaded_urls: Set[str] = set()
        self.failed_urls: Set[str] = set()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # logs 디렉토리 생성
        self.logs_dir = Path("logs")
        self.logs_dir.mkdir(exist_ok=True)
        
        # 로깅 설정
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.logs_dir / 'download.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # 통계 정보
        self.stats = {
            'total_resources': 0,
            'downloaded': 0,
            'failed': 0,
            'css_files': 0,
            'js_files': 0,
            'images': 0,
            'fonts': 0,
            'videos': 0,
            'other': 0
        }
        
    def setup_directories(self):
        """다운로드 디렉토리 구조 생성"""
        directories = [
            'css',
            'js', 
            'images',
            'fonts',
            'videos',
            'other'
        ]
        
        for dir_name in directories:
            (self.output_dir / dir_name).mkdir(parents=True, exist_ok=True)
            
        self.logger.info(f"디렉토리 구조 생성 완료: {self.output_dir}")
    
    def get_file_extension(self, url: str, content_type: Optional[str] = None) -> str:
        """URL과 Content-Type을 기반으로 파일 확장자 결정"""
        parsed_url = urlparse(url)
        path = parsed_url.path.lower()
        
        # URL에서 확장자 추출
        if '.' in path:
            ext = path.split('.')[-1]
            if ext in ['css', 'js', 'png', 'jpg', 'jpeg', 'gif', 'svg', 'woff', 'woff2', 'ttf', 'eot', 'mp4', 'webm', 'avif']:
                return ext
        
        # Content-Type 기반 확장자 결정
        if content_type:
            content_type = content_type.lower()
            if 'css' in content_type:
                return 'css'
            elif 'javascript' in content_type:
                return 'js'
            elif 'image/png' in content_type:
                return 'png'
            elif 'image/jpeg' in content_type:
                return 'jpg'
            elif 'image/gif' in content_type:
                return 'gif'
            elif 'image/svg+xml' in content_type:
                return 'svg'
            elif 'font/woff' in content_type:
                return 'woff'
            elif 'font/woff2' in content_type:
                return 'woff2'
            elif 'font/ttf' in content_type:
                return 'ttf'
            elif 'video/mp4' in content_type:
                return 'mp4'
            elif 'video/webm' in content_type:
                return 'webm'
            elif 'image/avif' in content_type:
                return 'avif'
        
        return 'bin'
    
    def get_download_path(self, url: str, content_type: Optional[str] = None) -> Path:
        """다운로드할 파일의 로컬 경로 결정"""
        ext = self.get_file_extension(url, content_type)
        
        # 파일 타입별 디렉토리 결정
        if ext in ['css']:
            subdir = 'css'
        elif ext in ['js']:
            subdir = 'js'
        elif ext in ['png', 'jpg', 'jpeg', 'gif', 'svg', 'avif']:
            subdir = 'images'
        elif ext in ['woff', 'woff2', 'ttf', 'eot']:
            subdir = 'fonts'
        elif ext in ['mp4', 'webm']:
            subdir = 'videos'
        else:
            subdir = 'other'
        
        # 파일명 생성 (URL의 마지막 부분 사용)
        filename = url.split('/')[-1]
        if not filename or '.' not in filename:
            filename = f"resource_{len(self.downloaded_urls)}.{ext}"
        
        # 파일명 정리 (특수문자 제거)
        filename = re.sub(r'[^\w\-_.]', '_', filename)
        
        return self.output_dir / subdir / filename
    
    def download_resource(self, url: str, base_url: str) -> Optional[str]:
        """개별 리소스 다운로드"""
        if url in self.downloaded_urls:
            return None
            
        try:
            # 절대 URL로 변환
            absolute_url = urljoin(base_url, url)
            
            self.logger.info(f"다운로드 중: {absolute_url}")
            
            # 요청
            response = self.session.get(absolute_url, timeout=30)
            response.raise_for_status()
            
            # 다운로드 경로 결정
            download_path = self.get_download_path(absolute_url, response.headers.get('content-type'))
            
            # 파일 저장
            with open(download_path, 'wb') as f:
                f.write(response.content)
            
            self.downloaded_urls.add(url)
            self.stats['downloaded'] += 1
            
            # 파일 타입별 통계 업데이트
            ext = self.get_file_extension(absolute_url, response.headers.get('content-type'))
            if ext == 'css':
                self.stats['css_files'] += 1
            elif ext == 'js':
                self.stats['js_files'] += 1
            elif ext in ['png', 'jpg', 'jpeg', 'gif', 'svg', 'avif']:
                self.stats['images'] += 1
            elif ext in ['woff', 'woff2', 'ttf', 'eot']:
                self.stats['fonts'] += 1
            elif ext in ['mp4', 'webm']:
                self.stats['videos'] += 1
            else:
                self.stats['other'] += 1
            
            self.logger.info(f"다운로드 완료: {download_path}")
            
            return str(download_path)
            
        except Exception as e:
            self.logger.error(f"다운로드 실패 {url}: {str(e)}")
            self.failed_urls.add(url)
            self.stats['failed'] += 1
            return None
    
    def extract_resources_from_html(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """HTML에서 외부 리소스 URL 추출"""
        resources = []
        
        # CSS 파일
        for link in soup.find_all('link', rel='stylesheet'):
            href = link.get('href')
            if href:
                resources.append(href)
        
        # JavaScript 파일
        for script in soup.find_all('script', src=True):
            src = script.get('src')
            if src:
                resources.append(src)
        
        # 이미지 파일
        for img in soup.find_all('img', src=True):
            src = img.get('src')
            if src:
                resources.append(src)
        
        # 비디오 파일
        for video in soup.find_all('video'):
            for source in video.find_all('source', src=True):
                src = source.get('src')
                if src:
                    resources.append(src)
        
        # iframe src
        for iframe in soup.find_all('iframe', src=True):
            src = iframe.get('src')
            if src:
                resources.append(src)
        
        # 오디오 파일
        for audio in soup.find_all('audio'):
            for source in audio.find_all('source', src=True):
                src = source.get('src')
                if src:
                    resources.append(src)
        
        return list(set(resources))  # 중복 제거
    
    def extract_resources_from_css(self, css_content: str, base_url: str) -> List[str]:
        """CSS 파일에서 추가 리소스 URL 추출"""
        resources = []
        
        # url() 함수에서 URL 추출
        url_pattern = r'url\(["\']?([^"\')\s]+)["\']?\)'
        matches = re.findall(url_pattern, css_content)
        
        for match in matches:
            if not match.startswith('data:'):  # data URL 제외
                resources.append(match)
        
        # @import 규칙에서 URL 추출
        import_pattern = r'@import\s+["\']([^"\']+)["\']'
        import_matches = re.findall(import_pattern, css_content)
        resources.extend(import_matches)
        
        return list(set(resources))  # 중복 제거
    
    def process_css_file(self, css_path: str, base_url: str):
        """CSS 파일 처리 및 내부 리소스 다운로드"""
        try:
            with open(css_path, 'r', encoding='utf-8') as f:
                css_content = f.read()
            
            # CSS에서 추가 리소스 추출
            additional_resources = self.extract_resources_from_css(css_content, base_url)
            
            for resource_url in additional_resources:
                self.download_resource(resource_url, base_url)
                
        except Exception as e:
            self.logger.error(f"CSS 파일 처리 실패 {css_path}: {str(e)}")
    
    def save_download_report(self):
        """다운로드 결과 리포트 저장"""
        report = {
            'stats': self.stats,
            'downloaded_urls': list(self.downloaded_urls),
            'failed_urls': list(self.failed_urls),
            'output_directory': str(self.output_dir.absolute())
        }
        
        # JSON 리포트를 logs 폴더에 저장
        with open(self.logs_dir / 'download_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # 텍스트 리포트도 logs 폴더에 생성
        with open(self.logs_dir / 'download_report.txt', 'w', encoding='utf-8') as f:
            f.write("HTML 외부 리소스 다운로드 리포트\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"총 발견된 리소스: {self.stats['total_resources']}\n")
            f.write(f"성공적으로 다운로드: {self.stats['downloaded']}\n")
            f.write(f"실패한 다운로드: {self.stats['failed']}\n\n")
            f.write("파일 타입별 통계:\n")
            f.write(f"  CSS 파일: {self.stats['css_files']}\n")
            f.write(f"  JS 파일: {self.stats['js_files']}\n")
            f.write(f"  이미지: {self.stats['images']}\n")
            f.write(f"  폰트: {self.stats['fonts']}\n")
            f.write(f"  비디오: {self.stats['videos']}\n")
            f.write(f"  기타: {self.stats['other']}\n\n")
            f.write(f"다운로드 위치: {self.output_dir.absolute()}\n")
            f.write(f"로그 및 리포트 위치: {self.logs_dir.absolute()}\n")
    
    def run(self):
        """메인 실행 함수"""
        self.logger.info("HTML 외부 리소스 다운로드 시작")
        
        # 디렉토리 설정
        self.setup_directories()
        
        # HTML 파일 읽기
        try:
            with open(self.html_file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
        except Exception as e:
            self.logger.error(f"HTML 파일 읽기 실패: {str(e)}")
            return
        
        # BeautifulSoup으로 파싱
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 기본 URL 추출 (HTML에서 추출하거나 기본값 사용)
        base_url = "https://seohee-unjeong.kr/"
        
        # HTML에서 리소스 추출
        resources = self.extract_resources_from_html(soup, base_url)
        self.stats['total_resources'] = len(resources)
        
        self.logger.info(f"발견된 리소스 수: {len(resources)}")
        
        # 리소스 다운로드
        downloaded_css_files = []
        
        for i, resource_url in enumerate(resources, 1):
            self.logger.info(f"처리 중 ({i}/{len(resources)}): {resource_url}")
            
            downloaded_path = self.download_resource(resource_url, base_url)
            
            if downloaded_path and downloaded_path.endswith('.css'):
                downloaded_css_files.append(downloaded_path)
            
            # 요청 간격 조절
            time.sleep(0.1)
        
        # CSS 파일에서 추가 리소스 다운로드
        self.logger.info("CSS 파일에서 추가 리소스 추출 중...")
        for css_file in downloaded_css_files:
            self.process_css_file(css_file, base_url)
        
        # 결과 리포트 저장
        self.save_download_report()
        
        # 결과 요약
        self.logger.info(f"다운로드 완료!")
        self.logger.info(f"총 발견된 리소스: {self.stats['total_resources']}")
        self.logger.info(f"성공적으로 다운로드: {self.stats['downloaded']}")
        self.logger.info(f"실패한 다운로드: {self.stats['failed']}")
        self.logger.info(f"다운로드 위치: {self.output_dir.absolute()}")
        self.logger.info(f"로그 및 리포트 위치: {self.logs_dir.absolute()}")

def main():
    """메인 함수"""
    html_file = "www/index.html"
    
    if not os.path.exists(html_file):
        print(f"오류: {html_file} 파일을 찾을 수 없습니다.")
        return
    
    downloader = HTMLResourceDownloader(html_file)
    downloader.run()

if __name__ == "__main__":
    main()