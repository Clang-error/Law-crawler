"""
PDF 변환 모듈 (데이터 구조 호환성 수정 완료)
"""
import os
from typing import List, Dict
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from utils import get_logger

logger = get_logger(__name__)

class PDFConverter:
    """데이터를 PDF로 변환하는 클래스"""
    
    def __init__(self, font_path: str = None):
        self.font_path = font_path
        self.font_name = 'Helvetica' # 기본값

        # 한글 폰트 등록
        if self.font_path and os.path.exists(self.font_path):
            try:
                pdfmetrics.registerFont(TTFont('Korean', self.font_path))
                self.font_name = 'Korean'
                logger.info(f"한글 폰트 로드 성공: {self.font_path}")
            except Exception as e:
                logger.error(f"폰트 로드 실패: {e}")
        else:
            logger.warning("한글 폰트가 없습니다.")

        self.styles = getSampleStyleSheet()
        self._setup_styles()
    
    def _setup_styles(self):
        # 스타일 정의
        self.styles.add(ParagraphStyle(
            name='LawTitle',
            parent=self.styles['Heading1'],
            fontName=self.font_name,
            fontSize=16,
            leading=20,
            alignment=1,
            spaceAfter=15
        ))
        
        self.styles.add(ParagraphStyle(
            name='LawBody',
            parent=self.styles['Normal'],
            fontName=self.font_name,
            fontSize=10,
            leading=16,
            spaceAfter=10
        ))

        self.styles.add(ParagraphStyle(
            name='SubHeading',
            parent=self.styles['Heading2'],
            fontName=self.font_name,
            fontSize=12,
            leading=14,
            spaceBefore=15,
            spaceAfter=10,
            textColor=colors.navy
        ))

    def convert_laws_to_pdf(self, laws: List[Dict], output_path: str, title: str = "법령 검색 결과"):
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=20*mm, leftMargin=20*mm,
            topMargin=20*mm, bottomMargin=20*mm
        )
        
        story = []
        
        # 문서 제목
        story.append(Paragraph(title, self.styles['LawTitle']))
        story.append(Spacer(1, 10*mm))
        
        for i, law in enumerate(laws, 1):
            # 1. 법령명
            law_name = law.get('법령명', '이름 없음')
            story.append(Paragraph(f"{i}. {law_name}", self.styles['SubHeading']))
            
            # 2. 메타데이터 테이블
            data = []
            if law.get('공포일자'): data.append(['공포일자', law['공포일자']])
            if law.get('시행일자'): data.append(['시행일자', law['시행일자']])
            if law.get('소관부처명'): data.append(['소관부처', law['소관부처명']])
            if law.get('법령ID'): data.append(['법령ID', law['법령ID']])
            
            if data:
                t = Table(data, colWidths=[30*mm, 100*mm])
                t.setStyle(TableStyle([
                    ('FONTNAME', (0,0), (-1,-1), self.font_name),
                    ('FONTSIZE', (0,0), (-1,-1), 9),
                    ('BACKGROUND', (0,0), (0,-1), colors.lightgrey),
                    ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                    ('PADDING', (0,0), (-1,-1), 4),
                ]))
                story.append(t)
                story.append(Spacer(1, 5*mm))

            # 3. 본문 내용 (여기가 핵심 수정됨!)
            # 수집된 데이터는 'detail' 안에 '본문'이 들어있을 수 있음
            content_text = ""
            
            # Case 1: 'detail' 딕셔너리 안에 '본문'이 있는 경우 (DataCollector 구조)
            if 'detail' in law and isinstance(law['detail'], dict):
                content_text = law['detail'].get('본문', '')
            
            # Case 2: 그냥 '본문' 키에 있는 경우 (예비용)
            elif '본문' in law:
                content_text = law['본문']
            
            # 본문 출력
            if content_text and len(content_text) > 10:
                # 대용량 텍스트 대응: Paragraph 하나에 너무 길게 넣으면 터지므로 줄 단위로 쪼갬
                lines = content_text.split('\n')
                for line in lines:
                    line = line.strip()
                    if not line:
                        story.append(Spacer(1, 2*mm))
                        continue
                    
                    # 특수문자 (<, > 등) 이스케이프 처리 (Paragraph는 XML 기반이라 필수)
                    clean_line = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    try:
                        story.append(Paragraph(clean_line, self.styles['LawBody']))
                    except:
                        # 가끔 이상한 문자 섞여 있으면 무시하고 진행
                        continue
            else:
                story.append(Paragraph("[본문 내용 없음 또는 수집 실패]", self.styles['LawBody']))
            
            story.append(Spacer(1, 10*mm))
            story.append(PageBreak()) # 법령마다 페이지 넘기기 깔끔하게
            
        try:
            doc.build(story)
            logger.info(f"PDF 저장 완료: {output_path}")
        except Exception as e:
            logger.error(f"PDF 생성 중 오류: {e}")

    def convert_precedents_to_pdf(self, precedents: List[Dict], output_path: str, title: str = "판례 검색 결과"):
        # 판례도 구조가 비슷하므로 같은 로직 사용 (함수 이름만 다르게 연결)
        # 판례는 '사건명'을 제목으로 씀
        for p in precedents:
            if '사건명' in p and '법령명' not in p:
                p['법령명'] = p['사건명']
                
        self.convert_laws_to_pdf(precedents, output_path, title)