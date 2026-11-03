"""Evidence/provenance tests with synthetic PDF and text fixtures only."""
import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import research_library as lib
import research_knowledge as knowledge


def pdf_fixture():
    """Two-page tiny PDF: one English text page and one blank page."""
    stream = b'BT /F1 12 Tf 50 750 Td (Forbidden reflection evidence fixture.) Tj ET'
    objects = [b'<< /Type /Catalog /Pages 2 0 R >>',
        b'<< /Type /Pages /Kids [3 0 R 4 0 R] /Count 2 >>',
        b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 5 0 R >> >> /Contents 6 0 R >>',
        b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << >> >>',
        b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',
        b'<< /Length '+str(len(stream)).encode()+b' >>\nstream\n'+stream+b'\nendstream']
    data = b'%PDF-1.4\n'; offsets = [0]
    for number, obj in enumerate(objects, 1):
        offsets.append(len(data)); data += str(number).encode()+b' 0 obj\n'+obj+b'\nendobj\n'
    xref = len(data)
    data += b'xref\n0 7\n0000000000 65535 f \n'
    data += b''.join(f'{offset:010d} 00000 n \n'.encode() for offset in offsets[1:])
    return data+b'trailer\n<< /Size 7 /Root 1 0 R >>\nstartxref\n'+str(xref).encode()+b'\n%%EOF\n'


class KnowledgeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='academic library 中文 ')
        self.root = Path(self.tmp.name).resolve()
        lib.initialize(self.root)

    def tearDown(self): self.tmp.cleanup()

    def put(self, relative, content):
        p = self.root/relative; p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(content); return p

    def test_pdf_pages_warnings_and_exact_source_hash(self):
        source = self.put('07_Textbooks/book.pdf', pdf_fixture())
        digest = lib.sha256(source)
        report = knowledge.build_index(self.root)
        self.assertTrue(report['success'])
        self.assertIn({'path':'07_Textbooks/book.pdf', 'pdf_page':2,
                       'status':'no_extractable_text', 'action':'Inspect original; OCR may be needed.'}, report['warnings'])
        hit = knowledge.find(self.root, 'FORBIDDEN reflection')['matches'][0]
        self.assertEqual(hit['pdf_page'], 1); self.assertEqual(hit['sha256'], digest)
        self.assertEqual(lib.sha256(source), digest)

    def test_unicode_phrase_and_newline_normalization(self):
        self.put('08_Notes/Concepts/note.md', '晶界判断\n跨行  词语\n'.encode())
        knowledge.build_index(self.root)
        hits = knowledge.find(self.root, '晶界判断 跨行')['matches']
        self.assertEqual(len(hits), 1); self.assertIsNone(hits[0]['pdf_page'])

    def test_modified_and_deleted_sources_withhold_old_excerpts(self):
        a=self.put('a.md', b'unique_old_evidence'); b=self.put('b.txt', b'unique_old_evidence second')
        knowledge.build_index(self.root); a.write_bytes(b'changed'); b.unlink()
        result=knowledge.find(self.root, 'unique_old_evidence')
        self.assertFalse(result['success']); self.assertEqual(result['matches'], [])
        self.assertEqual(len(result['errors']),2)

    def test_duplicate_copies_are_not_independent_evidence(self):
        self.put('00_Inbox/a.pdf',pdf_fixture()); self.put('01_Literature/Unreviewed/a.pdf',pdf_fixture())
        knowledge.build_index(self.root)
        self.assertEqual(len(knowledge.find(self.root,'Forbidden')['matches']),1)

    def test_bad_pdf_is_reported_while_other_documents_remain_searchable(self):
        self.put('bad.pdf',b'%PDF-1.4\ninvalid'); self.put('good.txt',b'valid_evidence')
        result=knowledge.build_index(self.root)
        self.assertFalse(result['success']); self.assertEqual(result['errors'][0]['path'],'bad.pdf')
        found=knowledge.find(self.root,'valid_evidence')
        self.assertFalse(found['success']); self.assertEqual(len(found['matches']),1)
        self.assertTrue(found['index_errors'])

    def test_absent_pdf_dependency_reports_error_not_empty_success(self):
        self.put('a.pdf',pdf_fixture())
        with patch.dict(sys.modules,{'pypdf':None}): result=knowledge.build_index(self.root)
        self.assertFalse(result['success']); self.assertIn('requirements-library',result['errors'][0]['error'])

    def test_file_changed_during_extraction_not_indexed(self):
        source=self.put('a.txt',b'volatile_keyword'); original=lib.sha256; calls=0
        def changing(path):
            nonlocal calls
            if path==source:
                calls+=1
                return 'a' if calls==1 else 'b'
            return original(path)
        with patch.object(lib,'sha256',side_effect=changing):result=knowledge.build_index(self.root)
        self.assertFalse(result['success'])
        self.assertEqual(knowledge.find(self.root,'volatile_keyword')['matches'],[])

    def test_rebuild_immutable_and_incomplete_build_ignored(self):
        self.put('a.md',b'first_marker')
        first=knowledge.build_index(self.root); second=knowledge.build_index(self.root)
        self.assertNotEqual(first['report_directory'], second['report_directory'])
        (self.root/'90_Index'/'99999999_fulltext_incomplete').mkdir()
        _, report=knowledge.latest_index(self.root)
        self.assertEqual(report['database'],second['database'])
        self.assertEqual(first['documents_indexed'],second['documents_indexed'])

    def test_note_provenance_and_original_preservation(self):
        p=self.put('07_Textbooks/book.pdf',pdf_fixture()); digest=lib.sha256(p)
        result=knowledge.create_note(self.root,'07_Textbooks/book.pdf',2)
        folder=Path(result['note_directory']); record=json.loads((folder/'source.json').read_text(encoding='utf-8'))
        self.assertEqual(record['source_sha256'],digest); self.assertEqual(record['pdf_page'],2)
        self.assertEqual(record['review_status'],'unreviewed'); self.assertEqual(lib.sha256(p),digest)
        self.assertTrue((folder/'writing_analysis.md').exists())
        with self.assertRaises(ValueError):knowledge.create_note(self.root,'07_Textbooks/book.pdf',3)
        with self.assertRaises(ValueError):knowledge.create_note(self.root,'../outside.pdf')

    def test_project_names_and_existing_projects_are_preserved(self):
        result=knowledge.create_project(self.root,'Conversion 电池')
        folder=Path(result['project_directory']); (folder/'README.md').write_text('my research')
        with self.assertRaises(FileExistsError):knowledge.create_project(self.root,'Conversion 电池')
        self.assertEqual((folder/'README.md').read_text(),'my research')
        self.assertTrue((folder/'evidence.csv').exists())
        for name in ('../outside','C:\\outside','CON','NUL.txt','bad.',''):
            with self.subTest(name=name),self.assertRaises(ValueError):knowledge.create_project(self.root,name)

    def test_setup_additive_preserves_workflow_and_old_library(self):
        workflow=self.root/'RESEARCH_WORKFLOW.md'; workflow.write_text('user workflow')
        data=self.put('03_Raw_Data/TEM/old.tif',b'original')
        lib.initialize(self.root)
        self.assertEqual(workflow.read_text(),'user workflow'); self.assertEqual(data.read_bytes(),b'original')
        self.assertTrue((self.root/'09_Writing/Examples').is_dir())
        self.assertEqual(lib.classify(Path('TEM教材.pdf'))[0],'07_Textbooks')
        self.assertEqual(lib.classify(Path('references.bib'))[0],'11_References')

    def test_query_literal_not_sql_and_limit(self):
        self.put('a.txt',b'first_marker'); knowledge.build_index(self.root)
        self.assertEqual(knowledge.find(self.root,"' OR 1=1 --")['matches'],[])
        for q,limit in (('',20),('x',0),('x',201)):
            with self.assertRaises(ValueError):knowledge.find(self.root,q,limit)

    def test_cli_pdf_index_search_note_project(self):
        self.put('07_Textbooks/book.pdf',pdf_fixture())
        for command in (['text-index'],['find','Forbidden'],['note','07_Textbooks/book.pdf','--page','1'],['project','科研项目']):
            proc=subprocess.run([sys.executable,str(Path(lib.__file__)),'--root',str(self.root),*command],capture_output=True,encoding='utf-8')
            self.assertEqual(proc.returncode,0,proc.stderr); self.assertIsInstance(json.loads(proc.stdout),dict)


if __name__=='__main__': unittest.main()
