from dataclasses import replace
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from claimaudit.config import ExperimentConfig
from claimaudit.demo import DemoEngine, REQUIRED_ARTIFACTS, calibration_thresholds, filter_records, load_run
from claimaudit.schemas import Prediction, Verdict

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / 'app/streamlit_app.py'
HAS_STREAMLIT = importlib.util.find_spec('streamlit') is not None


def fake_run():
    config = ExperimentConfig.load(ROOT/'experiments/controlled.toml')
    from dataclasses import asdict
    supported = {'verdict':'supported'}
    rejected = {'verdict':'not_supported'}
    return {'protocol':{'config':asdict(config)},
            'calibration':{'thresholds':{'embedding':{'threshold':.85},'nli':{'threshold':.5}}},
            'records':[
                {'id':'one','split':'test','label':'numeric_contradiction','group_id':'family1',
                 'methods':{'embedding':supported,'nli':supported,'structure-aware':rejected}},
                {'id':'two','split':'test','label':'supported','group_id':'family2',
                 'methods':{'embedding':supported,'nli':rejected,'structure-aware':rejected}},
                {'id':'three','split':'dev','label':'unsupported','group_id':'family3',
                 'methods':{'embedding':supported,'nli':rejected,'structure-aware':rejected}}]}


def fake_engine():
    config=ExperimentConfig.load(ROOT/'experiments/controlled.toml')
    embedding,nli=Mock(),Mock()
    embedding.verify.return_value=Prediction('embedding',Verdict.SUPPORTED,'stub',.9,'cosine_similarity')
    nli.verify.return_value=Prediction('nli',Verdict.SUPPORTED,'stub',.9,'entailment_probability',
                                      {'entailment':.9,'neutral':.05,'contradiction':.05})
    return DemoEngine(config,embedding,nli)


class DemoServiceTests(unittest.TestCase):
    def test_live_reuses_nli_and_respects_thresholds_and_ablations(self):
        engine=fake_engine()
        result=engine.verify('Model A achieved 80% accuracy.','Model A achieved 90% accuracy.',.95,.5)
        self.assertEqual(result['predictions']['embedding']['verdict'],'not_supported')
        self.assertEqual(result['predictions']['nli']['verdict'],'supported')
        self.assertEqual(result['predictions']['structure-aware']['verdict'],'not_supported')
        engine.nli.verify.assert_called_once()
        inputs=engine.nli.verify.call_args.args[0]
        self.assertEqual(set(vars(inputs)),{'evidence','claim'})
        self.assertEqual(engine.config.embedding.threshold,.75)
        off=engine.verify(inputs.evidence,inputs.claim,.5,.5,numeric=False,comparison=False)
        self.assertEqual(off['predictions']['structure-aware']['verdict'],'supported')

    def test_bad_input_fails_before_inference(self):
        engine=fake_engine()
        for evidence,claim in [(' ', 'claim'),('evidence',''),('x'*20001,'claim')]:
            with self.assertRaises(ValueError):
                engine.verify(evidence,claim,.5,.5)
        engine.nli.verify.assert_not_called()
        with self.assertRaises(ValueError):
            engine.verify('s','c',.5,2)

    def test_filters_use_binary_gold_not_four_way_verdict(self):
        records=fake_run()['records']
        self.assertEqual([r['id'] for r in filter_records(records,method='nli',errors_only=True)],['one','two'])
        self.assertEqual([r['id'] for r in filter_records(records,errors_only=True)],['two'])
        self.assertEqual(filter_records(records,label='supported',group='family1'),[])
        self.assertEqual([r['id'] for r in filter_records(records,split='dev')],['three'])

    def test_calibration_must_match_model(self):
        config=ExperimentConfig.load(ROOT/'experiments/controlled.toml')
        self.assertEqual(calibration_thresholds(fake_run(),config),(.85,.5))
        with self.assertRaises(ValueError):
            calibration_thresholds(fake_run(),replace(config,nli=replace(config.nli,revision='a'*40)))

    def test_artifact_tampering_and_incomplete_runs_rejected(self):
        run=fake_run()
        content={'protocol.json':json.dumps(run['protocol'],default=str),
                 'calibration.json':json.dumps(run['calibration']),'summary.json':'{}',
                 'predictions.jsonl':'\n'.join(json.dumps(r) for r in run['records']),
                 'failures.jsonl':'','report.md':'Test report'}
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)
            for name,text in content.items():
                (path/name).write_text(text)
            marker={'status':'complete','artifacts':{name:hashlib.sha256((path/name).read_bytes()).hexdigest() for name in REQUIRED_ARTIFACTS}}
            (path/'complete.json').write_text(json.dumps(marker))
            self.assertEqual(load_run(path)['report'],'Test report')
            (path/'summary.json').write_text('tampered')
            with self.assertRaisesRegex(ValueError,'integrity'):
                load_run(path)
            marker['status']='incomplete'
            (path/'complete.json').write_text(json.dumps(marker))
            with self.assertRaises(ValueError):
                load_run(path)


@unittest.skipUnless(HAS_STREAMLIT,'Install --extra app for UI tests')
class StreamlitTests(unittest.TestCase):
    def app(self):
        from streamlit.testing.v1 import AppTest
        return AppTest.from_file(str(APP),default_timeout=30)

    def test_initial_page_does_not_load_models(self):
        with patch('claimaudit.demo.DemoEngine.load',side_effect=AssertionError('Unexpected model load')):
            app=self.app().run()
        self.assertEqual(len(app.exception),0)
        self.assertTrue(any('ClaimAudit' in item.value for item in app.title))
        self.assertEqual(len(app.text_area),2)

    def test_empty_form_reports_actionable_error(self):
        app=self.app().run()
        app.text_area(key='evidence').set_value('')
        app.button[0].click().run()
        self.assertEqual(len(app.exception),0)
        self.assertTrue(any('Enter both' in item.value for item in app.error))

    def test_live_form_and_stale_result_handling(self):
        # Avoid global Streamlit cache leakage between tests while keeping production caching.
        with patch('streamlit.cache_resource',side_effect=lambda **kwargs:lambda fn:fn), patch(
            'claimaudit.demo.DemoEngine.load',return_value=fake_engine()
        ):
            app=self.app().run()
            app.button[0].click().run()
            self.assertEqual(len(app.exception),0)
            self.assertEqual(len(app.metric),3)
            self.assertEqual(app.metric[2].value,'Not supported')
            app.text_area(key='claim').set_value('Different claim.').run()
            self.assertEqual(len(app.metric),0)
            self.assertTrue(any('changed' in item.value for item in app.info))

    def test_model_error_is_shown_without_traceback(self):
        with patch('streamlit.cache_resource',side_effect=lambda **kwargs:lambda fn:fn), patch(
            'claimaudit.demo.DemoEngine.load',side_effect=RuntimeError('Weights unavailable')
        ):
            app=self.app().run()
            app.button[0].click().run()
            self.assertEqual(len(app.exception),0)
            self.assertTrue(any('Weights unavailable' in item.value for item in app.error))

    @unittest.skipUnless((ROOT/'results/controlled_v1/complete.json').exists(),'Saved evaluation not available')
    def test_evaluation_view_needs_no_inference_and_filters(self):
        with patch('claimaudit.demo.DemoEngine.load',side_effect=AssertionError('Unexpected model load')):
            app=self.app().run()
            app.sidebar.radio[0].set_value('Explore evaluation').run()
            self.assertEqual(len(app.exception),0)
            self.assertTrue(any('Controlled synthetic' in item.value for item in app.warning))
            self.assertGreaterEqual(len(app.dataframe),1)
            select=next(item for item in app.selectbox if item.label=='Gold label')
            select.set_value('unsupported').run()
            method=next(item for item in app.selectbox if item.label=='Method for filtering')
            method.set_value('structure-aware').run()
            self.assertTrue(any('No examples match' in item.value for item in app.info))
            self.assertEqual(len(app.exception),0)


if __name__=='__main__':
    unittest.main()
