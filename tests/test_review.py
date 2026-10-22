import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from rna_evidence_agent.evidence import verify_claims, review_run
from rna_evidence_agent.inspect_data import inspect_dataset

class ReviewChecks(unittest.TestCase):
    def result(self, ok=True):
        return SimpleNamespace(steps=[SimpleNamespace(index=0,code="print(1)",ok=ok,stdout="Number of samples: 4")])
    def test_valid_reference(self):
        self.assertEqual(verify_claims([dict(claim="Four samples",step=0,stdout_excerpt="Number of samples: 4")],self.result())["unsupported_count"],0)
    def test_failed_execution_rejected(self):
        self.assertEqual(verify_claims([dict(claim="Four samples",step=0,stdout_excerpt="Number of samples: 4")],self.result(False))["unsupported_count"],1)
    def test_malformed_step_rejected(self):
        for step in ([],{},True,"0",-1):
            self.assertEqual(verify_claims([dict(claim="Four samples",step=step,stdout_excerpt="Number of samples: 4")],self.result())["unsupported_count"],1)
    def test_missing_blank_and_short_evidence(self):
        for excerpt in ("missing evidence", "4", None):
            self.assertEqual(verify_claims([dict(claim="Four samples",step=0,stdout_excerpt=excerpt)],self.result())["unsupported_count"],1)
    def test_empty_registry_needs_review(self):
        with TemporaryDirectory() as d:
            Path(d,"claims.json").write_text("[]")
            self.assertEqual(review_run(d,self.result())["status"],"needs-review")
    def test_no_registry_needs_review(self):
        with TemporaryDirectory() as d:
            self.assertEqual(review_run(d,self.result())["status"],"needs-review")
    def test_sample_inventory(self):
        with TemporaryDirectory() as d:
            root=Path(__file__).resolve().parents[1]/"data/sample"
            result=inspect_dataset(root/"expression_counts.csv",root/"sample_metadata.csv",Path(d)/"inventory.json")
            self.assertEqual((result["genes"],result["samples"]),(4,4))
    def test_public_viewer_without_private_runs(self):
        import shutil
        from rna_evidence_agent import server
        original=server.ROOT
        with TemporaryDirectory() as d:
            try:
                source=Path(__file__).resolve().parents[1]/"output_examples"
                shutil.copytree(source,Path(d)/"output_examples")
                server.ROOT=Path(d)
                page=server.render()
                self.assertIn("21,833",page)
                self.assertNotIn("Run pending.",page)
                self.assertIn('id="codex_live_03"',page)
            finally: server.ROOT=original
    def test_bad_inputs(self):
        for counts in ("", "gene,s1\n", "gene,s1\na,-1\n", "gene,s1\na,nan\n", "gene,s1\na,1\na,2\n", "gene,s1\na,1.5\n", "gene,s1\na,1\n"):
            with TemporaryDirectory() as d:
                a=Path(d)/"c.csv";b=Path(d)/"m.csv"
                a.write_text(counts);b.write_text("sample,group\nother,control\n")
                with self.assertRaises(ValueError):inspect_dataset(a,b,Path(d)/"out.json")

if __name__=="__main__": unittest.main()
