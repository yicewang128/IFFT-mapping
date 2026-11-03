"""Filesystem behavior tests; Windows CI uses temporary fixtures, never the user's PC."""
import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parent))
import research_library as lib


class LibraryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix="research library 中文 ")
        self.root=Path(self.tmp.name).resolve()
        lib.initialize(self.root)

    def tearDown(self): self.tmp.cleanup()

    def put(self,name,data=b"source data"):
        p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data);return p

    def test_read_write_probe_removes_only_its_own_files(self):
        p=self.put("keep.txt");before=set(self.root.iterdir())
        self.assertTrue(lib.check(self.root)["write_read_cleanup_probe"])
        self.assertEqual(before,set(self.root.iterdir()));self.assertEqual(p.read_bytes(),b"source data")

    def test_missing_directory_is_not_silently_created(self):
        missing=self.root/"missing"
        with self.assertRaises(FileNotFoundError): lib.root_path(str(missing))
        self.assertFalse(missing.exists())

    def test_windows_path_rejected_on_non_windows(self):
        if os.name=="nt": self.skipTest("Windows paths valid on Windows")
        with self.assertRaises(ValueError):lib.root_path(r"C:\ChatGPT shared research database",create=True)

    def test_init_keeps_existing_agent_instructions(self):
        p=self.root/"AGENTS.md";p.write_text("My existing rules",encoding="utf-8")
        lib.initialize(self.root);self.assertEqual(p.read_text(encoding="utf-8"),"My existing rules")

    def test_path_escape_and_absolute_path_rejected(self):
        for rel in ("../outside.txt",str(self.root/"keep.txt"),r"C:\other\secret.txt"):
            with self.subTest(rel=rel),self.assertRaises(ValueError):lib.inside(self.root,rel)

    def test_symbolic_link_cannot_be_read_or_scanned(self):
        with tempfile.TemporaryDirectory() as other:
            p=Path(other)/"outside.txt";p.write_text("outside")
            link=self.root/"linked.txt"
            try:link.symlink_to(p)
            except OSError:self.skipTest("Creating symlinks requires unavailable OS privilege")
            with self.assertRaises(ValueError):lib.read_text(self.root,"linked.txt")
            self.assertNotIn(link,list(lib.walk_files(self.root)))

    def test_reparse_point_detection(self):
        fake=type("FakeStat",(),{"st_mode":0,"st_file_attributes":0x400})()
        with patch.object(Path,"lstat",return_value=fake):self.assertTrue(lib.linked(self.root))

    def test_symlink_destination_blocks_copy(self):
        with tempfile.TemporaryDirectory() as other:
            dest=self.root/"linked_folder"
            try:dest.symlink_to(other,target_is_directory=True)
            except OSError:self.skipTest("Creating symlinks requires unavailable OS privilege")
            src=self.put("00_Inbox/a.cif")
            with self.assertRaises(ValueError):lib.copy_verified(self.root,src,"linked_folder")
            self.assertEqual(list(Path(other).iterdir()),[])

    def test_dry_run_does_not_copy_or_write_report(self):
        self.put("00_Inbox/IFFT 012 中文.tif",bytes(range(256)))
        before=set(self.root.rglob('*'));r=lib.organize(self.root)
        self.assertEqual(before,set(self.root.rglob('*')));self.assertEqual(r["mode"],"preview_only")

    def test_copy_preserves_exact_bytes_original_and_idempotence(self):
        payload=bytes(range(256))*9000;src=self.put("00_Inbox/IFFT 012 中文.tif",payload)
        r=lib.organize(self.root,True);dst=self.root/r['entries'][0]['destination']
        self.assertEqual(dst.read_bytes(),payload);self.assertEqual(src.read_bytes(),payload)
        self.assertEqual(lib.organize(self.root,True)['entries'][0]['action'],"already_present")
        self.assertEqual(len(list((self.root/"05_Processing/IFFT").iterdir())),1)

    def test_name_collision_keeps_both_files(self):
        self.put("04_Crystal_Structures/sample.cif",b"old")
        self.put("00_Inbox/sample.cif",b"new")
        r=lib.organize(self.root,True);dest=self.root/r['entries'][0]['destination']
        self.assertNotEqual(dest.name,"sample.cif");self.assertEqual(dest.read_bytes(),b"new")
        self.assertEqual((self.root/"04_Crystal_Structures/sample.cif").read_bytes(),b"old")

    def test_unknown_files_are_not_misidentified_as_tem(self):
        self.assertEqual(lib.classify(Path("image123.tif"))[0],"99_Unsorted")
        self.assertEqual(lib.classify(Path("some.pdf"))[0],"01_Literature/Unreviewed")
        self.assertEqual(lib.classify(Path("IFFT mask.tif"))[0],"05_Processing/Masks")
        self.assertEqual(lib.classify(Path("IFFT overlay.tif"))[0],"06_Results")

    def test_index_checks_bytes_and_excludes_generated_indexes(self):
        p=self.put("00_Inbox/sample.cif",b"data_test")
        r1=lib.index_library(self.root);r2=lib.index_library(self.root)
        self.assertEqual(r1['files_read'],r2['files_read']);self.assertNotEqual(r1['report_directory'],r2['report_directory'])
        data=json.loads((Path(r2['report_directory'])/'catalog.json').read_text(encoding='utf-8'))
        row=next(r for r in data['files'] if r['path']=='00_Inbox/sample.cif')
        self.assertEqual(row['sha256'],lib.sha256(p));self.assertTrue(r2['success'])

    def test_index_does_not_report_failed_read_as_success(self):
        self.put("00_Inbox/bad.tif")
        original=lib.sha256
        def fail(p):
            if p.name=='bad.tif':raise PermissionError('fixture unreadable')
            return original(p)
        with patch.object(lib,'sha256',side_effect=fail):r=lib.index_library(self.root)
        self.assertFalse(r['success']);self.assertEqual(r['errors'][0]['path'],'00_Inbox/bad.tif')

    def test_corrupt_copy_is_removed_source_preserved(self):
        src=self.put("00_Inbox/a.cif",b"original")
        def corrupt(source,target,*args):target.write(b"corrupted")
        with patch.object(lib.shutil,'copyfileobj',side_effect=corrupt):r=lib.organize(self.root,True)
        self.assertFalse(r['success']);self.assertEqual(src.read_bytes(),b'original')
        self.assertEqual(list((self.root/'04_Crystal_Structures').iterdir()),[])

    def test_text_search_returns_line_numbers_and_binary_read_rejected(self):
        self.put("notes.txt","line one\n禁反射：forbidden reflection\n".encode())
        r=lib.search(self.root,'forbidden',True)
        self.assertEqual(r['matches'][0]['line'],2)
        self.put("original.tif")
        with self.assertRaises(ValueError):lib.read_text(self.root,"original.tif")

    def test_pdf_without_extractor_fails_explicitly(self):
        self.put("paper.pdf",b"%PDF")
        with patch.dict(sys.modules,{'pypdf':None}),self.assertRaisesRegex(ValueError,'pypdf'):
            lib.read_text(self.root,"paper.pdf")

    def test_cli_setup_and_organize_with_spaces_and_unicode(self):
        self.put("00_Inbox/晶格 IFFT.tif",b"unchanged")
        script=Path(lib.__file__)
        for command in (['setup'],['organize','--apply'],['index']):
            p=subprocess.run([sys.executable,str(script),'--root',str(self.root),*command],capture_output=True,text=True,encoding='utf-8',env={**os.environ,'PYTHONIOENCODING':'utf-8'})
            self.assertEqual(p.returncode,0,p.stderr);self.assertIsInstance(json.loads(p.stdout),dict)


if __name__=='__main__': unittest.main()
