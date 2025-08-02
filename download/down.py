#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTML 외부 리소스 다운로드 및 경로 수정 스크립트
HTML 파일에 포함된 모든 외부 리소스(CSS, JS, 이미지, 폰트 등)를 다운로드하고,
HTML 파일 내의 경로를 로컬 경로로 수정합니다.
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
from typing import List, Set, Optional, Dict

class HTMLResourceDownloader:
    def __init__(self, html_file_path: str, output_dir: str = "www/assets"):
        self.html_file_path = Path(html_file_path)
        self.output_dir = Path(output_dir)
        self.base_url = "https://seohee-unjeong.kr/"
        
        self.downloaded_urls: Set[str] = set()
        self.failed_urls: Set[str] = set()
        self.url_map: Dict[str, str] = {}
        
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
                logging.FileHandler(self.logs_dir / 'download.log', mode='w', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # 통계 정보
        self.stats = {
            'total_resources': 0, 'downloaded': 0, 'failed': 0,
            'css_files': 0, 'js_files': 0, 'images': 0,
            'fonts': 0, 'videos': 0, 'other': 0
        }
        
    def setup_directories(self):
        """다운로드 디렉토리 구조 생성"""
        directories = ['css', 'js', 'images', 'fonts', 'videos', 'other']
        for dir_name in directories:
            (self.output_dir / dir_name).mkdir(parents=True, exist_ok=True)
        self.logger.info(f"디렉토리 구조 생성 완료: {self.output_dir}")
    
    def get_file_extension(self, url: str, content_type: Optional[str] = None) -> str:
        """URL과 Content-Type을 기반으로 파일 확장자 결정"""
        parsed_url = urlparse(url)
        path = parsed_url.path.lower()
        
        if '.' in Path(path).name:
            ext = Path(path).suffix[1:]
            if ext in ['css', 'js', 'png', 'jpg', 'jpeg', 'gif', 'svg', 'woff', 'woff2', 'ttf', 'eot', 'mp4', 'webm', 'avif']:
                return ext
        
        if content_type:
            content_type = content_type.lower()
            mime_map = {
                'css': 'css', 'javascript': 'js', 'png': 'png', 'jpeg': 'jpg', 'gif': 'gif',
                'svg+xml': 'svg', 'woff': 'woff', 'woff2': 'woff2', 'ttf': 'ttf',
                'mp4': 'mp4', 'webm': 'webm', 'avif': 'avif'
            }
            for key, value in mime_map.items():
                if key in content_type:
                    return value
        
        return 'bin'

    def get_download_path(self, url: str, content_type: Optional[str] = None) -> Path:
        """다운로드할 파일의 로컬 경로 결정"""
        ext = self.get_file_extension(url, content_type)
        
        dir_map = {
            'css': 'css', 'js': 'js', 'png': 'images', 'jpg': 'images', 'jpeg': 'images',
            'gif': 'images', 'svg': 'images', 'avif': 'images', 'woff': 'fonts',
            'woff2': 'fonts', 'ttf': 'fonts', 'eot': 'fonts', 'mp4': 'videos', 'webm': 'videos'
        }
        subdir = dir_map.get(ext, 'other')
        
        parsed_url = urlparse(url)
        filename = Path(parsed_url.path).name
        if not filename:
             filename = f"resource_{len(self.downloaded_urls)}_{int(time.time())}.{ext}"
        
        if parsed_url.query:
             filename += "_" + re.sub(r'[^\w\-_.]', '_', parsed_url.query)

        filename = re.sub(r'[^\w\-_.]', '_', filename)
        
        return self.output_dir / subdir / filename

    def download_resource(self, url: str) -> None:
        """개별 리소스 다운로드"""
        if not url or url.startswith('data:') or url.startswith('javascript:'):
            return

        absolute_url = urljoin(self.base_url, url)
        if absolute_url in self.downloaded_urls:
            return
            
        try:
            self.logger.info(f"다운로드 중: {absolute_url}")
            response = self.session.get(absolute_url, timeout=30, allow_redirects=True)
            response.raise_for_status()
            
            final_url = response.url
            if final_url in self.downloaded_urls:
                self.url_map[url] = self.url_map[final_url]
                self.url_map[absolute_url] = self.url_map[final_url]
                return

            download_path = self.get_download_path(final_url, response.headers.get('content-type'))
            
            with open(download_path, 'wb') as f:
                f.write(response.content)
            
            self.downloaded_urls.add(absolute_url)
            self.downloaded_urls.add(final_url)

            relative_path = os.path.join(self.output_dir.name, download_path.relative_to(self.output_dir))
            
            self.url_map[url] = relative_path
            self.url_map[absolute_url] = relative_path
            self.url_map[final_url] = relative_path

            self.stats['downloaded'] += 1
            ext = self.get_file_extension(final_url, response.headers.get('content-type'))
            if ext == 'css': self.stats['css_files'] += 1
            elif ext == 'js': self.stats['js_files'] += 1
            elif ext in ['png', 'jpg', 'jpeg', 'gif', 'svg', 'avif']: self.stats['images'] += 1
            elif ext in ['woff', 'woff2', 'ttf', 'eot']: self.stats['fonts'] += 1
            elif ext in ['mp4', 'webm']: self.stats['videos'] += 1
            else: self.stats['other'] += 1
            
            self.logger.info(f"다운로드 완료: {download_path}")

            if ext == 'css':
                self.process_css_file(download_path, final_url)

        except requests.exceptions.RequestException as e:
            self.logger.error(f"다운로드 실패 {url}: {e}")
            self.failed_urls.add(absolute_url)
            self.stats['failed'] += 1
    
    def extract_resources(self, soup: BeautifulSoup) -> List[str]:
        """HTML에서 모든 외부 리소스 URL 추출"""
        resources = set()
        
        tag_attrs = {'link': 'href', 'script': 'src', 'img': 'src', 'audio': 'src', 'video': 'src', 'source': 'src', 'iframe': 'src'}
        
        for tag_name, attr_name in tag_attrs.items():
            for tag in soup.find_all(tag_name, **{attr_name: True}):
                resources.add(tag[attr_name])

        for img in soup.find_all('img', srcset=True):
            for s in img['srcset'].split(','):
                url = s.strip().split(' ')[0]
                if url: resources.add(url)

        for tag in soup.find_all('meta', content=True):
             if tag.get('name') == 'msapplication-TileImage' or 'image' in tag.get('property', ''):
                 resources.add(tag['content'])

        style_content = "".join(s.string for s in soup.find_all('style') if s.string)
        for url in self.extract_resources_from_css_content(style_content, self.base_url):
            resources.add(url)

        return list(resources)

    def extract_resources_from_css_content(self, css_content: str, base_url: str) -> List[str]:
        """CSS 내용에서 리소스 URL 추출 (url(), @import)"""
        urls = []
        url_pattern = r'url\(["\']?([^"\')\s]+)["\']?\)'
        matches = re.findall(url_pattern, css_content)
        for url in matches:
            if not url.startswith('data:'): urls.append(urljoin(base_url, url))
        
        import_pattern = r'@import\s+(?:url\()?["\']?([^"\')]+)["\']?\)?'
        matches = re.findall(import_pattern, css_content)
        for url in matches: urls.append(urljoin(base_url, url))
        return urls
    
    def process_css_file(self, css_path: Path, base_url: str):
        """CSS 파일 처리 및 내부 리소스 다운로드"""
        try:
            with open(css_path, 'r+', encoding='utf-8') as f:
                css_content = f.read()
                original_content = css_content
                
                additional_resources = self.extract_resources_from_css_content(css_content, base_url)
                
                for resource_url in additional_resources:
                    self.download_resource(resource_url)
                
                # CSS 파일 내의 경로도 수정
                for original_url, local_path in self.url_map.items():
                    relative_css_path = os.path.relpath(local_path, start=css_path.parent)
                    css_content = css_content.replace(original_url, relative_css_path)
                
                if css_content != original_content:
                    f.seek(0)
                    f.write(css_content)
                    f.truncate()
                    self.logger.info(f"CSS 파일 내 경로 수정 완료: {css_path}")

        except Exception as e:
            self.logger.error(f"CSS 파일 처리 실패 {css_path}: {e}")

    def update_html_paths(self):
        """HTML 파일의 리소스 경로를 로컬 경로로 업데이트"""
        self.logger.info("HTML 파일 경로 업데이트 시작...")
        with open(self.html_file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # 원본 URL을 길이 순으로 정렬하여 긴 URL이 먼저 대체되도록 함 (부분 문자열 문제 방지)
        sorted_urls = sorted(self.url_map.keys(), key=len, reverse=True)

        for original_url in sorted_urls:
            local_path = self.url_map[original_url]
            # HTML content에서 일반적인 경로 교체
            html_content = html_content.replace(f'"{original_url}"', f'"{local_path}"')
            html_content = html_content.replace(f"'{original_url}'", f"'{local_path}'")
            # srcset 등에서 공백으로 끝나는 경우
            html_content = html_content.replace(f'{original_url} ', f'{local_path} ')

        with open(self.html_file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        self.logger.info("HTML 파일 경로 업데이트 완료.")

    def save_download_report(self):
        """다운로드 결과 리포트 저장 (JSON 및 TXT)"""
        # JSON 리포트
        report_path_json = self.logs_dir / 'download_report.json'
        report_data = {
            'stats': self.stats,
            'url_map': self.url_map,
            'failed_urls': list(self.failed_urls),
            'output_directory': str(self.output_dir.resolve())
        }
        with open(report_path_json, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        self.logger.info(f"JSON 리포트 저장: {report_path_json}")

        # TXT 리포트
        report_path_txt = Path('./MIGRATION.txt')
        with open(report_path_txt, 'w', encoding='utf-8') as f:
            f.write("HTML 외부 리소스 다운로드 및 경로 변경 리포트\n")
            f.write("=" * 70 + "\n\n")
            f.write(f"대상 HTML 파일: {self.html_file_path}\n")
            f.write(f"저장된 디렉토리: {self.output_dir.resolve()}\n\n")

            f.write("[요약]\n")
            f.write(f"  - 총 발견된 리소스: {self.stats['total_resources']}\n")
            f.write(f"  - 다운로드 성공: {self.stats['downloaded']}\n")
            f.write(f"  - 다운로드 실패: {self.stats['failed']}\n\n")
            
            if self.url_map:
                f.write("[경로 변경 내역 (원본 URL -> 로컬 경로)]\n")
                f.write("-" * 70 + "\n")
                # url_map에서 중복된 local_path를 기준으로 그룹화하여 보기 좋게 출력
                processed_urls = set()
                for original_url, local_path in sorted(self.url_map.items()):
                    if original_url not in processed_urls:
                         f.write(f"{original_url}\n  -> {local_path}\n\n")
                    processed_urls.add(original_url)

            if self.failed_urls:
                f.write("\n[다운로드 실패 URL]\n")
                f.write("-" * 70 + "\n")
                for url in sorted(list(self.failed_urls)):
                    f.write(f"- {url}\n")
        
        self.logger.info(f"텍스트 리포트 저장: {report_path_txt}")

    def run(self):
        """메인 실행 함수"""
        self.logger.info(f"HTML 외부 리소스 다운로드 시작: {self.html_file_path}")
        self.setup_directories()
        
        try:
            with open(self.html_file_path, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f, 'html.parser')
        except Exception as e:
            self.logger.error(f"HTML 파일 읽기 실패: {e}")
            return
        
        resources = self.extract_resources(soup)
        self.stats['total_resources'] = len(resources)
        self.logger.info(f"총 {len(resources)}개의 리소스 발견.")
        
        for i, resource_url in enumerate(resources, 1):
            self.logger.info(f"처리 중 ({i}/{len(resources)}): {resource_url[:100]}")
            self.download_resource(resource_url)
            time.sleep(0.05)
        
        self.update_html_paths()
        self.save_download_report()
        
        self.logger.info("모든 작업 완료!")
        self.logger.info(f"총 발견: {self.stats['total_resources']}, 다운로드 성공: {self.stats['downloaded']}, 실패: {self.stats['failed']}")

def main():
    """메인 함수"""
    html_file = "www/index.html"
    if not Path(html_file).exists():
        print(f"오류: {html_file} 파일을 찾을 수 없습니다.")
        return
    
    downloader = HTMLResourceDownloader(html_file)
    downloader.run()

if __name__ == "__main__":
    main()