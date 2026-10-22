import csv
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from rna_evidence_agent.design_review import review_design

class DesignReviewChecks(unittest.TestCase):
    def run_case(self, metadata, confirmation=None, counts="gene,S1,S2,S3,S4\ng1,1,2,3,4\n"):
        with TemporaryDirectory() as d:
            root=Path(d);c=root/'counts.csv';m=root/'metadata.csv'
            c.write_text(counts)
            m.write_text(metadata)
            return review_design(c,m,root/'out',confirmation=confirmation)
    def valid(self):
        return 'sample,cell_line,group\nS1,A,control\nS2,B,control\nS3,A,treated\nS4,B,treated\n'
    def test_requires_biological_confirmation(self):
        r=self.run_case(self.valid());self.assertEqual(r['status'],'needs-researcher-confirmation')
        self.assertFalse(r['differential_expression_run']);self.assertEqual(len(r['pairs']),2)
    def test_shuffled_rows_remain_valid(self):
        lines=self.valid().splitlines();r=self.run_case(lines[0]+'\n'+'\n'.join(reversed(lines[1:]))+'\n')
        self.assertEqual(r['status'],'needs-researcher-confirmation')
    def test_mismatched_id_blocks(self):
        self.assertEqual(self.run_case(self.valid().replace('S4,','UNKNOWN,'))['status'],'blocked-input-alignment')
    def test_missing_factor_requires_information(self):
        self.assertEqual(self.run_case('sample,group\nS1,control\nS2,control\nS3,treated\nS4,treated\n')['status'],'needs-design-information')
    def test_unbalanced_pairs_not_approved(self):
        self.assertEqual(self.run_case(self.valid().replace('S4,B,treated','S4,A,treated'))['status'],'needs-design-review')
    def test_wrong_confirmation_blocks(self):
        self.assertEqual(self.run_case(self.valid(),{'biological_pairing_confirmed':True})['status'],'blocked-confirmation')
    def test_confirmation_bound_to_data(self):
        r=self.run_case(self.valid())
        c={'dataset_sha256':r['dataset_sha256'],'factor':'cell_line','contrast':['treated','control'],'biological_pairing_confirmed':True}
        self.assertEqual(self.run_case(self.valid(),c)['status'],'ready-for-method-review')
        self.assertEqual(self.run_case(self.valid(),c,counts='gene,S1,S2,S3,S4\ng1,1,2,3,5\n')['status'],'blocked-confirmation')

if __name__=='__main__':unittest.main()
